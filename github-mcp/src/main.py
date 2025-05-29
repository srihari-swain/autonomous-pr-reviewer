"""
Main entry point for the PR review system.
Uses LangGraph to orchestrate a workflow of specialized agents.
"""
import asyncio
import argparse
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Import the workflow graph
from src.graph.graph import create_workflow_graph, WorkflowState

# Load environment variables
load_dotenv()

# Default GitHub repository details
DEFAULT_REPO_OWNER = "psf"
DEFAULT_REPO_NAME = "black"

async def run_pr_review(repo_owner: str, repo_name: str, pr_number: Optional[int] = None, verbose: bool = True) -> Dict[str, Any]:
    """Run the PR review workflow.
    
    Args:
        repo_owner: The GitHub repository owner
        repo_name: The GitHub repository name
        pr_number: Optional PR number to review. If None, reviews the latest PR.
        verbose: Whether to print progress messages to console
        
    Returns:
        The final workflow state with PR review results
    """
    # Create the workflow graph
    workflow = create_workflow_graph(repo_owner, repo_name, pr_number)
    
    if verbose:
        print(f"\n=== Starting PR Review for {repo_owner}/{repo_name} ===\n")
        if pr_number:
            print(f"Reviewing PR #{pr_number}")
        else:
            print("Reviewing latest open PR")
    
    try:
        # Run the workflow with an empty initial state
        result = await workflow.ainvoke(WorkflowState())
        return result
    except Exception as e:
        if verbose:
            print(f"Error in PR review workflow: {str(e)}")
        raise

def print_review_summary(result: Dict[str, Any]) -> None:
    """Print a summary of the PR review.
    
    Args:
        result: The workflow result
    """
    # Check for errors
    if 'error' in result and result['error']:
        print(f"\nError in workflow: {result['error']}\n")
        return
    
    # Print the final result
    print("\n=== PR REVIEW SUMMARY ===\n")
    
    # Print PR metadata if available
    if 'pr_number' in result and result['pr_number']:
        print(f"PR #{result['pr_number']}: {result.get('pr_title', 'No title')}")
        print(f"Author: {result.get('pr_author', 'Unknown')}")
    
    # Print the final review
    if 'final_review' in result and result['final_review']:
        print("\n" + result['final_review'])
    else:
        print("\nNo final review was generated.")
    
    print("\n=== PR Review Complete ===\n")

async def main():
    """Main entry point for the PR review system."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='GitHub PR Review System')
    parser.add_argument('--owner', type=str, default=DEFAULT_REPO_OWNER,
                        help=f'GitHub repository owner (default: {DEFAULT_REPO_OWNER})')
    parser.add_argument('--repo', type=str, default=DEFAULT_REPO_NAME,
                        help=f'GitHub repository name (default: {DEFAULT_REPO_NAME})')
    parser.add_argument('--pr', type=int, default=None,
                        help='PR number to review (default: latest open PR)')
    parser.add_argument('--json', action='store_true',
                        help='Output results as JSON instead of human-readable format')
    args = parser.parse_args()
    
    try:
        # Run the PR review
        result = await run_pr_review(args.owner, args.repo, args.pr)
        
        # Print the review summary
        if args.json:
            import json
            print(json.dumps(result, indent=2))
        else:
            print_review_summary(result)
        return result
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    asyncio.run(main())
