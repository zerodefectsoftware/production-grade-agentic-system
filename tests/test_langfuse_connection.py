"""Test Langfuse connection and trace writing with your credentials."""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langchain_openai import ChatOpenAI
from src.config.settings import settings

print("=" * 70)
print("LANGFUSE CONNECTION & TRACE TEST")
print("=" * 70)

# Step 1: Check credentials are loaded
print("\n[1] Checking Credentials...")
if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
    print("❌ FAILED: Credentials not set in .env.development")
    exit(1)

print(f"✓ Public Key: {settings.LANGFUSE_PUBLIC_KEY[:20]}...")
print(f"✓ Secret Key: {settings.LANGFUSE_SECRET_KEY[:20]}...")
print(f"✓ Host: {settings.LANGFUSE_HOST}")

# Step 2: Initialize Langfuse client
print("\n[2] Initializing Langfuse Client...")
try:
    client = Langfuse(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
    )
    print("✓ Client initialized")
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit(1)

# Step 3: Test with CallbackHandler (as used in your app)
print("\n[3] Testing CallbackHandler (as used in your app)...")
try:
    handler = CallbackHandler()
    print("✓ CallbackHandler initialized")
    print(f"  Client enabled: {handler.client.tracing_enabled if hasattr(handler.client, 'tracing_enabled') else 'Unknown'}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit(1)

# Step 4: Make a real LLM call with tracing
print("\n[4] Making LLM call with Langfuse tracing...")
if not settings.OPENAI_API_KEY:
    print("⚠ SKIPPED: OPENAI_API_KEY not set")
else:
    try:
        # Create a new handler for this test
        test_handler = CallbackHandler()

        # Create LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )

        # Make a call with the handler
        print("  Calling LLM with trace...")
        result = llm.invoke(
            "Say 'Langfuse test successful' and nothing else",
            config={"callbacks": [test_handler]}
        )

        print(f"✓ LLM Response: {result.content}")

        # Flush to send trace immediately
        print("  Flushing trace to Langfuse...")
        test_handler.client.flush()

        # Wait a moment for the trace to be sent
        time.sleep(2)

        print("✓ Trace sent to Langfuse")

        if test_handler.last_trace_id:
            print(f"  Trace ID: {test_handler.last_trace_id}")
            print(f"  View at: {settings.LANGFUSE_HOST}/trace/{test_handler.last_trace_id}")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

# Step 5: Check for authentication errors
print("\n[5] Checking for authentication errors...")
print("  Waiting 3 seconds to see if any errors occur...")
time.sleep(3)

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print("\nWhat to do next:")
print("1. Go to your Langfuse dashboard:", settings.LANGFUSE_HOST)
print("2. Navigate to: Traces")
print("3. Look for a trace with input: 'Say 'Langfuse test successful'...")
print("\nIf you DON'T see traces:")
print("  → Your credentials may be invalid/expired")
print("  → Go to Settings → API Keys in Langfuse dashboard")
print("  → Create new keys and update .env.development")
print("\nIf you DO see traces:")
print("  → Your integration is working!")
print("  → Traces should appear when you use your chat app")
print("=" * 70)
