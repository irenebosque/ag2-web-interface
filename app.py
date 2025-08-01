"""
FastAPI web server that bridges AG2 agents with a web UI.

This module provides the web API endpoints for:
1. Starting AG2 agent conversations via streaming responses
2. Handling bidirectional communication between UI and AG2 agents
3. Serving the test HTML interface

Key architecture points:
- Uses Server-Sent Events (SSE) for real-time agent communication
- Implements an asyncio Queue for user input handling when agents request it
- Separates AG2 logic from web concerns via the ag2_streaming_service module
"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio

from ag2_streaming_service import process_chat

app = FastAPI(title="AG2 Web Interface", version="1.0.0")

# Configure CORS to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global queue for bidirectional communication between UI and AG2 agents
# When agents request user input, responses are queued here
input_queue = asyncio.Queue()

class ChatRequest(BaseModel):
    """Request model for starting a chat conversation"""
    messages: list

class InputRequest(BaseModel):
    """Request model for user input responses during agent conversations"""
    message: str

# AG2 --> UI (real-time agent events and messages via SSE)
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Start an AG2 agent conversation and stream events back to the UI.
    
    This endpoint:
    1. Initiates AG2 agent conversation with the provided message
    2. Streams all agent events (messages, state changes, input requests) via SSE
    3. Handles the async event loop for real-time communication
    
    Returns:
        StreamingResponse: Server-sent events stream of agent interactions
    """
    event_generator = await process_chat(request.messages, input_queue)
    return StreamingResponse(event_generator, media_type="text/event-stream")


# UI --> AG2 (user input responses via HTTP POST when agents request it)
@app.post("/send_input") 
async def send_input(data: InputRequest):
    """
    Send user input response when AG2 agents request it.
    
    When agents have human_input_mode="ALWAYS", they pause and wait for user input.
    This endpoint queues the user's response to continue the conversation.
    
    Args:
        data: User's input message
        
    Returns:
        dict: Confirmation that input was queued
    """
    await input_queue.put(data.message)
    return {"status": "sent"}

@app.get("/")
async def test_page():
    """Serve the test HTML interface"""
    return FileResponse("index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8888)