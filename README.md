# AG2 Web UI Integration

A working implementation of AG2 (AutoGen 2.0) agents with a real-time web interface using **Server-Sent Events (SSE)** for agent-to-UI communication and **HTTP POST** for UI-to-agent communication.

## 🎬 Demo Video

https://github.com/irenebosque/ag2-web-interface/raw/master/assets/demo.mp4

## The Problem This Solves

AG2 documentation and examples focus mainly on CLI usage. Integrating AG2 with web UIs requires handling async agent events and bidirectional communication, which isn't well documented. This project demonstrates a working solution using `a_run_group_chat` with event streaming.

## 🏗️ Architecture

The solution uses a clean 3-layer architecture:

```
┌─────────────────┐   HTTP POST     ┌─────────────────┐
│                 │ ──────────────► │                 │
│   Web UI        │                 │  FastAPI App    │
│  (index.html)   │ ◄────────────── │   (app.py)      │
│                 │      SSE        │                 │
└─────────────────┘                 └─────────────────┘
                                             │ process_chat()
                                             │ + input_queue
                                             ▼
                                    ┌─────────────────┐
                                    │ Streaming       │ run_chat()
                                    │ Service         │ ──────────┐
                                    │(ag2_streaming_  │           │
                                    │ service.py)     │           │
                                    └─────────────────┘           │
                                             ▲                    │
                                             │ Async Events       │
                                             │ + JSON Convert     │
                                             │                    ▼
                                    ┌─────────────────────────────────┐
                                    │        AG2 Agents               │
                                    │      (ag2_agents.py)            │
                                    │                                 │
                                    │  a_run_group_chat() ────────►   │
                                    │  ├─ triage_agent                │
                                    │  ├─ tech_agent                  │
                                    │  ├─ general_agent               │
                                    │  └─ user (input_mode=ALWAYS)    │
                                    └─────────────────────────────────┘
```

**Communication Protocols:**
- **UI → FastAPI**: HTTP POST (user messages, input responses)
- **FastAPI → UI**: Server-Sent Events (real-time agent events and messages)

### Layer Details

1. **Web UI Layer** (`index.html`):
   - Simple HTML interface with JavaScript
   - Connects via Server-Sent Events for real-time agent messages
   - Sends user input via HTTP POST when agents request it
   - Single input field with intelligent send button

2. **FastAPI App Layer** (`app.py`):
   - Provides HTTP endpoints for chat initiation and user input
   - Manages asyncio Queue for bidirectional communication
   - Serves the web interface
   - Handles CORS and web server concerns

3. **Streaming Service Layer** (`ag2_streaming_service.py`):
   - **This is the crucial bridge layer**
   - Converts AG2 events to JSON-serializable Server-Sent Events
   - Handles the complex async coordination between web requests and AG2 events
   - Manages input_request events by coordinating with the UI queue

4. **Pure AG2 Layer** (`ag2_agents.py`):
   - Contains pure AG2 agent logic without web dependencies
   - Can be tested standalone from command line
   - Uses `a_run_group_chat` with `AutoPattern` for event streaming
   - Implements triage pattern with specialized agents

## Key Implementation: `a_run_group_chat` + Event Streaming

The main approach that enables web integration:

```python
# This is what enables web UI integration!
response = await a_run_group_chat(
    pattern=pattern, 
    messages=message, 
    max_rounds=max_rounds
)

# The response.events async iterator is the key
async for event in response.events:
    # Convert to web-friendly format
    yield f"data: {json.dumps(event_dict)}\n\n"
```

**How it works:**
- `a_run_group_chat` returns an async response with an event stream
- The event stream includes all agent interactions, state changes, and input requests
- Events can be iterated in real-time and streamed to the web UI via SSE
- When agents request input (`event.type == "input_request"`), coordination happens via async queues

## 🚀 Communication Flow

### 1. Starting a Conversation (AG2 → UI via SSE)

```
User types message → POST /chat → AG2 agents start → Events stream via SSE
```

1. User enters message in web UI
2. JavaScript sends HTTP POST to `/chat`
3. FastAPI calls `process_chat()` with message and input queue
4. `ag2_streaming_service` calls `run_chat()` from `ag2_agents`
5. AG2 starts conversation and returns async event stream
6. Events are converted to JSON and streamed via Server-Sent Events
7. Web UI receives real-time updates of agent conversations

### 2. User Input Request (Bidirectional via SSE + HTTP)

```
Agent needs input → SSE "waiting_for_input" → User types → POST /send_input → AG2 continues
```

1. AG2 agent hits `input_request` event (when human_input_mode="ALWAYS")
2. Streaming service sends `waiting_for_input` event via SSE
3. Web UI shows input prompt to user
4. User types response and submits
5. JavaScript sends HTTP POST to `/send_input`
6. FastAPI queues user input via `input_queue.put()`
7. Streaming service receives input via `input_queue.get()`
8. Input is sent back to AG2 agents via `event.content.respond()`
9. AG2 continues conversation with user input

## 📋 Agent Configuration

The system implements a triage pattern:

- **triage_agent**: Routes queries to appropriate specialists
- **tech_agent**: Handles technical issues and troubleshooting  
- **general_agent**: Handles non-technical support questions
- **user**: Human user with `human_input_mode="ALWAYS"` for interactive conversations

## 🛠️ Setup and Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   Create `.env` file with:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the interface:**
   Open http://localhost:8888 in your browser

## 📁 File Structure

```
ag2-ui/
├── app.py                    # FastAPI web server
├── ag2_streaming_service.py  # AG2-to-web streaming bridge
├── ag2_agents.py            # Pure AG2 agent implementation
├── index.html               # Web interface
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── README.md               # This file
```

## 🧪 Testing

### Test AG2 Agents Standalone
```bash
python ag2_agents.py
```
*Note: Input requests won't work properly in CLI mode as they need the web queue system*

### Test Full Web Integration
1. Run `python app.py`
2. Open http://localhost:8888
3. Type a message and interact with the agents
4. Test the bidirectional communication when agents request input

## 🔧 Customization

### Adding New Agents
1. Create new `ConversableAgent` in `ag2_agents.py`
2. Add to the `agents` list in `AutoPattern`
3. Update system messages as needed

### Modifying UI
- Edit `index.html` for interface changes
- Modify JavaScript event handlers for different behaviors
- Customize CSS styling in the `<style>` section

### Changing Models
Update the `LLMConfig` in `ag2_agents.py`:
```python
llm_config = LLMConfig(
    api_type="openai",
    model="gpt-4-mini",  # Change model here
    api_key=os.getenv("OPENAI_API_KEY")
)
```

## 🚨 Important Notes

- **CORS Configuration**: Currently set to allow all origins (`"*"`) for development. Restrict this in production.
- **Error Handling**: Basic error handling is implemented. Add more robust error handling for production use.
- **Security**: The API key is loaded from environment variables. Never commit secrets to the repository.
- **Scalability**: This implementation uses in-memory queues. For production, consider Redis or other message brokers.

## Why This Matters

This implementation demonstrates:
1. How to bridge AG2's async system with web interfaces
2. Real-time bidirectional communication between agents and users  
3. Clean architecture separating concerns
4. A practical working example for web-based AG2 integration

Using `a_run_group_chat` with event streaming enables building web-based AI agent interfaces with proper real-time interaction.



With 💗, Irene
