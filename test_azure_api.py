#!/usr/bin/env python3
"""Test script to verify Azure OpenAI Claude API configuration"""

import os
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME", "claude-sonnet-4-5-2")

print("=" * 60)
print("Azure API Configuration Test")
print("=" * 60)
print(f"AZURE_ENDPOINT: {AZURE_ENDPOINT}")
print(f"DEPLOYMENT_NAME: {DEPLOYMENT_NAME}")
print(f"AZURE_API_KEY: {AZURE_API_KEY[:10]}...{AZURE_API_KEY[-10:] if AZURE_API_KEY else 'NOT SET'}")
print("=" * 60)

if not AZURE_API_KEY:
    print("ERROR: AZURE_API_KEY is not set!")
    exit(1)

if not AZURE_ENDPOINT:
    print("ERROR: AZURE_ENDPOINT is not set!")
    exit(1)

# Ensure endpoint format is correct for Claude in Azure AI Foundry
AZURE_ENDPOINT = AZURE_ENDPOINT.rstrip('/')
if not AZURE_ENDPOINT.endswith('/anthropic'):
    AZURE_ENDPOINT += '/anthropic'

# Test API call
print("\nTesting API connection...")
print(f"Making request to: {AZURE_ENDPOINT}/v1/messages")

headers = {
    "Content-Type": "application/json",
    "x-api-key": AZURE_API_KEY,
    "anthropic-version": "2023-06-01"
}

payload = {
    "model": DEPLOYMENT_NAME,
    "max_tokens": 100,
    "messages": [
        {
            "role": "user",
            "content": "Say 'Hello, API test successful!' and nothing else."
        }
    ]
}

try:
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{AZURE_ENDPOINT}/v1/messages",
            headers=headers,
            json=payload
        )

        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 401:
            print("\n[X] AUTHENTICATION FAILED (401)")
            print("This means your AZURE_API_KEY is invalid or expired.")
            print("Please verify your API key in the .env file.")
            print(f"\nError response: {response.text}")

        response.raise_for_status()

        response_data = response.json()
        print("\n[OK] SUCCESS!")
        print(f"Response: {response_data}")

        if "content" in response_data:
            print(f"\nClaude's response: {response_data['content'][0]['text']}")

except httpx.HTTPStatusError as e:
    print(f"\n[X] HTTP ERROR: {e}")
    print(f"Response body: {e.response.text}")
except Exception as e:
    print(f"\n[X] ERROR: {e}")

print("\n" + "=" * 60)
