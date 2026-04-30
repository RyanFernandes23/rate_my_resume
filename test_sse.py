"""Test script for SSE endpoint."""
import requests
import json

def test_sse_stream():
    url = "http://127.0.0.1:8000/api/analyze/stream"
    test_file = r"C:\Users\Hp\OneDrive\Desktop\rate_my_resume\backend\tests\Ryanfernandes (4).pdf"
    
    with open(test_file, "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        data = {"jd": "software engineer"}  # optional
        
        print("Connecting to SSE stream...")
        print("-" * 50)
        
        response = requests.post(url, files=files, data=data, stream=True)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error: {response.text}")
            return
        
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        stage = data.get("stage", "")
                        progress = data.get("progress", 0)
                        message = data.get("message", "")
                        status = data.get("status", "")
                        
                        if status == "complete":
                            print(f"\n{'='*50}")
                            print("COMPLETE!")
                            print(f"Analysis ID: {data.get('analysis_id')}")
                            print(f"Credits remaining: {data.get('credits_remaining')}")
                            break
                        elif stage == "error" or status == "error":
                            print(f"\nERROR: {message}")
                            break
                        elif stage == "credits_error":
                            print(f"\nCREDITS ERROR: {message}")
                            break
                        else:
                            print(f"[{progress:3d}%] {stage:20s} - {message}")
                    except json.JSONDecodeError as e:
                        print(f"JSON parse error: {e}, line: {line}")
            else:
                print(f"Raw: {line}")

if __name__ == "__main__":
    test_sse_stream()