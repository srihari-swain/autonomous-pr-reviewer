import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv('/home/srihari/Documents/GEnAi/fynd/.env')
github_pat = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
async def main():
    
    async with MultiServerMCPClient(
        {
            "github": {
                "command": "/githubmcp/github-mcp-server/github-mcp-server",
                "args": ["stdio"],
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": github_pat,
                    "GITHUB_TOOLSETS": "repos,issues,pull_requests,code_security"
                }
            }
        }
    ) as client:
        tools = client.get_tools()
        print(tools)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())