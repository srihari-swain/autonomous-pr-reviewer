from typing import List, Optional, Dict, Any
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import PRReviewState from shared_types instead of schema
from src.configs.schema import PRReviewState

from src.agents import (
    pr_retriever_agent,
    code_understanding_agent,
    pr_review_comment_agent
)
from src.agents.supervisor_agent import SupervisorAgent

logger = logging.getLogger(__name__)

# --- Workflow Definition ---
workflow = StateGraph(PRReviewState)

# Create an instance of the SupervisorAgent that will coordinate all other agents
supervisor = SupervisorAgent()

# Add all agent nodes to the workflow
workflow.add_node("supervisor", supervisor.coordinate)
workflow.add_node("pr_retriever", pr_retriever_agent)
workflow.add_node("code_analyzer", code_understanding_agent)
workflow.add_node("comment_generator", pr_review_comment_agent)
workflow.add_node("final_summary", supervisor.compile_summary)

# Define a simple sequential workflow for testing purposes
# This ensures we get predictable results without complex conditional routing
workflow.add_edge("supervisor", "pr_retriever")
workflow.add_edge("pr_retriever", "code_analyzer")
workflow.add_edge("code_analyzer", "comment_generator")
workflow.add_edge("comment_generator", "final_summary")
workflow.add_edge("final_summary", END)

# Set the supervisor as the entry point
workflow.set_entry_point("supervisor")


memory = MemorySaver()

app = workflow.compile(checkpointer=memory) 
