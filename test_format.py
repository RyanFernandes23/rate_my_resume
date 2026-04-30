
import json

def emit(stage, progress, message):
    return f"data: {json.dumps({'stage': stage, 'progress': progress, 'message': message})}\n\n"

def test_stream():
    # Test the format
    events = [
        emit("extract", 5, "Extracting text from file..."),
        emit("parse", 15, "Parsing resume structure..."),
        "data: {\"status\": \"complete\", \"result\": {}}\n\n"
    ]
    
    for event in events:
        print(f"Format: {repr(event)}")

if __name__ == "__main__":
    test_stream()
