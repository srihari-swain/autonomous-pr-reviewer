import logging
import re
from typing import Dict, Any, Optional, Tuple

from src.configs.schema import PRReviewState 
from src.tools.github_tools import GetPRInfoTool, GetPRInfoInput

logger = logging.getLogger(__name__)
github_tool = GetPRInfoTool() 

def parse_github_pr_url(url: str) -> Optional[Tuple[str, str, int]]:
    """
    Parses a GitHub PR URL to extract owner, repo, and PR number.
    """
    match = re.match(r"^(?:https?://)?github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:/.*)?$", url)
    if match:
        owner, repo, pr_number_str = match.groups()
        return owner, repo, int(pr_number_str)
    return None

def pr_retriever_agent(state: PRReviewState) -> Dict[str, Any]: # Return only the updated parts of the state
    logger.info("Agent: pr_retriever_agent - Processing PR information")
    
    # Check if we have a PR URL but no repo_owner/repo_name/pr_number
    if 'pr_url' in state and (not state.get('repo_owner') or not state.get('repo_name') or not state.get('pr_number')):
        logger.info(f"Agent: pr_retriever_agent - Parsing PR URL: {state['pr_url']}")
        parsed_url = parse_github_pr_url(state['pr_url'])
        if parsed_url:
            repo_owner, repo_name, pr_number = parsed_url
            logger.info(f"Agent: pr_retriever_agent - Parsed PR URL: Owner={repo_owner}, Repo={repo_name}, PR#={pr_number}")
            state['repo_owner'] = repo_owner
            state['repo_name'] = repo_name
            state['pr_number'] = pr_number
    
    # Now retrieve the PR information using the GitHub tool
    if state.get('repo_owner') and state.get('repo_name') and state.get('pr_number'):
        logger.info(f"Agent: pr_retriever_agent - Retrieving PR info for {state['repo_owner']}/{state['repo_name']}#{state['pr_number']}")
        tool_input = GetPRInfoInput(
            repo_owner=state['repo_owner'],
            repo_name=state['repo_name'],
            pr_number=state['pr_number']
        )
        try:
            result = github_tool(**tool_input.model_dump())
            logger.info("Agent: pr_retriever_agent - Successfully retrieved PR information")
            return result
        except Exception as e:
            logger.error(f"Agent: pr_retriever_agent - Error retrieving PR info: {e}")
            return {"error": str(e)}
    else:
        logger.error("Agent: pr_retriever_agent - Missing required PR information (repo_owner, repo_name, or pr_number)")
        return {"error": "Missing required PR information"}