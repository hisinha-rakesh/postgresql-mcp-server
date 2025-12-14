#!/usr/bin/env python3
"""Test different Azure endpoint formats to find the correct one"""

import os
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_API_KEY")
BASE_ENDPOINT = os.getenv("AZURE_ENDPOINT", "https://ai-premmalothu0362ai608205493981.cognitiveservices.azure.com")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME", "claude-sonnet-4-5-2")

# Remove trailing slash and /anthropic/ if present
BASE_ENDPOINT = BASE_ENDPOINT.rstrip('/')
if BASE_ENDPOINT.endswith('/anthropic'):
    BASE_ENDPOINT = BASE_ENDPOINT[:-len('/anthropic')]

print("=" * 70)
print("Testing Different Azure Endpoint Formats")
print("=" * 70)
print(f"Base Endpoint: {BASE_ENDPOINT}")
print(f"Deployment: {DEPLOYMENT_NAME}")
print(f"API Key: {AZURE_API_KEY[:10]}...{AZURE_API_KEY[-10:] if AZURE_API_KEY else 'NOT SET'}")
print("=" * 70)

# Different endpoint formats to try
endpoint_formats = [
    # Standard Azure OpenAI endpoint
    {
        "name": "Standard Azure OpenAI",
        "url": f"{BASE_ENDPOINT}/openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version=2024-02-15-preview",
        "headers": {
            "Content-Type": "application/json",
            "api-key": AZURE_API_KEY
        },
        "payload": {
            "messages": [{"role": "user", "content": "Say 'Test successful'"}],
            "max_tokens": 50
        }
    },
    # Anthropic-style endpoint
    {
        "name": "Anthropic API Format",
        "url": f"{BASE_ENDPOINT}/anthropic/v1/messages",
        "headers": {
            "Content-Type": "application/json",
            "api-key": AZURE_API_KEY,
            "anthropic-version": "2023-06-01"
        },
        "payload": {
            "model": DEPLOYMENT_NAME,
            "max_tokens": 50,
            "messages": [{"role": "user", "content": "Say 'Test successful'"}]
        }
    },
    # Direct v1/messages endpoint
    {
        "name": "Direct Messages API",
        "url": f"{BASE_ENDPOINT}/v1/messages",
        "headers": {
            "Content-Type": "application/json",
            "api-key": AZURE_API_KEY,
            "anthropic-version": "2023-06-01"
        },
        "payload": {
            "model": DEPLOYMENT_NAME,
            "max_tokens": 50,
            "messages": [{"role": "user", "content": "Say 'Test successful'"}]
        }
    },
    # OpenAI compatibility endpoint for Anthropic
    {
        "name": "OpenAI Compat with Anthropic",
        "url": f"{BASE_ENDPOINT}/openai/deployments/{DEPLOYMENT_NAME}/extensions/chat/completions?api-version=2023-12-01-preview",
        "headers": {
            "Content-Type": "application/json",
            "api-key": AZURE_API_KEY
        },
        "payload": {
            "messages": [{"role": "user", "content": "Say 'Test successful'"}],
            "max_tokens": 50
        }
    }
]

successful_endpoint = None

for i, endpoint_config in enumerate(endpoint_formats, 1):
    print(f"\n[{i}/{len(endpoint_formats)}] Testing: {endpoint_config['name']}")
    print(f"URL: {endpoint_config['url']}")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                endpoint_config['url'],
                headers=endpoint_config['headers'],
                json=endpoint_config['payload']
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                print("[OK] SUCCESS! This endpoint works!")
                print(f"Response: {response.json()}")
                successful_endpoint = endpoint_config
                break
            else:
                print(f"[X] Failed - {response.status_code}")
                print(f"Error: {response.text[:200]}")

    except Exception as e:
        print(f"[X] Exception: {str(e)[:200]}")

print("\n" + "=" * 70)

if successful_endpoint:
    print("[OK] FOUND WORKING ENDPOINT!")
    print("=" * 70)
    print(f"Endpoint Name: {successful_endpoint['name']}")
    print(f"URL: {successful_endpoint['url']}")
    print("\nUpdate your .env file with:")

    if "anthropic" in successful_endpoint['url']:
        base_url = successful_endpoint['url'].split('/v1/messages')[0] + '/'
        print(f"AZURE_ENDPOINT={base_url}")
    else:
        print(f"# Use this URL format in your code:")
        print(f"# {successful_endpoint['url']}")
else:
    print("[X] NO WORKING ENDPOINT FOUND")
    print("=" * 70)
    print("\nPlease verify:")
    print("1. Your API key is correct and active")
    print("2. Your Azure resource endpoint URL")
    print("3. Your deployment name matches what's in Azure Portal")
    print("4. The Claude model is properly deployed in your Azure resource")

print("=" * 70)
