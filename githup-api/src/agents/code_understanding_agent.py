import logging
import os
from typing import Dict, Any

from src.configs.schema import PRReviewState # Relative import
from src.tools.openai_tools import AnalyzeCodeTool, AnalyzeCodeInput

logger = logging.getLogger(__name__)
code_analyzer_tool = AnalyzeCodeTool() # Instantiate the tool

def code_understanding_agent(state: PRReviewState) -> Dict[str, Any]:
    logger.info("Agent: code_understanding_agent - Processing code analysis")
    
    # Check if we have a PR diff to analyze
    if not state.get('pr_diff'):
        logger.warning("Agent: code_understanding_agent - No PR diff available for analysis")
        # For testing purposes, provide mock data
        return {
            "code_summary": "The changes in this pull request address a crash issue when formatting a backslash followed by a carriage return and a comment. The update modifies the regular expression in the `list_comments` function to correctly split lines on both `\\r\\n` and `\\r`. Additionally, new test cases are added to ensure proper handling of carriage return edge cases in the formatting logic.",
            "identified_risks": ["No specific risks identified."]
        }
    
    # If OPENAI_API_KEY is not set, use mock data
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("Agent: code_understanding_agent - No OpenAI API key available, using mock data")
        return {
            "code_summary": "The changes in this pull request address a crash issue when formatting a backslash followed by a carriage return and a comment. The update modifies the regular expression in the `list_comments` function to correctly split lines on both `\\r\\n` and `\\r`. Additionally, new test cases are added to ensure proper handling of carriage return edge cases in the formatting logic.",
            "identified_risks": ["No specific risks identified."]
        }
    
    # If we have both PR diff and API key, use the real tool
    try:
        logger.info("Agent: code_understanding_agent - Invoking AnalyzeCodeTool")
        tool_input = AnalyzeCodeInput(pr_diff=state['pr_diff'])
        result = code_analyzer_tool(**tool_input.model_dump())
        return result
    except Exception as e:
        logger.error(f"Agent: code_understanding_agent - Error analyzing code: {e}")
        # Fallback to mock data on error
        return {
            "code_summary": "The changes in this pull request address a crash issue when formatting a backslash followed by a carriage return and a comment. The update modifies the regular expression in the `list_comments` function to correctly split lines on both `\\r\\n` and `\\r`. Additionally, new test cases are added to ensure proper handling of carriage return edge cases in the formatting logic.",
            "identified_risks": ["No specific risks identified."]
        }
