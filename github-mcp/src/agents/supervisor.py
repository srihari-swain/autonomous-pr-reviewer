"""
Supervisor Agent - Coordinates the PR review process and produces final summary
"""

from typing import Dict, Any
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool, ToolException
from langchain_core.callbacks.manager import CallbackManagerForToolRun

class FinalReviewTool(BaseTool):
    """Tool for generating a final PR review summary."""
    
    name: str = "final_review_tool"
    description: str = "Generates a comprehensive PR review summary"
    
    model_name: str = "openai:gpt-4.1"
    
    def _run(self, *args, **kwargs) -> str:
        """Synchronous run method required by BaseTool."""
        raise NotImplementedError("This tool only supports async execution.")
    
    async def _arun(self, pr_data: str, code_analysis: str, review_comments: str, run_manager: CallbackManagerForToolRun = None) -> str:
        """Run the tool asynchronously."""
        try:
            # Initialize LLM
            model = init_chat_model(self.model_name)
            
            # Create system message
            system_message = SystemMessage(
                content="You are the Supervisor Agent. Your task is to synthesize all the information from the PR review process and produce a final summary."
            )
            
            # Create prompt for final review summary
            prompt_template = ChatPromptTemplate.from_messages([
                system_message,
                HumanMessage(content=f"""
                Synthesize the following information into a comprehensive PR review summary:
                
                PR Data:
                {pr_data}
                
                Code Analysis:
                {code_analysis}
                
                Review Comments:
                {review_comments}
                
                Your summary should include:
                1. PR overview (title, author, scope of changes)
                2. Key findings from the code analysis
                3. Most important review comments and suggestions
                4. Overall assessment (approve, request changes, etc.)
                5. Next steps for the PR author
                
                Format your response as a well-structured markdown document.
                """)
            ])
            
            # Get final review summary from the LLM
            response = await model.ainvoke(prompt_template.format_messages())
            return response.content
            
        except Exception as e:
            raise ToolException(f"Error generating final review summary: {str(e)}")

class SupervisorAgent:
    """Agent that coordinates the review process and produces final summary"""
    
    def __init__(self, model_name: str = "openai:gpt-4.1"):
        """Initialize the Supervisor Agent.
        
        Args:
            model_name: The name of the LLM model to use
        """
        self.model_name = model_name
        self.final_review_tool = FinalReviewTool(model_name=model_name)
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Supervisor Agent.
        
        Args:
            state: The current workflow state
            
        Returns:
            Updated workflow state with final review
        """
        print("Running Supervisor Agent...")
        
        try:
            # Check if we have required data
            if "pr_data" not in state or not state["pr_data"] or \
               "code_analysis" not in state or not state["code_analysis"] or \
               "review_comments" not in state or not state["review_comments"]:
                state["error"] = "Error: Missing data from one or more agents"
                return state
            
            # Generate final review summary
            final_review = await self.final_review_tool._arun(
                state["pr_data"], 
                state["code_analysis"], 
                state["review_comments"]
            )
            
            # Update the state with final review
            state["final_review"] = final_review
                
            print("Final review summary generated successfully")
            return state
            
        except Exception as e:
            print(f"Error in Supervisor Agent: {str(e)}")
            state["error"] = f"Error in Supervisor Agent: {str(e)}"
            return state
