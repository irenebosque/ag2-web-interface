"""
Streaming service that adapts AG2 agent conversations for web UI consumption.

This module bridges the gap between AG2's async event system and web-based
Server-Sent Events (SSE). It converts AG2 events into JSON streams and handles
the bidirectional communication flow when agents request user input.

Key responsibilities:
- Convert AG2 events to JSON-serializable format
- Stream events to UI via Server-Sent Events protocol
- Handle input_request events by coordinating with UI via async queues
- Maintain the async event loop for real-time communication
"""

import asyncio
import json
from ag2_agents import run_chat


async def process_chat(messages, input_queue):
    """
    Process AG2 chat conversation and generate real-time events for web UI.
    
    This function acts as the core bridge between AG2 agents and the web interface.
    It starts an AG2 conversation and converts all events into Server-Sent Events
    format for real-time streaming to the frontend.
    
    Args:
        messages: List of chat messages from the UI
        input_queue: Asyncio queue for receiving user input when agents request it
        
    Returns:
        AsyncGenerator: Event generator that yields SSE-formatted events
    """
    async def event_generator():
        response = await run_chat(messages[-1]["content"])

        # Send initial context variables
        yield f"data: {json.dumps({'type': 'context_variables', 'content': {'which_agent': 'none'}})}\n\n"

        async for event in response.events:
            # Convert AG2 event to JSON-serializable dictionary
            event_dict = {
                'type': event.type,
                'content': str(event.content) if hasattr(event, 'content') else None
            }
            
            # Stream event to UI using Server-Sent Events format
            yield f"data: {json.dumps(event_dict)}\n\n"
            
            # Handle special case: when agents request user input
            if event.type == "input_request":
                # Notify UI that we're waiting for user input
                yield f"data: {json.dumps({'type': 'waiting_for_input'})}\n\n"
                
                # Wait for user response via the input queue (from HTTP POST /send_input)
                user_input = await input_queue.get()
                
                # Send user response back to AG2 agents to continue conversation
                await event.content.respond(user_input)

    return event_generator()