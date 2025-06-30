import os
import requests
import csv
from datetime import datetime, timedelta

# --- Configuration ---

# Best practice: Load your GitHub Personal Access Token from an environment variable.
GITHUB_TOKEN = os.getenv('GITHUB_PAT')
if not GITHUB_TOKEN:
    raise ValueError("GitHub token not found. Please set the GITHUB_TOKEN environment variable.")

# GitHub API endpoints
SEARCH_API_URL = "https://api.github.com/search/repositories"
USERS_API_URL = "https://api.github.com/users"

# Keywords for repository search
KEYWORDS = [
    "Retrieval-Augmented Generation",
    "RAG pipeline",
    "LLM search",
    "semantic search",
    "vector search accuracy"
]

# Cache to store emails we've already found to avoid redundant API calls
email_cache = {}

# --- Script Logic ---

def get_past_date(days_ago):
    """Calculates the date from a specific number of days ago in YYYY-MM-DD format."""
    past_date = datetime.now() - timedelta(days=days_ago)
    return past_date.strftime("%Y-%m-%d")

def make_api_request(url):
    """A helper function to make authenticated GET requests to the GitHub API."""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request to {url}: {e}")
        return None

def get_user_email(username):
    """
    Attempts to find a user's public email by checking their recent public push events.
    Uses a cache to avoid re-fetching emails for the same user.
    """
    if username in email_cache:
        return email_cache[username]

    print(f"    -> Attempting to find email for user: {username}...")
    events_url = f"{USERS_API_URL}/{username}/events/public"
    events = make_api_request(events_url)

    if not events:
        email_cache[username] = "Not found (no public events)"
        return email_cache[username]

    for event in events:
        if event['type'] == 'PushEvent' and 'commits' in event['payload']:
            for commit in event['payload']['commits']:
                email = commit['author']['email']
                # Avoid returning the default GitHub no-reply email if possible,
                # but return it if it's the only one found.
                if "users.noreply.github.com" not in email:
                    email_cache[username] = email
                    return email
    
    # If no non-private email was found after checking all events
    email_cache[username] = "Not found"
    return email_cache[username]

def main():
    """
    Main function to run discovery, find emails, and write to a CSV file.
    """
    print("--- Starting Weekly GitHub Discovery & Email Retrieval ---")
    
    one_week_ago_date = get_past_date(7)
    
    # Create a unique CSV filename with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"github_discovery_{timestamp}.csv"
    
    # Open the CSV file for writing
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
        # Define the headers for the CSV file
        fieldnames = [
            'Keyword', 'Repo Name', 'Owner', 'Owner Type', 'Stars', 
            'Repo URL', 'Description', 'Owner Email'
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        print(f"Results will be saved to {csv_filename}")

        # Loop through each keyword to perform a search
        for keyword in KEYWORDS:
            # Add `stars:>=1` to the query to filter results on the server side
            query = f'"{keyword}" in:name,description,readme created:>{one_week_ago_date} stars:>=1'
            
            print(f"\nSearching for repositories with keyword: '{keyword}'...")
            
            search_url = f"{SEARCH_API_URL}?q={query}&sort=updated&order=desc"
            results = make_api_request(search_url)
            
            if not results or not results.get('items'):
                print("No repositories found for this keyword.")
                continue

            print(f"Found {results['total_count']} repositories. Processing...")
            
            # Process each repository found in the search results
            for repo in results['items']:
                owner_login = repo['owner']['login']
                owner_type = repo['owner']['type']
                retrieved_email = "N/A (Organization)"

                # Only try to get email if the owner is a 'User'
                if owner_type == 'User':
                    retrieved_email = get_user_email(owner_login)

                # Prepare the data row for the CSV
                repo_data = {
                    'Keyword': keyword,
                    'Repo Name': repo['full_name'],
                    'Owner': owner_login,
                    'Owner Type': owner_type,
                    'Stars': repo['stargazers_count'],
                    'Repo URL': repo['html_url'],
                    'Description': repo.get('description', 'N/A'),
                    'Owner Email': retrieved_email
                }
                
                # Write the row to the CSV file
                writer.writerow(repo_data)

    print(f"\n--- Discovery complete. All data saved to {csv_filename} ---")

if __name__ == "__main__":
    main()