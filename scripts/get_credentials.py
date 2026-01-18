import json
import os

CREDENTIALS_FILE = "hittrax-automator.credentials.json"

def get_credentials():
    """Loads credentials from the local JSON file."""
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: {CREDENTIALS_FILE} not found.")
        print("Please create this file with your 'project_id' and 'location'.")
        return None
    
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            creds = json.load(f)
            return creds
    except json.JSONDecodeError:
        print(f"Error: Failed to parse {CREDENTIALS_FILE}.")
        return None
