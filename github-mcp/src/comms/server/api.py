"""
FastAPI endpoint for GitHub PR Review System
"""

import re
import asyncio
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from src.main import run_pr_review

app = FastAPI(
    title="GitHub PR Review API",
    description="API for reviewing GitHub Pull Requests",
    version="1.0.0"
)

class PRReviewRequest(BaseModel):
    """Request model for PR review API."""
    repo_url: str
    pr_number: Optional[int] = None
    
    @validator('repo_url')
    def validate_repo_url(cls, v):
        """Validate GitHub repository URL."""
        pattern = r'^https?://github\.com/([^/]+)/([^/]+)/?.*$'
        match = re.match(pattern, v)
        if not match:
            raise ValueError("Invalid GitHub repository URL. Format should be: https://github.com/owner/repo")
        return v
    
    def parse_owner_and_repo(self):
        """Parse owner and repo from the GitHub URL."""
        pattern = r'^https?://github\.com/([^/]+)/([^/]+)/?.*$'
        match = re.match(pattern, self.repo_url)
        if match:
            return match.group(1), match.group(2)
        return None, None

class PRReviewResponse(BaseModel):
    """Response model for PR review API."""
    repo_owner: str
    repo_name: str
    pr_number: Optional[int]
    pr_title: Optional[str]
    pr_author: Optional[str]
    summary: str
    final_review: str

@app.post("/review-pr", response_model=PRReviewResponse)
async def review_pr(request: PRReviewRequest):
    """
    Review a GitHub Pull Request.
    
    - **repo_url**: GitHub repository URL (e.g., https://github.com/username/repo)
    - **pr_number**: PR number to review (optional, will use latest if not provided)
    """
    owner, repo = request.parse_owner_and_repo()
    if not owner or not repo:
        raise HTTPException(status_code=400, detail="Failed to parse repository owner and name from URL")
    
    try:
        result = await run_pr_review(owner, repo, request.pr_number)
        
        return PRReviewResponse(
            repo_owner=owner,
            repo_name=repo,
            pr_number=result.get("pr_number"),
            pr_title=result.get("pr_title"),
            pr_author=result.get("pr_author"),
            summary=result.get("summary", ""),
            final_review=result.get("final_review", "No final review was generated.")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reviewing PR: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
