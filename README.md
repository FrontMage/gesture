# Requirements
```bash
pip install opencv-python fastapi websockets uvicorn mediapipe cvzone
```

# Demo
```bash
uvicorn zoom:app --host 0.0.0.0 --log-level debug
```

websocket
```bash
localhost:8000/ws
```

video feed
```bash
http://localhost:8000/video_feed
```

# Notice

To shutdown program, press ctrl+c multiple times, because threading issue.

