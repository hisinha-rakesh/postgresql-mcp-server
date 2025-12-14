#!/usr/bin/env python3
"""Try different deployment name variations"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_API_KEY")
BASE_ENDPOINT = "https://ai-premmalothu0362ai608205493981.services.ai.azure.com"

# Common deployment name variations for Claude
deployment_variations = [
    "claude-sonnet-4-5-2",
    "claude-sonnet-4-5",
    "claude-sonnet-45-2",
    "claude-sonnet",
    "claude-3-5-sonnet",
    "claude-3-sonnet",
    "claude",
    "claude-sonnet-20241022",
    "claude-3-5-sonnet-20241022",
]

print("=" * 70)
print("Testing Different Deployment Names")
print("=" * 70)
print(f"Endpoint: {BASE_ENDPOINT}")
print(f"API Key: {AZURE_API_KEY[:10]}...{AZURE_API_KEY[-10:]}")
print("=" * 70)

for deployment in deployment_variations:
    url = f"{BASE_ENDPOINT}/openai/deployments/{deployment}/chat/completions?api-version=2024-02-15-preview"

    print(f"\nTrying: {deployment}")

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "api-key": AZURE_API_KEY
                },
                json={
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                }
            )

            if response.status_code == 200:
                print(f"  [OK] SUCCESS! Use this deployment name: {deployment}")
                print(f"  Response: {response.json()}")
                break
            elif response.status_code == 400:
                error_data = response.json()
                if "unknown_model" in str(error_data).lower():
                    print(f"  [X] Model not found")
                else:
                    print(f"  [?] Other error: {error_data}")
            elif response.status_code == 401:
                print(f"  [X] Auth failed - API key issue")
            elif response.status_code == 404:
                print(f"  [X] Deployment not found")
            else:
                print(f"  [?] Status {response.status_code}: {response.text[:100]}")

    except Exception as e:
        print(f"  [X] Error: {str(e)[:100]}")

print("\n" + "=" * 70)
print("\nIf none worked, please check Azure Portal:")
print("1. Go to your Azure AI Services resource")
print("2. Navigate to 'Model deployments' or 'Deployments'")
print("3. Copy the EXACT deployment name shown there")
print("4. Update your .env file with that deployment name")
print("=" * 70)
