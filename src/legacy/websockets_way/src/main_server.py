"""
Simple WebSocket server for AG2 agents
"""
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
import json
import os
from simple_vacation_agents import start_a_run_group_chat

app = FastAPI()

@app.get("/")
async def get_index():
    """Serve the HTML file"""
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(html_path)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        # Initial user message
        user_message = """I want to plan a vacation!

My preferences:
- Budget: Around $2000
- Duration: 5 days
- Interests: Culture, food, history
- Preferred location: Europe

Please create a vacation plan for me!"""

        # Run AG2 chat
        response = await start_a_run_group_chat(user_message, max_rounds=15)

        # Stream events
        async for event in response.events:

            print(f"📡 Event: {event.type}")
            # Send event to frontend
            await websocket.send_text(json.dumps({
                "type": event.type,
                "content": str(getattr(event, 'content', ''))[:2000]
            }))

            # Handle user input requests
            if event.type == 'input_request':
                await websocket.send_text(json.dumps({
                    "type": "input_needed"
                }))

                # Wait for user response
                user_input = await websocket.receive_text()

                # Send response back to AG2
                if hasattr(event, 'content') and hasattr(event.content, 'respond'):
                    await event.content.respond(user_input)

        # Send completion
        await websocket.send_text(json.dumps({
            "type": "completed",
            "content": "Chat completed!"
        }))

    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "content": str(e)
        }))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)