# AG2 Web UI Integration

A production-ready implementation of AG2 (AutoGen 2.0) agents with real-time web interfaces, built with **clean architecture** following SOLID principles.

## 🎬 Demo Video

https://github.com/user-attachments/assets/3e5e83c0-7407-4529-b748-b45aee2a93fe

## The Problem This Solves

AG2 documentation and examples focus mainly on CLI usage. Integrating AG2 with web UIs requires handling async agent events and bidirectional communication, which isn't well documented. This project demonstrates a **decoupled architecture** that solves this problem while maintaining testability and maintainability.

## 🏗️ Architecture

This implementation follows the **Dependency Inversion Principle** for clean separation of concerns:

```
┌─────────────────────────────────────────────────┐
│          Transport Layer                        │
│  (WebSocket, HTTP, CLI, gRPC, etc.)             │
│                                                  │
│  - Handles client communication                 │
│  - Serializes events                            │
│  - Blocking happens HERE (correct place)        │
└────────────────┬────────────────────────────────┘
                 │ depends on ↓
┌────────────────▼────────────────────────────────┐
│          BaseAgent (ABC Interface)              │
│                                                  │
│  - chat(message) -> AsyncIterator[AgentEvent]   │
│  - respond(event_id, message)                   │
│  - NO knowledge of transport                    │
└────────────────▲────────────────────────────────┘
                 │ implements ↑
┌────────────────┴────────────────────────────────┐
│          Ag2VacationAgent                       │
│                                                  │
│  - Concrete AG2 implementation                  │
│  - Emits events via yield                       │
│  - Does NOT block on input                      │
│  - NO knowledge of WebSockets                   │
└─────────────────────────────────────────────────┘
```

**Key Benefits:**
- ✅ **Decoupled**: AG2 logic is independent of transport layer (WebSocket, HTTP, CLI)
- ✅ **Testable**: Can test agent logic without network infrastructure
- ✅ **Reusable**: Same agent works with any transport
- ✅ **Extensible**: Easy to add new agent implementations

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
   cd src/new_interface_way
   python main_server.py
   ```
   Access at: http://localhost:8000

## 📁 File Structure

```
ag2-web-interface/
├── src/
│   └── new_interface_way/       # Decoupled architecture
│       ├── base_agent.py        # Abstract interface (ABC)
│       ├── ag2_agent.py         # AG2 implementation
│       ├── main_server.py       # WebSocket transport layer
│       ├── simple_vacation_agents.py  # AG2 agent configuration
│       ├── index.html           # Basic WebSocket client
│       └── index_improved.html  # Enhanced WebSocket client
├── assets/
│   └── demo.mp4                 # Demo video
├── requirements.txt             # Python dependencies
├── .env                        # Environment variables
└── README.md                   # This file
```

## 🧪 Testing

### Test Agent Logic Without Web Infrastructure

One of the key benefits of the decoupled architecture:

```bash
cd src/new_interface_way
python ag2_agent.py
```

This demonstrates that the agent logic works independently of the transport layer.

### Test Full Web Integration

1. Run the server:
   ```bash
   cd src/new_interface_way
   python main_server.py
   ```
2. Open http://localhost:8000
3. Interact with the vacation planning agents
4. Test bidirectional communication when agents request input

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

---

## 📖 How It Works

### Core Concept: Separation of Concerns

The key is using an **abstract interface (`BaseAgent`)** to separate AG2 business logic from transport (WebSocket, HTTP, etc.).

### The Agent Layer (Business Logic)

```python
# ag2_agent.py - Emits events, doesn't know about WebSockets
async def chat(self, message):
    async for event in ag2_response.events:
        yield AgentEvent(...)  # Just emit events
```

### The Transport Layer (WebSocket/HTTP/CLI)

```python
# main_server.py - Handles WebSocket communication
async for event in agent.chat(message):
    await websocket.send_json(event.to_dict())
    if event.type == INPUT_REQUEST:
        user_input = await websocket.receive_text()
        await agent.respond(event.uuid, user_input)
```

**Benefits:**
- ✅ Test AG2 logic without network infrastructure
- ✅ Same agent works with WebSocket, HTTP, or CLI
- ✅ Easy to swap or add new transport layers

### Flow

1. Client connects → Server creates agent
2. User sends message → Agent processes with AG2
3. Agent emits events → Server sends to client via WebSocket
4. Agent needs input → Client shows prompt → User responds
5. Conversation continues until completion



With 💗, Irene
