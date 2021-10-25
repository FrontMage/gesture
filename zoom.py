from typing import Deque
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
import threading
import cv2
from cvzone.HandTrackingModule import HandDetector
from collections import deque
import asyncio
import json

GESTURE_CONTINIUS_TRHESHOLD = 10
gesture_msgs = deque(maxlen=30)
frames = deque(maxlen=30)
gesture_start = deque(maxlen=GESTURE_CONTINIUS_TRHESHOLD)

# Define the gstreamer sink
# gst_str_rtp = 'appsrc ! videoconvert ! x264enc speed-preset=ultrafast tune=zerolatency byte-stream=true threads=2 key-int-max=15 intra-refresh=true ! h264parse ! rtph264pay ! capssetter caps="application/x-rtp,profile-level-id=(string)42e01f" ! udpsink host=127.0.0.1 port=8004'
# Cam properties
fps = 30.0
frame_width = 1280
frame_height = 720


def is_deque_all_true(d: Deque):
    flag = True
    for el in d:
        flag = flag and el
    return flag


def is_deque_all_false(d: Deque):
    flag = True
    for el in d:
        flag = flag and not el
    return flag


def rec_gesture():
    cap = cv2.VideoCapture(1)
    cap.set(3, frame_width)
    cap.set(4, frame_height)

    detector = HandDetector(detectionCon=0.7)
    scale = 0
    # Create videowriter as a SHM sink
    # out = cv2.VideoWriter(gst_str_rtp, 0, fps, (frame_width, frame_height), True)
    # 在gesture stop触发之前，下一个gesture start不会触发
    is_waiting_gesture_stop = False
    # 在gesture start触发之前，下一个gesture stop不会触发
    is_waiting_gesture_start = False
    # 上次识别有几只手
    previous_hand_count = 0
    while True:
        success, img = cap.read()
        hands, img = detector.findHands(img)

        if len(hands) == 2:
            gesture_start.append(True)
            if detector.fingersUp(hands[0]) == [1, 1, 0, 0, 0] and detector.fingersUp(
                hands[1]
            ) == [1, 1, 0, 0, 0]:
                length, info, img = detector.findDistance(
                    hands[0]["center"], hands[1]["center"], img
                )

                scale = length
                gesture_msgs.append(
                    json.dumps({"gesture_type": "zoom", "scale": scale})
                )
        elif len(hands) == 1:
            if previous_hand_count == 1:
                gesture_start.append(True)
                gesture_msgs.append(
                    json.dumps(
                        {"gesture_type": "swipe", "scale": hands[0]["center"][0]}
                    )
                )
        else:
            gesture_start.append(False)

        frames.append(img)
        if (
            is_deque_all_true(gesture_start)
            and len(gesture_start) == GESTURE_CONTINIUS_TRHESHOLD
            and not is_waiting_gesture_stop
            and len(hands) > 0
        ):
            gesture_type = "invalide_gesture"
            if len(hands) == 2:
                gesture_type = "zoom_start"
            if len(hands) == 1:
                gesture_type = "swipe start"
            gesture_msgs.append(json.dumps({"gesture_type": gesture_type, "scale": 0}))
            gesture_start.clear()
            is_waiting_gesture_stop = True
            is_waiting_gesture_start = False
            print(gesture_type)
        elif (
            is_deque_all_false(gesture_start)
            and len(gesture_start) == GESTURE_CONTINIUS_TRHESHOLD
            and not is_waiting_gesture_start
        ):
            gesture_msgs.append(
                json.dumps({"gesture_type": "gesture_stop", "scale": 0})
            )
            gesture_start.clear()
            is_waiting_gesture_stop = False
            is_waiting_gesture_start = True

        previous_hand_count = len(hands)

        scale_percent = 30  # percent of original size
        width = int(img.shape[1] * scale_percent / 100)
        height = int(img.shape[0] * scale_percent / 100)
        dim = (width, height)
        cv2.imshow("Image", cv2.resize(img, dim, interpolation=cv2.INTER_AREA))
        # out.write(img)
        if cv2.waitKey(33) == ord("q"):
            break


threading.Thread(target=rec_gesture).start()
# rec_gesture()

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
            gesture_msg = gesture_msgs.pop()
            try:
                await websocket.send_text(gesture_msg)
            except WebSocketDisconnect:
                break
        except IndexError:
            await asyncio.sleep(1)


# def generate():
#     global outputFrame, lock
#     # loop over frames from the output stream
#     while True:
#         try:
#             frame = frames.popleft()
#         except IndexError:
#             continue
#         (flag, encodedImage) = cv2.imencode(".jpg", frame)
#         if not flag:
#             continue
#         yield (
#             b"--frame\r\n"
#             b"Content-Type: image/jpeg\r\n\r\n" + bytearray(encodedImage) + b"\r\n"
#         )


# @app.get("/video_feed")
# async def video_feed():
#     return StreamingResponse(
#         generate(), media_type="multipart/x-mixed-replace;boundary=frame"
#     )
