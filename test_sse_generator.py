
import sys
import os

# Add the project root to sys.path so we can import app
sys.path.append(os.path.abspath("backend"))

import json
from app.main import stream_analyze_generator

# Simulate file content
filename = "test.txt"
content = b"fake content"

# Create a mock user_id
user_id = None

async def test_stream():
    print("Testing stream generator...")
    async for event in stream_analyze_generator(content, filename, None, user_id):
        print(f"Received: {event}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_stream())
