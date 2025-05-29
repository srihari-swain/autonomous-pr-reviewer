from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from github import Github, GithubException
import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")

class GetPRInfoInput(BaseModel):
    repo_owner: str = Field(description="Owner of the repository")
    repo_name: str = Field(description="Name of the repository")
    pr_number: Optional[int] = Field(None, description="PR number; if None, fetches the latest open PR")

class GetPRInfoTool:
    name: str = "get_pr_info_tool"
    description: str = "Fetches metadata for a GitHub Pull Request including title, URL, diff, files changed, and commit messages."
    args_schema: type[BaseModel] = GetPRInfoInput

    def __call__(self, repo_owner: str, repo_name: str, pr_number: Optional[int] = None) -> Dict[str, Any]:
        if not GITHUB_TOKEN:
            logger.error(f"Tool '{self.name}': GITHUB_TOKEN is not set.")
            raise ValueError("GITHUB_TOKEN environment variable is not set.")
        
        logger.info(f"Tool '{self.name}': Fetching PR for {repo_owner}/{repo_name}, PR #: {pr_number or 'latest'}")
        gh = Github(GITHUB_TOKEN)
        try:
            repo = gh.get_repo(f"{repo_owner}/{repo_name}")
            if pr_number is not None:
                pr = repo.get_pull(pr_number)
            else:
                prs = repo.get_pulls(state='open', sort='created', direction='desc')
                if prs.totalCount == 0:
                    raise ValueError(f"No open PRs found in {repo_owner}/{repo_name}.")
                pr = prs[0]
            
            logger.info(f"Tool '{self.name}': Found PR #{pr.number}: {pr.title}")

            diff_response = requests.get(pr.diff_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
            diff_response.raise_for_status()
            pr_diff = diff_response.text

            files_changed = [file.filename for file in pr.get_files()]
            commit_messages = [commit.commit.message for commit in pr.get_commits()]

            return {
                "pr_number": pr.number,
                "pr_title": pr.title,
                "pr_url": pr.html_url,
                "pr_diff": pr_diff,
                "pr_files_changed": files_changed,
                "pr_commit_messages": commit_messages,
            }
        except GithubException as e:
            logger.error(f"Tool '{self.name}': GitHub API Error: {e.status} - {e.data}")
            raise
        except requests.RequestException as e:
            logger.error(f"Tool '{self.name}': Error fetching diff: {e}")
            raise
        except ValueError as e: # Catch "No open PRs"
            logger.error(f"Tool '{self.name}': {e}")
            raise
