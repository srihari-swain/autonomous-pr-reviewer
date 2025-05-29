# Automated PR Review System with LangGraph

## Author Information

- Developer: Srihari Swain
- Email: srihariswain2001@gmail.com
- GitHub: https://github.com/srihari-swain

## Project Timeline

- Development Time: Approximately 2 hours


## overview

This project implements an automated PR (Pull Request) review system using LangGraph, OpenAI, and the GitHub API. It can fetch PR details, analyze code changes, identify risks, and generate review comments.

## Project Structure

```
/home/srihari/Documents/GEnAi/
├── fynd/
│   └── src/
│       ├── agents/                   # Agent logic modules
│       │   ├── __init__.py
│       │   ├── pr_retriever_agent.py
│       │   ├── code_understanding_agent.py
│       │   ├── pr_review_comment_agent.py
│       │   └── supervisor_agent.py
│       ├── comms/
│       │   └── server/
│       │       └── rest_api/
│       │           └── api.py        # FastAPI application
│       ├── configs/
│       │   ├── config.json           # Application and server configuration
│       │   ├── config_loader.py      # Loader for config.json
│       │   └── schema.py             # Pydantic schemas / TypedDicts (like PRReviewState)
│       ├── graph/
│       │   └── graph.py              # LangGraph workflow definition
│       └── main.py                   # Main script to run the FastAPI/Uvicorn server


## Features

*   Fetches PR information (title, diff, files changed, commit messages) from GitHub.
*   Analyzes code changes using OpenAI models to generate summaries and identify risks.
*   Generates PR review comments based on the analysis.
*   Provides a final summary of the review.
*   Exposes functionality via a FastAPI endpoint.
*   Uses LangGraph for defining and managing the review workflow.
*   Configuration driven via `fynd/src/configs/config.json`.

## Agent Design

The system uses a hierarchical agent architecture managed by a LangGraph `StateGraph` (defined in `fynd/src/graph/graph.py`). The Supervisor Agent coordinates the workflow of specialized agents, each responsible for a specific task in the PR review process.

### Hierarchical Agent System

1. **Supervisor Agent (`fynd.src.agents.supervisor_agent`)**:
   - **Role**: Central coordinator of the entire agent system
   - **Functions**: 
     - Parses PR URLs to extract repository owner, name, and PR number
     - Coordinates the workflow between specialized agents
     - Compiles the final review summary
   - **Implementation**: Implemented as a class with methods for coordination and summary compilation

2. **PR Retriever Agent (`fynd.src.agents.pr_retriever_agent`)**:
   - **Tool**: `GetPRInfoTool` (from `tools.github_tools`)
   - **Function**: Fetches PR metadata including title, URL, diff, files changed, and commit messages
   - **Features**: Includes PR URL parsing capability and robust error handling

3. **Code Understanding Agent (`fynd.src.agents.code_understanding_agent`)**:
   - **Tool**: `AnalyzeCodeTool` (from `tools.openai_tools`)
   - **Function**: Analyzes PR diff to generate a summary and identify potential risks
   - **Features**: Includes fallback mechanisms for when OpenAI API is unavailable

4. **PR Review Comment Agent (`fynd.src.agents.pr_review_comment_agent`)**:
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

The workflow uses a `PRReviewState` (TypedDict in `src/configs/schema.py`) to pass data between agents.

## Configuration

The application and Uvicorn server settings are configured via `src/configs/config.json`. This file is loaded by `fynd/src/configs/config_loader.py`.

Example settings in `config.json` include:
- FastAPI app title, description, version, docs/redoc URLs.
- Uvicorn server host, port, reload status, worker count.
- CORS middleware settings.

Sensitive keys like API tokens are still expected to be set as environment variables (see `.env.example`).

## Setup and Installation

1.  **Clone the repository (if applicable).**

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    Ensure you have all necessary packages installed (e.g., `fastapi`, `uvicorn`, `langgraph`, `openai`, `python-dotenv`, `PyGithub`). You might need to create/update a `requirements.txt` in the root and run:
    ```bash
    pip install -r requirements.txt 
    ```

4.  **Set up environment variables:**
    Copy `.env.example` to `.env` in the project root  and fill in your `GITHUB_PERSONAL_ACCESS_TOKEN` and `OPENAI_API_KEY`.
    

5.  **Set PYTHONPATH:**
    To ensure Python can find your `src` modules, export `PYTHONPATH` from the project root directory:
    ```bash
    export PYTHONPATH=$(pwd)
    ```

## How to Run

### FastAPI Server

1.  Ensure `PYTHONPATH` is set as described in Setup.

2.  Run the main application script (which starts Uvicorn based on `config.json`):
    ```bash
    python3 src/main.py
    ```
    The server will typically start on `http://0.0.0.0:8000` (or as configured in `config.json`).

4.  **Test the API:**
    
    ```bash
    curl -X POST "http://127.0.0.1:8000/review-pr/" \
         -H "Content-Type: application/json" \
         -d '{"pr_url": "https://github.com/owner/repo/pull/123"}'
    ```
    or use test_api.py file 

## Environment Variables

-   `GITHUB_PERSONAL_ACCESS_TOKEN`: Your GitHub Personal Access Token.
-   `OPENAI_API_KEY`: Your OpenAI API Key.

Place these in a `.env` file in the project root.
