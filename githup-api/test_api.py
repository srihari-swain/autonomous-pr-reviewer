import requests
import json

API_URL = "http://127.0.0.1:8000/review-pr/"


TEST_PR_URL = "https://github.com/psf/black/pull/4663" 

def test_pr_review_api(pr_url: str):
    """Sends a request to the PR review API and prints the response."""
    payload = {"pr_url": pr_url}
    
    print(f"Sending request to API: {API_URL}")
    print(f"Payload: {json.dumps(payload)}\n")
    
    try:
        response = requests.post(API_URL, json=payload, timeout=300) 
        
        print(f"Response Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            print("API Response (JSON):")
            try:
                response_data = response.json()
                print(json.dumps(response_data, indent=2))
            except json.JSONDecodeError:
                print("Error: Could not decode JSON response.")
                print(f"Raw response content:\n{response.text}")
        else:
            print("Error from API:")
            try:
                error_data = response.json() 
                print(json.dumps(error_data, indent=2))
            except json.JSONDecodeError:
                print(f"Raw error response content:\n{response.text}")
                
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: Failed to connect to the API at {API_URL}.")
        print("Please ensure the FastAPI server is running (`uvicorn api:fast_api_app --reload`).")
        print(f"Details: {e}")
    except requests.exceptions.Timeout:
        print(f"Request timed out after 300 seconds for PR: {pr_url}")
    except requests.exceptions.RequestException as e:
        print(f"An unexpected error occurred with the request: {e}")

if __name__ == "__main__":
    print("--- Starting API Test ---")
   
    test_pr_review_api(TEST_PR_URL)
    print("\n--- API Test Finished ---")


