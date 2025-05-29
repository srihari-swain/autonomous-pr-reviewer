"""
PR Retriever Agent - Fetches metadata of PRs using GitHub API via MCP
"""

import json
from typing import Dict, Any, List
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from src.tools.github_tools import get_github_tools

class PRRetrieverAgent:
    """Agent that fetches PR metadata using GitHub MCP"""
    
    def __init__(self, model_name: str = "openai:gpt-4.1"):
        """Initialize the PR Retriever Agent.
        
        Args:
            model_name: The name of the LLM model to use
        """
        self.model_name = model_name
        self.llm = init_chat_model(model_name)
    
    async def run(self, state: Dict[str, Any], repo_owner: str, repo_name: str, pr_number: int = None) -> Dict[str, Any]:
        """Run the PR Retriever Agent.
        
        Args:
            state: The current workflow state
            repo_owner: The GitHub repository owner
            repo_name: The GitHub repository name
            pr_number: Optional PR number to retrieve. If None, gets the latest PR.
            
        Returns:
            Updated workflow state with PR data
        """
        print(f"Running PR Retriever Agent for {repo_owner}/{repo_name}...")
        
        try:
            # Get GitHub tools
            github_tools = get_github_tools(repo_owner=repo_owner, repo_name=repo_name, pr_number=pr_number)
            
            # Extract PR data using tools
            pr_info = await github_tools[0]._arun()  # GetPRTool
            pr_files = await github_tools[1]._arun()  # GetPRFilesTool
            pr_diff = await github_tools[2]._arun()   # GetPRDiffTool
            
            # Combine the data into a structured format
            pr_data = {
                "pr_number": pr_info.get("number"),
                "title": pr_info.get("title"),
                "description": pr_info.get("body"),
                "author": pr_info.get("user", {}).get("login"),
                "files_changed": pr_files,
                "diff": pr_diff,
                "commit_messages": self._extract_commit_messages(pr_info)
            }
            
            # Update the state with PR data
            state["pr_data"] = json.dumps(pr_data, indent=2)
            state["pr_number"] = pr_data["pr_number"]
            state["pr_title"] = pr_data["title"]
            state["pr_author"] = pr_data["author"]
            
            print(f"Successfully retrieved data for PR #{pr_data['pr_number']}: {pr_data['title']}")
            return state
            
        except Exception as e:
            print(f"Error in PR Retriever Agent: {str(e)}")
            state["error"] = f"Error in PR Retriever Agent: {str(e)}"
            return state
    
    def _extract_commit_messages(self, pr_info: Dict[str, Any]) -> List[str]:
        """Extract commit messages from PR info."""
        messages = []
        if "commits" in pr_info and isinstance(pr_info["commits"], list):
            for commit in pr_info["commits"]:
                if "commit" in commit and "message" in commit["commit"]:
                    messages.append(commit["commit"]["message"])
        return messages
