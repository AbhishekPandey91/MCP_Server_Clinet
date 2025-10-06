from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

async def main():
    print("🚀 Starting MCP Agent...")
    
    # Initialize MCP client with stdio transport for both servers
    print("📡 Configuring MCP servers...")
    client = MultiServerMCPClient(
            {
                "math": {
                    "command": "python",
                    "args": ["calculation_server.py"],
                    "transport": "stdio"
                },
                "Weather_server": {
                    "command": "python",
                    "args": ["WEATHER.py"],
                    "transport": "stdio"
                },
                "gmail-mcp-server":{
                    "command":"python",
                    "args":["gmail_server.py"],
                    "transport":"stdio"

                },
                "search_tools":{
                    "command":"python",
                    "args":["search_server.py"],
                    "transport":"stdio"
                },
                "google-workspace":{
                    "command":"python",
                    "args":["drive_calander_server.py"],
                    "transport":"stdio"
                },
                "openstreetmap":{
                    "command":"python",
                    "args":["map_server.py"],
                    "transport":"stdio"
                },
                "github":{
                    "command":"python",
                    "args":["github_server.py"],
                    "transport":"stdio"
                },
                "sqlite-db":{
                    "command":"python",
                    "args":["sql_server.py"],
                    "transport":"stdio"
                },
                "oogle-sheets-robotics":{
                    "command":"python",
                    "args":["robo_club_server.py"],
                    "transport":"stdio"

                }
                
            
                
            }
      )
    

    tools = await client.get_tools()
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=groq_api_key,
        temperature=0,
    )

    agent = create_react_agent(llm, tools)

    while True:
        user_input = input("You: ")

        # exit condition
        if user_input.lower() in ["bye", "exit", "quit"]:
            print("Chatbot: Goodbye! 👋")
            break

    
        try:
            ai_response = await agent.ainvoke(
                {"messages": [{"role": "user", "content": user_input}]}
            )
            print("\n AI Response:")
            print(ai_response['messages'][-1].content)
        except Exception as e:
            print(f"❌ Error in math query: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()