import logging
import re
from typing import Dict, Any, Callable, Tuple, Optional

from src.configs.schema import PRReviewState

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor Agent that coordinates the PR review process and compiles the final summary.
    This agent is the central coordinator that decides which agent to call next based on the current state.
    """
    
    def __init__(self):
        logger.info("Initializing Supervisor Agent")
    
    def parse_github_pr_url(self, url: str) -> Optional[Tuple[str, str, int]]:
        """
        Parses a GitHub PR URL to extract owner, repo, and PR number.
        """
        match = re.match(r"^(?:https?://)?github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:/.*)?$", url)
        if match:
            owner, repo, pr_number_str = match.groups()
            return owner, repo, int(pr_number_str)
        return None
    
    def coordinate(self, state: PRReviewState) -> Dict[str, Any]:
        """
        Coordinate the PR review process by checking the state and determining next steps.
        This is the main entry point for the Supervisor Agent that decides the workflow.
        """
        logger.info("Agent: SupervisorAgent - Coordinating PR review process")
        
        # If this is the first run with no data, initialize the state
        if not state:
            logger.info("Agent: SupervisorAgent - Initializing new PR review process")
            return {"status": "initialized", "message": "PR review process started"}
        
        # Check if we need to parse the PR URL to get repo_owner, repo_name, and pr_number
        if 'pr_url' in state and not state.get('repo_owner') and not state.get('repo_name'):
            parsed_url = self.parse_github_pr_url(state['pr_url'])
            if parsed_url:
                repo_owner, repo_name, pr_number = parsed_url
                logger.info(f"Agent: SupervisorAgent - Parsed PR URL: Owner={repo_owner}, Repo={repo_name}, PR#={pr_number}")
                return {**state, "repo_owner": repo_owner, "repo_name": repo_name, "pr_number": pr_number}
        
        # Check if we have all the necessary information to compile the final summary
        if self._is_ready_for_summary(state):
            logger.info("Agent: SupervisorAgent - All data collected, ready for final summary")
            # Don't compile the summary here - the workflow will route to the final_summary node
            return state
        
        # Determine what data is missing and log the next step
        missing_data = self._get_missing_data(state)
        logger.info(f"Agent: SupervisorAgent - Missing data: {missing_data}")
        
        # Return the current state with status information
        return {**state, "status": "in_progress", "missing_data": missing_data}
    
    def _is_ready_for_summary(self, state: PRReviewState) -> bool:
        """
        Check if all required data is available to compile the summary.
        """
        required_keys = ['pr_title', 'pr_url', 'code_summary', 'identified_risks', 'generated_review_comments']
        return all(key in state for key in required_keys)
    
    def _get_missing_data(self, state: PRReviewState) -> list:
        """
        Identify which required data is missing from the state.
        """
        required_keys = ['pr_title', 'pr_url', 'code_summary', 'identified_risks', 'generated_review_comments']
        return [key for key in required_keys if key not in state]
        
    def _generate_summary(self, state: PRReviewState) -> str:
        """
        Helper method to generate the final review summary string from state data.
        """
        title = state.get('pr_title', 'N/A')
        url = state.get('pr_url', 'N/A')
        summary = state.get('code_summary', 'No summary.')
        risks = state.get('identified_risks', [])
        comments = state.get('generated_review_comments', 'No comments.')
        risks_formatted = "\n".join([f"- {risk}" for risk in risks]) if risks else "- No specific risks highlighted."

        final_summary = f"""**Automated PR Review Summary**
PR Title: {title}
PR URL: {url}

1. Summary of Changes:
{summary}

2. Identified Potential Risks/Concerns:
{risks_formatted}

3. Detailed Review Comments & Suggestions:
{comments}
--- End of Automated Review ---""" 
        
        return final_summary.strip()
    
    def compile_summary(self, state: PRReviewState) -> Dict[str, Any]:
        """
        Compile the final review summary based on the information collected by other agents.
        """
        logger.info("Agent: SupervisorAgent - Compiling final review")
        
        # Use the helper method to generate the summary
        final_summary = self._generate_summary(state)
        logger.info("Agent: SupervisorAgent - Summary compiled.")
        
        # Important: Return both the final_review_summary and the original state
        # This ensures all state information is preserved while adding the summary
        return {**state, "final_review_summary": final_summary}


# For backward compatibility and easy integration with existing code
def supervisor_agent_compile_summary(state: PRReviewState) -> Dict[str, Any]:
    """
    Legacy function that creates a SupervisorAgent instance and calls its compile_summary method.
    """
    supervisor = SupervisorAgent()
    return supervisor.compile_summary(state)
