from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        await websocket.send_json({
            "event": "connected",
            "task_id": task_id,
            "message": "WebSocket connection established",
        })
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "event": "echo",
                "task_id": task_id,
                "data": data,
            })
    except WebSocketDisconnect:
        pass
