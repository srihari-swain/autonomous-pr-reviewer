"""
PR Review Comment Agent - Generates constructive review comments for a PR
"""

import json
from typing import Dict, Any
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool, ToolException
from langchain_core.callbacks.manager import CallbackManagerForToolRun

class PRReviewTool(BaseTool):
    """Tool for generating PR review comments."""
    
    name: str = "pr_review_tool"
    description: str = "Generates constructive review comments for a PR"
    
    model_name: str = "openai:gpt-4.1"
    
    def _run(self, *args, **kwargs) -> str:
        """Synchronous run method required by BaseTool."""
        raise NotImplementedError("This tool only supports async execution.")
    
    async def _arun(self, pr_data: str, code_analysis: str, run_manager: CallbackManagerForToolRun = None) -> str:
        """Run the tool asynchronously."""
        try:
            # Initialize LLM
            model = init_chat_model(self.model_name)
            
            # Create system message
            system_message = SystemMessage(
                content="You are the PR Review Comment Agent. Your task is to generate constructive review comments for a PR."
            )
            
            # Create prompt for generating PR comments
            prompt_template = ChatPromptTemplate.from_messages([
                system_message,
                HumanMessage(content=f"""
                Based on the PR data and code analysis below, generate constructive PR review comments.
                Include specific suggestions for improvements and potential fixes.
                
                Format your response as a structured JSON with these fields:
                - file_comments: List of objects with 'file', 'line', 'comment' fields
                - general_comments: List of general comments about the PR
                
                PR Data:
                {pr_data}
                
                Code Analysis:
                {code_analysis}
                """)
            ])
            
            # Get review comments from the LLM
            response = await model.ainvoke(prompt_template.format_messages())
            return response.content
            
        except Exception as e:
            raise ToolException(f"Error generating PR review comments: {str(e)}")

class PRReviewCommentAgent:
    """Agent that generates PR review comments"""
    
    def __init__(self, model_name: str = "openai:gpt-4.1"):
        """Initialize the PR Review Comment Agent.
        
        Args:
            model_name: The name of the LLM model to use
        """
        self.model_name = model_name
        self.review_tool = PRReviewTool(model_name=model_name)
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the PR Review Comment Agent.
        
        Args:
            state: The current workflow state
            
        Returns:
            Updated workflow state with review comments
        """
        print("Running PR Review Comment Agent...")
        
        try:
            # Check if we have required data
            if "pr_data" not in state or not state["pr_data"] or "code_analysis" not in state or not state["code_analysis"]:
                state["error"] = "Error: Missing data from previous agents"
                return state
            
            # Generate PR review comments
            review_comments = await self.review_tool._arun(state["pr_data"], state["code_analysis"])
            
            # Update the state with review comments
            state["review_comments"] = review_comments
            
            # Try to parse the review comments to extract key metrics
            try:
                comments_json = json.loads(review_comments)
                if "file_comments" in comments_json:
                    state["file_comments_count"] = len(comments_json["file_comments"])
                if "general_comments" in comments_json:
                    state["general_comments_count"] = len(comments_json["general_comments"])
            except json.JSONDecodeError:
                # If parsing fails, just continue without the extra metrics
                pass
                
            print("PR review comments generated successfully")
            return state
            
        except Exception as e:
            print(f"Error in PR Review Comment Agent: {str(e)}")
            state["error"] = f"Error in PR Review Comment Agent: {str(e)}"
            return state
