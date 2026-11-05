
import asyncio
import json
import ollama

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


# ==========================================
# 1. OLLAMA CONFIGURATION
# ==========================================

MODEL = "llama3.2"


# ==========================================
# 2. COLLECT USER PREFERENCES
# ==========================================

print("\n========================================")
print("       TRAVEL PLANNING AGENT")
print("========================================")

city = input("Destination city [Hyderabad]: ") or "Hyderabad"
days = int(input("Number of days [3]: ") or 3)
people = int(input("Number of people [4]: ") or 4)
budget = float(input("Total budget [15000]: ") or 15000)

preferences = input(
    "Travel preferences [Sightseeing and food]: "
) or "Sightseeing and food"

accommodation = input(
    "Accommodation preference [Budget]: "
) or "Budget"


# ==========================================
# 3. SINGLE TRAVEL PLANNING AGENT
# ==========================================

async def main():

    server_params = StdioServerParameters(
        command="python",
        args=["travel_mcp_server.py"]
    )

    print("\nConnecting to MCP server...")

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            print("MCP connected successfully!")

            # Get available MCP tools
            tools_response = await session.list_tools()

            tools = []

            for tool in tools_response.tools:

                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

            print("\nAvailable MCP tools:")

            for tool in tools_response.tools:
                print("-", tool.name)

            # ==================================
            # 4. AGENT INSTRUCTIONS
            # ==================================

            messages = [
                {
                    "role": "system",
                    "content": """
                    You are a Single Travel Planning Agent.

                    Your task is to plan personalized trips.

                    Use the available MCP tools to:

                    1. Search tourist destinations.
                    2. Suggest accommodation.
                    3. Suggest transportation.
                    4. Estimate travel expenses.

                    Generate a complete day-wise itinerary.

                    Include:
                    - Tourist attractions
                    - Accommodation
                    - Restaurants and food suggestions
                    - Transportation
                    - Estimated budget

                    Respect the user's budget and preferences.

                    Group nearby attractions together.

                    Use Indian Rupees.

                    Do not claim that hotel prices or availability
                    are live or verified.

                    Clearly explain if the budget is insufficient.
                    """
                },
                {
                    "role": "user",
                    "content": f"""
                    Plan a {days}-day trip to {city}.

                    Number of people: {people}
                    Total budget: Rs. {budget}
                    Preferences: {preferences}
                    Accommodation: {accommodation}

                    Generate the complete travel itinerary.
                    """
                }
            ]

            # ==================================
            # 5. MCP TOOL CALLING
            # ==================================

            for iteration in range(10):

                response = ollama.chat(
                    model=MODEL,
                    messages=messages,
                    tools=tools
                )

                message = response["message"]

                messages.append(message)

                if not message.get("tool_calls"):
                    print("\n========================================")
                    print("         FINAL TRAVEL ITINERARY")
                    print("========================================")

                    print(message["content"])
                    break

                for tool_call in message["tool_calls"]:

                    name = tool_call["function"]["name"]

                    arguments = tool_call["function"]["arguments"]

                    print(f"\nCalling MCP tool: {name}")

                    result = await session.call_tool(
                        name,
                        arguments
                    )

                    output = "\n".join(
                        item.text
                        for item in result.content
                        if hasattr(item, "text")
                    )

                    print("Tool result:", output)

                    messages.append({
                        "role": "tool",
                        "content": output
                    })

            else:
                print("Agent reached its maximum tool-call limit.")


# ==========================================
# 6. RUN AGENT
# ==========================================

if __name__ == "__main__":
    asyncio.run(main())
