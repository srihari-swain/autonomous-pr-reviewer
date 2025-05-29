from typing import TypedDict, List, Optional

# --- State Definition ---
class PRReviewState(TypedDict):
    """Represents the state of the PR review workflow."""
    repo_owner: str
    repo_name: str
    pr_number: Optional[int]
    pr_title: str
    pr_url: str
    pr_diff: str
    pr_files_changed: List[str]
    pr_commit_messages: List[str]
    code_summary: str
    identified_risks: List[str]
    generated_review_comments: str
    final_review_summary: str
