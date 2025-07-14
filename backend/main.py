from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from pathlib import Path

from .database import init_database
from .api import auth, scripts, folders, logs, execution
from .websocket_manager import WebSocketManager

# Initialize database
init_database()

app = FastAPI(
    title="PyScheduler",
    description="Python Script Scheduler & Monitor",
    version="1.0.0",
    redirect_slashes=False
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket manager for real-time updates
ws_manager = WebSocketManager()

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "PyScheduler"}

# API routes
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(scripts.router, prefix="/api/scripts", tags=["scripts"])
app.include_router(folders.router, prefix="/api/folders", tags=["folders"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(execution.router, prefix="/api/execution", tags=["execution"])

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# Serve frontend static files (if they exist)
frontend_dist = Path(__file__).parent.parent / "frontend"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)