# Requirements
```bash
pip install opencv-python fastapi websockets uvicorn mediapipe cvzone
```

# Demo
```bash
uvicorn zoom:app --host 0.0.0.0 --log-level debug
```

# Notice

To shutdown program, press ctrl+c multiple times, because threading issue.

