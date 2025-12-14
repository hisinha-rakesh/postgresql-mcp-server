#!/usr/bin/env python3
"""Test Azure AI Inference SDK with Claude"""

import os
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage
from azure.core.credentials import AzureKeyCredential

# Load environment variables
load_dotenv()

AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT", "https://ai-premmalothu0362ai608205493981.cognitiveservices.azure.com")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME", "claude-sonnet-4-5-2")

# Remove /anthropic/ suffix if present
AZURE_ENDPOINT = AZURE_ENDPOINT.rstrip('/')
if AZURE_ENDPOINT.endswith('/anthropic'):
    AZURE_ENDPOINT = AZURE_ENDPOINT[:-len('/anthropic')]

print("=" * 70)
print("Azure AI Inference SDK Test")
print("=" * 70)
print(f"Endpoint: {AZURE_ENDPOINT}")
print(f"Deployment: {DEPLOYMENT_NAME}")
print(f"API Key: {AZURE_API_KEY[:10]}...{AZURE_API_KEY[-10:] if AZURE_API_KEY else 'NOT SET'}")
print("=" * 70)

if not AZURE_API_KEY:
    print("\n[X] ERROR: AZURE_API_KEY is not set!")
    exit(1)

try:
    # Initialize the client
    print("\n[1] Initializing ChatCompletionsClient...")
    client = ChatCompletionsClient(
        endpoint=AZURE_ENDPOINT,
        credential=AzureKeyCredential(AZURE_API_KEY)
    )
    print("[OK] Client initialized successfully")

    # Make a test request
    print(f"\n[2] Sending test message to model: {DEPLOYMENT_NAME}...")
    response = client.complete(
        model=DEPLOYMENT_NAME,
        messages=[
            UserMessage(content="Say 'Hello! API test successful.' and nothing else.")
        ],
        max_tokens=50,
        temperature=0.0
    )

    print("[OK] Response received!")
    print("\n" + "=" * 70)
    print("SUCCESS!")
    print("=" * 70)
    print(f"\nClaude's response: {response.choices[0].message.content}")
    print(f"\nModel used: {response.model}")
    print(f"Tokens used - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}")
    print("\n" + "=" * 70)
    print("\n[OK] Your Azure AI configuration is working correctly!")
    print("You can now start your MCP server.")
    print("=" * 70)

except Exception as e:
    print(f"\n[X] ERROR: {e}")
    print("\nPlease check:")
    print("1. Your AZURE_API_KEY is correct")
    print("2. Your AZURE_ENDPOINT is correct")
    print("3. Your DEPLOYMENT_NAME matches what's in Azure Portal")
    print("4. The deployment is active and running")
    print("=" * 70)
    exit(1)
