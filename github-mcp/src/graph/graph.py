"""
LangGraph setup for PR review workflow
"""

from typing import Dict, Any, TypedDict, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

from src.agents.pr_retriever import PRRetrieverAgent
from src.agents.code_understanding import CodeUnderstandingAgent
from src.agents.pr_review_comment import PRReviewCommentAgent
from src.agents.supervisor import SupervisorAgent

# Define the state for our workflow
class WorkflowState(BaseModel):
    """State for the PR review workflow."""
    # PR data
    pr_data: Optional[str] = None
    pr_number: Optional[int] = None
    pr_title: Optional[str] = None
    pr_author: Optional[str] = None
    
    # Analysis data
    code_analysis: Optional[str] = None
    analysis_summary: Optional[str] = None
    risky_practices_count: Optional[int] = None
    quality_issues_count: Optional[int] = None
    
    # Review data
    review_comments: Optional[str] = None
    file_comments_count: Optional[int] = None
    general_comments_count: Optional[int] = None
    
    # Final review
    final_review: Optional[str] = None
    
    # Error tracking
    error: Optional[str] = None

# Agent functions - wrapped to handle async properly
def create_pr_retriever_node(repo_owner: str, repo_name: str, pr_number: Optional[int] = None):
    async def pr_retriever_node(state: WorkflowState) -> Dict[str, Any]:
        """Run the PR Retriever Agent."""
        agent = PRRetrieverAgent()
        result = await agent.run(state.dict(), repo_owner, repo_name, pr_number)
        return result
    return pr_retriever_node

def create_code_understanding_node():
    async def code_understanding_node(state: WorkflowState) -> Dict[str, Any]:
        """Run the Code Understanding Agent."""
        agent = CodeUnderstandingAgent()
        result = await agent.run(state.dict())
        return result
    return code_understanding_node

def create_pr_review_comment_node():
    async def pr_review_comment_node(state: WorkflowState) -> Dict[str, Any]:
        """Run the PR Review Comment Agent."""
        agent = PRReviewCommentAgent()
        result = await agent.run(state.dict())
        return result
    return pr_review_comment_node

def create_supervisor_node():
    async def supervisor_node(state: WorkflowState) -> Dict[str, Any]:
        """Run the Supervisor Agent."""
        agent = SupervisorAgent()
        result = await agent.run(state.dict())
        return result
    return supervisor_node

# Routing functions
def route_after_pr_retrieval(state: WorkflowState) -> str:
    """Determine next step after PR retrieval."""
    if state.error:
        return END
    return "code_understanding"

def route_after_code_understanding(state: WorkflowState) -> str:
    """Determine next step after code understanding."""
    if state.error:
        return END
    return "pr_review_comment"

def route_after_pr_review(state: WorkflowState) -> str:
    """Determine next step after PR review comments."""
    if state.error:
        return END
    return "supervisor"

def route_after_supervisor(state: WorkflowState) -> str:
    """Determine next step after supervisor agent."""
    # Always end after supervisor agent
    return END

def create_workflow_graph(repo_owner: str, repo_name: str, pr_number: Optional[int] = None) -> StateGraph:
    """Create the workflow graph for PR review.
    
    Args:
        repo_owner: The GitHub repository owner
        repo_name: The GitHub repository name
        pr_number: Optional PR number to review. If None, reviews the latest PR.
        
    Returns:
        Compiled StateGraph for the PR review workflow
    """
    # Create the state graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes for each agent
    workflow.add_node("pr_retriever", create_pr_retriever_node(repo_owner, repo_name, pr_number))
    workflow.add_node("code_understanding", create_code_understanding_node())
    workflow.add_node("pr_review_comment", create_pr_review_comment_node())
    workflow.add_node("supervisor", create_supervisor_node())
    
    # Add edges with conditional routing
    workflow.add_conditional_edges(
        "pr_retriever",
        route_after_pr_retrieval,
        {"code_understanding": "code_understanding", END: END}
    )
    workflow.add_conditional_edges(
        "code_understanding",
        route_after_code_understanding,
        {"pr_review_comment": "pr_review_comment", END: END}
    )
    workflow.add_conditional_edges(
        "pr_review_comment",
        route_after_pr_review,
        {"supervisor": "supervisor", END: END}
    )
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {END: END}
    )
    
    # Set the entry point
    workflow.set_entry_point("pr_retriever")
    
    # Compile the graph
    return workflow.compile()
