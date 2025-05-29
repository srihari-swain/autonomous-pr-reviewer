"""
Code Understanding Agent - Analyzes PR code changes to identify issues and summarize changes
"""

import json
from typing import Dict, Any
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool, ToolException
from langchain_core.callbacks.manager import CallbackManagerForToolRun

class CodeAnalysisTool(BaseTool):
    """Tool for analyzing code changes in a PR."""
    
    name: str = "code_analysis_tool"
    description: str = "Analyzes code changes in a PR to identify issues and summarize changes"
    
    model_name: str = "openai:gpt-4.1"
    
    def _run(self, *args, **kwargs) -> str:
        """Synchronous run method required by BaseTool."""
        raise NotImplementedError("This tool only supports async execution.")
    
    async def _arun(self, pr_data: str, run_manager: CallbackManagerForToolRun = None) -> str:
        """Run the tool asynchronously."""
        try:
            # Initialize LLM
            model = init_chat_model(self.model_name)
            
            # Create system message
            system_message = SystemMessage(
                content="You are the Code Understanding Agent. Your task is to analyze code changes in a PR and identify potential issues."
            )
            
            # Create prompt for code analysis
            prompt_template = ChatPromptTemplate.from_messages([
                system_message,
                HumanMessage(content=f"""
                Analyze the following PR data and provide:
                1. A summary of the changes
                2. Identification of any risky or poor coding practices
                3. Code quality issues
                
                Format your response as a structured JSON with these fields:
                - summary: A concise summary of the changes
                - risky_practices: List of objects with 'file', 'line', and 'description' fields
                - code_quality_issues: List of objects with 'file', 'line', and 'description' fields
                
                PR Data:
                {pr_data}
                """)
            ])
            
            # Get analysis from the LLM
            response = await model.ainvoke(prompt_template.format_messages())
            return response.content
            
        except Exception as e:
            raise ToolException(f"Error analyzing code changes: {str(e)}")

class CodeUnderstandingAgent:
    """Agent that analyzes code changes using an LLM"""
    
    def __init__(self, model_name: str = "openai:gpt-4.1"):
        """Initialize the Code Understanding Agent.
        
        Args:
            model_name: The name of the LLM model to use
        """
        self.model_name = model_name
        self.analysis_tool = CodeAnalysisTool(model_name=model_name)
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the Code Understanding Agent.
        
        Args:
            state: The current workflow state
            
        Returns:
            Updated workflow state with code analysis
        """
        print("Running Code Understanding Agent...")
        
        try:
            # Check if we have PR data
            if "pr_data" not in state or not state["pr_data"]:
                state["error"] = "Error: No PR data found from PR Retriever Agent"
                return state
            
            # Analyze the code changes
            code_analysis = await self.analysis_tool._arun(state["pr_data"])
            
            # Update the state with code analysis
            state["code_analysis"] = code_analysis
            
            # Try to parse the analysis to extract key metrics
            try:
                analysis_json = json.loads(code_analysis)
                if "summary" in analysis_json:
                    state["analysis_summary"] = analysis_json["summary"]
                if "risky_practices" in analysis_json:
                    state["risky_practices_count"] = len(analysis_json["risky_practices"])
                if "code_quality_issues" in analysis_json:
                    state["quality_issues_count"] = len(analysis_json["code_quality_issues"])
            except json.JSONDecodeError:
                # If parsing fails, just continue without the extra metrics
                pass
                
            print("Code analysis completed successfully")
            return state
            
        except Exception as e:
            print(f"Error in Code Understanding Agent: {str(e)}")
            state["error"] = f"Error in Code Understanding Agent: {str(e)}"
            return state
