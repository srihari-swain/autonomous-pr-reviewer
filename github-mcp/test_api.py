"""
Simple test script for GitHub PR Review API
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8000/review-pr"

# Test repository URL - change this to your target repository
REPO_URL = "https://github.com/psf/black"

# Optional PR number - set to None to use latest PR
PR_NUMBER = None

# Create the request payload
payload = {
    "repo_url": REPO_URL
}

if PR_NUMBER:
    payload["pr_number"] = PR_NUMBER

# Print what we're about to do
print(f"Sending request to {API_URL}")
print(f"Repository: {REPO_URL}")
if PR_NUMBER:
    print(f"PR Number: {PR_NUMBER}")
else:
    print("PR Number: Latest")

try:
    # Make the API request
    response = requests.post(API_URL, json=payload)
    
    # Print status code
    print(f"\nResponse Status: {response.status_code}")
    
    # Check if request was successful
    if response.status_code == 200:
        # Get the response data
        result = response.json()
        
        # Print a summary of the response
        print("\n=== PR Review Summary ===")
        print(f"Repository: {result['repo_owner']}/{result['repo_name']}")
        print(f"PR #{result['pr_number']}: {result['pr_title'] or 'No title'}")
        print(f"Author: {result['pr_author'] or 'Unknown'}")
        print(f"\nFinal Review:\n{result['final_review']}")
    else:
        # Print error information
        print("\nError Response:")
        print(response.text)
except Exception as e:
    print(f"\nError: {str(e)}")
    print("\nMake sure the API server is running with: uvicorn api:app --reload")
