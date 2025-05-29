#!/bin/bash
# Script to run GitHub MCP Server in Docker

# Load the GitHub token from the .env file
source /home/srihari/Documents/GEnAi/fynd/.env

# Check if the token is available
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN not found in .env file"
  exit 1
fi

# Run the docker container
docker run -d -p 3000:3000 --name github-mcp-server \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_TOKEN \
  -e GITHUB_TOOLSETS="repos,issues,pull_requests,code_security" \
  ghcr.io/github/github-mcp-server:latest

echo "GitHub MCP Server started on port 3000"
