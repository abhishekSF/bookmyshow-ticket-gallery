"""
Gmail OAuth setup for BookMyShow Ticket Gallery.
Run this script once to set up credentials.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.auth import AuthLoader
import json

# Redirect stdout to capture print statements
class CapturingOutput:
    def __init__(self):
        self.text = ''
    
    def write(self, text):
        self.text += text
    
    def flush(self):
        pass
    
    def getvalue(self):
        return self.text


# Scopes for Gmail API - readonly for personal use
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Path to save credentials and tokens
OUTPUT_DIR = "./tokens"


def setup_gmail_oauth():
    """
    Set up Gmail OAuth credentials interactively.
    """
    print("\n" + "="*60)
    print("🔑 Gmail OAuth Setup for BookMyShow Ticket Gallery")
    print("="*60)
    print("\nThis script will:")
    print("1. Download Gmail OAuth credentials")
    print("2. Open your browser for consent")
    print("3. Save credentials and access token locally")
    print("\nNote: You need a Google Cloud project with Gmail API enabled.\n")
    
    input("Press Enter to continue...")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("\nStep 1: Enter Google Cloud Project ID (from console.cloud.google.com)")
    project_id = input("Project ID: ").strip()
    
    if not project_id:
        print("✗ Project ID is required. Please try again.")
        sys.exit(1)
    
    print("\nStep 2: Enter OAuth Client ID and Secret (from Google Cloud Console)")
    print("\n   Go to: https://console.cloud.google.com/apis/credentials")
    print("   Select your project")
    print("   Find 'OAuth client' and click 'Create OAuth client'")
    print("   Choose 'Desktop app' as the application type")
    
    client_id = input("\nClient ID: ").strip()
    client_secret = input("Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("✗ Client ID and Secret are required. Please try again.")
        sys.exit(1)
    
    # Create credentials file path
    credentials_file = Path(OUTPUT_DIR) / "credentials.json"
    token_file = Path(OUTPUT_DIR) / "token.json"
    
    # Save client credentials
    creds_data = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": "dummy",  # Will be generated
        "private_key": "dummy",
        "client_email": f"{project_id}@accounts.google.com",
        "client_id": client_id,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v3/certs",
        "client_x509_cert_url": "https://www.googleapis.com/oauth2/v3/certs",
    }
    
    # OAuth flow for service account (without key)
    print("\n" + "="*60)
    print("🚦 Initializing OAuth Flow...")
    print("="*60)
    
    try:
        flow = Flow.from_client_config(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            },
            scopes=SCOPES,
        )
        
        # Capture browser output
        output = CapturingOutput()
        original_stdout = sys.stdout
        sys.stdout = output
        
        try:
            flow.run_to_complete()
        finally:
            sys.stdout = original_stdout
        
        sys.stdout = original_stdout
        sys.stderr = output
        print(output.getvalue())
        
        print(f"🎉 Browser opened for consent. Please grant permissions when prompted.")
        print("\nYou will be redirected back after consenting.")
        print("Press Enter when the browser returns...")
        
        input("Press Enter when you've been redirected back...")
        
    except Exception as e:
        print(f"\n✗ Error during OAuth flow: {e}")
        sys.exit(1)
    
    # Save credentials and token
    print("\n" + "="*60)
    print("💾 Saving credentials...")
    print("="*60)
    
    # Save client credentials
    with open(credentials_file, 'w') as f:
        json.dump(creds_data, f, indent=2)
    print(f"✓ Saved client credentials to {credentials_file}")
    
    # Save token
    token_data = {
        "access_token": flow.credentials.token,
        "refresh_token": flow.credentials.refresh_token,
        "token_type": flow.credentials.token_type,
        "expires_in": 3600,
        "scope": " ".join(SCOPES),
        "locale": "en",
    }
    
    with open(token_file, 'w') as f:
        json.dump(token_data, f, indent=2)
    print(f"✓ Saved access token to {token_file}")
    
    print("\n" + "="*60)
    print("✅ Gmail OAuth setup complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Run the main scraper: python main_scraper.py")
    print("2. The scraper will use the credentials from tokens/token.json")
    print("3. If the token expires, run this script again to refresh it")
    print("\n" + "="*60)


if __name__ == "__main__":
    try:
        setup_gmail_oauth()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted. Your credentials have been saved.")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()