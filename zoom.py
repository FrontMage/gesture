from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
import threading
import cv2
from cvzone.HandTrackingModule import HandDetector
from collections import deque
import asyncio
import json

zoom_distance = deque(maxlen=30)
frames = deque(maxlen=30)


def rec_gesture():
    cap = cv2.VideoCapture(1)
    cap.set(3, 640)
    cap.set(4, 360)

    detector = HandDetector(detectionCon=0.7)
    startDist = None
    scale = 0
    while True:
        success, img = cap.read()
        hands, img = detector.findHands(img)

        if len(hands) == 2:
            if detector.fingersUp(hands[0]) == [1, 1, 0, 0, 0] and detector.fingersUp(
                hands[1]
            ) == [1, 1, 0, 0, 0]:
                if startDist is None:
                    length, info, img = detector.findDistance(
                        hands[0]["center"], hands[1]["center"], img
                    )

                    startDist = length

                length, info, img = detector.findDistance(
                    hands[0]["center"], hands[1]["center"], img
                )

                scale = int((length - startDist) // 2)
                zoom_distance.append(scale)
        else:
            startDist = None

        frames.append(img)


threading.Thread(target=rec_gesture).start()

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # data = await websocket.receive_text()
        try:
            data = zoom_distance.pop()
            try:
                await websocket.send_text(
                    json.dumps({"gesture_type": "zoom", "scale": data})
                )
            except WebSocketDisconnect:
                break
        except IndexError:
            await asyncio.sleep(1)


def generate():
    global outputFrame, lock
    # loop over frames from the output stream
    while True:
        try:
            frame = frames.popleft()
        except IndexError:
            continue
        (flag, encodedImage) = cv2.imencode(".jpg", frame)
        if not flag:
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + bytearray(encodedImage) + b"\r\n"
        )


@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(
        generate(), media_type="multipart/x-mixed-replace;boundary=frame"
    )
