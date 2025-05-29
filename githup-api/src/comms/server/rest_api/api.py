from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file at the earliest opportunity
load_dotenv()

from src.graph.graph import app 
from src.configs.schema import PRReviewState 
from src.configs.config_loader import read_base_config

# --- Load Configuration ---
config_data = read_base_config()

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Environment Variables / Secrets --- 
# Ensure these are loaded after load_dotenv() has been called.
# The GitHub MCP server and tools specifically require GITHUB_PERSONAL_ACCESS_TOKEN.
GITHUB_PAT = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not GITHUB_PAT:
    logger.critical("CRITICAL: GITHUB_PERSONAL_ACCESS_TOKEN is not set. FastAPI server may not function correctly for GitHub operations.")
if not OPENAI_API_KEY:
    logger.critical("CRITICAL: OPENAI_API_KEY is not set. FastAPI server may not function correctly for OpenAI operations.")

# Initialize FastAPI app using values from config_data
fast_api_app = FastAPI(
    title=config_data.get("title", "PR Review API"), 
    description=config_data.get("description", "An API to trigger automated PR reviews."),
    version=config_data.get("version", "0.1.0"),
    docs_url=config_data.get("docs_url", "/docs"),
    redoc_url=config_data.get("redoc_url", "/redoc")
)

# --- CORS Middleware --- 
# Using settings from config_data
fast_api_app.add_middleware(
    CORSMiddleware,
    allow_origins=config_data.get("allow_origins", ["*"]), 
    allow_credentials=config_data.get("allow_credentials", True),
    allow_methods=config_data.get("allow_methods", ["*"]),
    allow_headers=config_data.get("allow_headers", ["*"]),
)

class PRReviewRequest(BaseModel):
    pr_url: str

class PRReviewResponse(BaseModel):
    pr_title: str
    pr_url: str
    review_summary: str 

def parse_github_pr_url(url: str) -> tuple[str, str, int] | None:
    """Parses a GitHub PR URL to extract owner, repo, and PR number."""

    match = re.match(r"^(?:https?://)?github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:/.*)?$", url)
    if match:
        owner, repo, pr_number_str = match.groups()
        return owner, repo, int(pr_number_str)
    return None

@fast_api_app.post("/review-pr/", response_model=PRReviewResponse)
async def review_pr_endpoint(request: PRReviewRequest):
    logger.info(f"Received PR review request for URL: {request.pr_url}")

    if not GITHUB_PAT or not OPENAI_API_KEY:
        # Check for GITHUB_PERSONAL_ACCESS_TOKEN here as well
        logger.error("API keys (GITHUB_PERSONAL_ACCESS_TOKEN or OPENAI_API_KEY) are missing in the environment.")
        raise HTTPException(status_code=500, detail="Server configuration error: Critical API keys missing.")

    parsed_url = parse_github_pr_url(request.pr_url)
    if not parsed_url:
        logger.error(f"Invalid GitHub PR URL format: {request.pr_url}")
        raise HTTPException(status_code=400, detail="Invalid GitHub PR URL format. Expected format: https://github.com/owner/repo/pull/number")
    
    repo_owner, repo_name, pr_number = parsed_url
    logger.info(f"Parsed PR details: Owner={repo_owner}, Repo={repo_name}, PR#={pr_number}")

    initial_run_state = PRReviewState(
        repo_owner=repo_owner,
        repo_name=repo_name,
        pr_number=pr_number,
        pr_title="", 
        pr_url=request.pr_url,  # Pass the PR URL from the request
        pr_diff="", 
        pr_files_changed=[], 
        pr_commit_messages=[],
        code_summary="", 
        identified_risks=[], 
        generated_review_comments="", 
        final_review_summary=""
    )

    thread_id = f"pr-review-api-{repo_owner}-{repo_name}-{pr_number}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        logger.info(f"Invoking LangGraph app for PR: {request.pr_url} with thread_id: {thread_id}")
        final_state = await app.ainvoke(initial_run_state, config=config)
        logger.info(f"LangGraph app completed for PR: {request.pr_url}")

        logger.info(f"Final state from workflow: {final_state}")
        
        # If we have PR title and URL, we can generate a response even if final_review_summary isn't available yet
        if final_state and 'pr_title' in final_state:
            # If final_review_summary is available, use it
            if 'final_review_summary' in final_state:
                review_summary = final_state['final_review_summary']
            # Otherwise, try to generate it on the fly if we have the necessary components
            elif all(k in final_state for k in ['code_summary', 'identified_risks', 'generated_review_comments']):
                title = final_state.get('pr_title', 'N/A')
                url = final_state.get('pr_url', request.pr_url)
                summary = final_state.get('code_summary', 'No summary.')
                risks = final_state.get('identified_risks', [])
                comments = final_state.get('generated_review_comments', 'No comments.')
                risks_formatted = "\n".join([f"- {risk}" for risk in risks]) if risks else "- No specific risks highlighted."
                
                review_summary = f"""**Automated PR Review Summary**
PR Title: {title}
PR URL: {url}

1. Summary of Changes:
{summary}

2. Identified Potential Risks/Concerns:
{risks_formatted}

3. Detailed Review Comments & Suggestions:
{comments}
--- End of Automated Review ---""".strip()
            else:
                # If we don't have enough information, return what we have with an empty review summary
                review_summary = ""
                
            return PRReviewResponse(
                pr_title=final_state.get('pr_title', 'N/A'),
                pr_url=final_state.get('pr_url', request.pr_url),
                review_summary=review_summary
            )
        else:
            logger.error(f"Workflow completed for {request.pr_url}, but key information for response is missing in final_state: {final_state}")
            raise HTTPException(status_code=500, detail="Workflow completed, but failed to generate full review summary.")

    except ValueError as ve: 
        logger.error(f"ValueError during workflow for {request.pr_url}: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error during workflow for {request.pr_url}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during PR review: {e}")
