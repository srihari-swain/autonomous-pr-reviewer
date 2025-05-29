# Automated PR Review System with LangGraph


## Author Information

- Developer: Srihari Swain
- Email: srihariswain2001@gmail.com
- GitHub: https://github.com/srihari-swain

## Project Timeline

- Development Time: Approximately 7 hours


## overview

This project implements an automated PR (Pull Request) review system using LangGraph, OpenAI, and the GitHub API. It can fetch PR details, analyze code changes, identify risks, and generate review comments.

## Project Structure

```
github-mcp/
├── src/
│   ├── agents/                   # Agent logic modules
│   │   ├── __init__.py
│   │   ├── pr_retriever.py       # Fetches PR metadata
│   │   ├── code_understanding.py # Analyzes code changes
│   │   ├── pr_review_comment.py  # Generates review comments
│   │   └── supervisor.py         # Coordinates the review workflow
│   │
│   ├── comms/server/          # API server implementation
│   │   └── api.py               # FastAPI application
│   │
│   ├── graph/                 # Workflow definition
│   │   └── graph.py             # LangGraph workflow setup
│   │
│   ├── tools/                 # Utility tools
│   │   └── github_tools.py      # MCP-based GitHub API tools
│   │
│   └── main.py                # Application entry point
│
├── test_api.py               # Test script for the API
├── requirements.txt           # Python dependencies
└── .env.example              # Example environment variables
```

## Features

* Fetches PR information (title, diff, files changed, commit messages) from GitHub.
* Analyzes code changes using OpenAI models to generate summaries and identify risks.
* Generates PR review comments based on the analysis.
* Provides a final summary of the review.
* Exposes functionality via a FastAPI endpoint.
* Uses LangGraph for defining and managing the review workflow.
* Configuration driven via environment variables and settings.

## Agent Design

The system uses a hierarchical agent architecture managed by a LangGraph `StateGraph` (defined in `src/graph/graph.py`). The Supervisor Agent coordinates the workflow of specialized agents, each responsible for a specific task in the PR review process.

### Hierarchical Agent System

1. **Supervisor Agent** (`src/agents/supervisor.py`):
   - **Role**: Central coordinator of the entire agent system
   - **Functions**: 
     - Parses PR URLs to extract repository owner, name, and PR number
     - Coordinates the workflow between specialized agents
     - Compiles the final review summary
   - **Implementation**: Implemented as a class with methods for coordination and summary compilation

2. **PR Retriever Agent** (`src/agents/pr_retriever.py`):
   - **Tool**: `GetPRInfoTool` (from `tools.github_tools`)
   - **Function**: Fetches PR metadata including title, URL, diff, files changed, and commit messages
   - **Features**: Includes PR URL parsing capability and robust error handling

3. **Code Understanding Agent** (`src/agents/code_understanding.py`):
   - **Tool**: `AnalyzeCodeTool` (from `tools.openai_tools`)
   - **Function**: Analyzes PR diff to generate a summary and identify potential risks
   - **Features**: Includes fallback mechanisms for when OpenAI API is unavailable

4. **PR Review Comment Agent** (`src/agents/pr_review_comment.py`):
   - **Tool**: `GenerateCommentTool` (from `tools.openai_tools`)
   - **Function**: Generates detailed review comments based on code analysis
   - **Features**: Handles various input scenarios with appropriate fallbacks

### Workflow Process

The hierarchical workflow follows these steps:

1. The Supervisor Agent initiates the process and parses the PR URL
2. The PR Retriever Agent fetches detailed PR information from GitHub
3. The Code Understanding Agent analyzes the code changes
4. The PR Review Comment Agent generates detailed review comments
5. The Supervisor Agent compiles all information into a final review summary

This hierarchical approach allows each agent to focus on its specialized task while the Supervisor Agent ensures proper coordination and data flow between agents.

### State

The workflow uses a `WorkflowState` (Pydantic model in `src/graph/graph.py`) to pass data between agents.

## Configuration

The application and Uvicorn server settings are configured via environment variables and the `WorkflowState` class in `src/graph/graph.py`.

Example environment variables in `.env`:
```
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token
OPENAI_API_KEY=your_openai_api_key
```

## Setup and Installation

1. **Clone the repository (if applicable).**

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Copy `.env.example` to `.env` and update with your credentials:
   ```bash
   cp .env.example .env
   # Edit .env and add your tokens
   ```

5. **Set up MCP Server:**
   Follow the MCP server setup instructions in the section below.

## MCP Server Setup

1. **Clone and build the MCP server:**
   ```bash
   git clone https://github.com/github/github-mcp-server.git
   cd github-mcp-server/cmd/github-mcp-server
   go build -o github-mcp-server
   ```

2. **Configure the MCP server path** in `src/tools/github_tools.py`:
   ```python
   mcp_path: str = Field(
       default="/path/to/github-mcp-server/cmd/github-mcp-server/github-mcp-server",
       description="Path to GitHub MCP server executable"
   )
   ```

3. **Set your GitHub token:**
   ```bash
   export GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token
   ```

## How to Run

### FastAPI Server

1. Ensure `PYTHONPATH` is set to include the project root:
   ```bash
   export PYTHONPATH=$(pwd)
   ```

2. Start the server:
   ```bash
   python3 src/comms/server/api.py
   ```
   The server will start on `http://0.0.0.0:8000` by default.

3. **Test the API:**
   ```bash
   curl -X POST "http://127.0.0.1:8000/review-pr/" \
        -H "Content-Type: application/json" \
        -d '{"pr_url": "https://github.com/owner/repo/pull/123"}'
   ```
   Or use the test script:
   ```bash
   python test_api.py --repo-url https://github.com/owner/repo --pr-number 123
   ```

 ## Environment Variables

-   `GITHUB_PERSONAL_ACCESS_TOKEN`: Your GitHub Personal Access Token.
-   `OPENAI_API_KEY`: Your OpenAI API Key.

Place these in a `.env` file in the project root.  