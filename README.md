# AG2 Web UI Integration

A working implementation of AG2 (AutoGen 2.0) agents with real-time web interfaces. This project demonstrates **multiple architectural approaches**:

1. **New Interface Way** (recommended): Decoupled architecture following **Dependency Inversion Principle** with abstract interfaces
2. **WebSocket Implementation** (legacy): Direct WebSocket integration
3. **SSE + HTTP Implementation** (legacy): Server-Sent Events for streaming with HTTP POST for user input

> **Note:** The legacy implementations (`src/legacy/`) are kept for reference but the recommended approach is the new decoupled architecture in `src/new_interface_way/`

## 🎬 Demo Video


https://github.com/user-attachments/assets/3e5e83c0-7407-4529-b748-b45aee2a93fe



## The Problem This Solves

AG2 documentation and examples focus mainly on CLI usage. Integrating AG2 with web UIs requires handling async agent events and bidirectional communication, which isn't well documented. This project demonstrates working solutions, including a **decoupled architecture** that follows SOLID principles for better testability and maintainability.

## 🏗️ Architecture

### New Interface Way (Recommended - Decoupled Architecture)

This implementation follows the **Dependency Inversion Principle** for clean separation of concerns:

```
┌─────────────────────────────────────────────────┐
│          Capa de Transporte                     │
│  (WebSocket, HTTP, CLI, gRPC, etc.)             │
│                                                  │
│  - Maneja comunicación con el cliente           │
│  - Serializa eventos                            │
│  - AQUÍ se bloquea esperando input              │
└────────────────┬────────────────────────────────┘
                 │ depende de ↓
┌────────────────▼────────────────────────────────┐
│          BaseAgent (Interfaz ABC)               │
│                                                  │
│  - chat(message) -> AsyncIterator[AgentEvent]   │
│  - respond(event_id, message)                   │
│  - NO conoce el transporte                      │
└────────────────▲────────────────────────────────┘
                 │ implementa ↑
┌────────────────┴────────────────────────────────┐
│          Ag2VacationAgent                       │
│                                                  │
│  - Implementación concreta usando AG2           │
│  - Emite eventos vía yield                      │
│  - NO bloquea esperando input                   │
│  - NO conoce WebSockets                         │
└─────────────────────────────────────────────────┘
```

**Key Benefits:**
- ✅ **Decoupled**: AG2 logic is independent of transport layer (WebSocket, HTTP, CLI)
- ✅ **Testable**: Can test agent logic without network infrastructure
- ✅ **Reusable**: Same agent works with any transport
- ✅ **Extensible**: Easy to add new agent implementations

**Location:** `src/new_interface_way/`

---

## 📚 Legacy Implementations

Earlier implementations are kept in `src/legacy/` for reference:
- **WebSocket** (`src/legacy/websockets_way/`): Direct WebSocket integration with AG2 agents
- **SSE + HTTP** (`src/legacy/old_sse_events_http/`): Server-Sent Events for streaming with HTTP POST for input

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

   **New Interface Way (Recommended):**
   ```bash
   cd src/new_interface_way
   python main_server.py
   ```
   Access at: http://localhost:8000

## 📁 File Structure

```
ag2-web-interface/
├── src/
│   ├── new_interface_way/       # Recommended decoupled architecture
│   │   ├── base_agent.py        # Abstract interface (ABC)
│   │   ├── ag2_agent.py         # AG2 implementation
│   │   ├── main_server.py       # WebSocket transport layer
│   │   ├── simple_vacation_agents.py  # AG2 agent configuration
│   │   ├── index.html           # Basic WebSocket client
│   │   └── index_improved.html  # Enhanced WebSocket client
│   └── legacy/                  # Previous implementations
│       ├── websockets_way/      # Direct WebSocket integration
│       └── old_sse_events_http/ # SSE + HTTP implementation
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

## 📖 Deep Dive: Decoupled Architecture

### 🎯 The Problem with Direct Coupling

The legacy implementations directly coupled AG2 with the transport layer:

```python
# ❌ PROBLEM: AG2 blocked on WebSocket
async for event in response.events:
    if event.type == 'input_request':
        user_input = await websocket.receive_text()  # AG2 thread blocked!
        await event.content.respond(user_input)
```

**Issues:**
- ❌ AG2 directly coupled to WebSockets
- ❌ Difficult to test without network infrastructure
- ❌ Cannot reuse with other transports (HTTP, gRPC, CLI)
- ❌ AG2 thread blocked waiting for WebSocket input

### ✅ The Solution: Dependency Inversion

The new architecture inverts dependencies using abstract interfaces:

```
┌─────────────────────────────────────────────────┐
│          Transport Layer                        │
│  (WebSocket, HTTP, CLI, gRPC, etc.)             │
│  - Handles client communication                 │
│  - Serializes events                            │
│  - Blocking happens HERE (correct place)        │
└────────────────┬────────────────────────────────┘
                 │ depends on ↓
┌────────────────▼────────────────────────────────┐
│          BaseAgent (ABC Interface)              │
│  - chat(message) -> AsyncIterator[AgentEvent]   │
│  - respond(event_id, message)                   │
│  - NO knowledge of transport                    │
└────────────────▲────────────────────────────────┘
                 │ implements ↑
┌────────────────┴────────────────────────────────┐
│          Ag2VacationAgent                       │
│  - Concrete AG2 implementation                  │
│  - Emits events via yield                       │
│  - Does NOT block on input                      │
│  - NO knowledge of WebSockets                   │
└─────────────────────────────────────────────────┘
```

### 🔑 Key Concept: Blocking in the Right Layer

```python
# In ag2_agent.py (Does NOT block)
async def chat(self, message):
    async for event in ag2_response.events:
        if event.type == 'input_request':
            yield AgentEvent(...)  # Just emit event
            # Use Future to wait for respond() call
            future = asyncio.Future()
            await future  # Wait for respond() to resolve it
```

```python
# In main_server.py (Blocking is CORRECT here)
async for event in agent.chat(message):
    if event.type == AgentEventType.INPUT_REQUEST:
        await websocket.send_json({...})
        user_input = await websocket.receive_text()  # ✅ Block in transport layer
        await agent.respond(event.uuid, user_input)
```

### 📊 Separation of Responsibilities

| Component | Responsibility | Does NOT Know About |
|-----------|---------------|-------------------|
| `BaseAgent` | Define contract | Implementation details |
| `Ag2Agent` | AG2 business logic | WebSockets, HTTP, CLI |
| `main_server.py` | WebSocket transport | AG2 internal details |
| `index.html` | UI client | Business logic |

### 🎨 Benefits of This Architecture

#### ✅ Decoupling
AG2 logic is completely independent of transport. Easy to swap WebSocket for HTTP, gRPC, or CLI.

#### ✅ Testability
```python
# Test without any network infrastructure
agent = Ag2VacationAgent()
events = []
async for event in agent.chat("test"):
    events.append(event)
assert len(events) > 0
```

#### ✅ Reusability
Same agent, different transports:

```python
# WebSocket
async for event in agent.chat(msg):
    await websocket.send_json(event.to_dict())

# HTTP
events = [e.to_dict() async for e in agent.chat(msg)]
return {"events": events}

# CLI
async for event in agent.chat(msg):
    print(event.content)
```

#### ✅ Extensibility
```python
# New implementation without touching transport layer
class OpenAIAgent(BaseAgent):
    async def chat(self, message):
        # OpenAI Assistants API implementation
        yield AgentEvent(...)

# Server works unchanged
agent = OpenAIAgent()  # Or Ag2VacationAgent()
async for event in agent.chat(message):
    await websocket.send_json(event.to_dict())
```

### 🔄 Execution Flow

```
1. Client connects via WebSocket
         ↓
2. main_server.py creates Ag2VacationAgent()
         ↓
3. Calls agent.chat(message)
         ↓
4. Ag2Agent starts AG2 and emits events
         ↓
5. main_server receives events via yield
         ↓
6. main_server sends events to client
         ↓
7. If INPUT_REQUEST event:
   - Client shows input prompt
   - User types response
   - Client sends via WebSocket
   - main_server calls agent.respond()
   - Ag2Agent resolves Future and continues
         ↓
8. When AG2 completes, emits COMPLETED
         ↓
9. Client receives COMPLETED event
```

### 🎓 SOLID Principles Applied

1. **S**ingle Responsibility
   - `BaseAgent`: Define contract
   - `Ag2Agent`: Business logic
   - `main_server`: Transport

2. **O**pen/Closed
   - Open for extension: New BaseAgent implementations
   - Closed for modification: main_server unchanged

3. **L**iskov Substitution
   - Any BaseAgent implementation works in main_server

4. **I**nterface Segregation
   - Specific interfaces (chat, respond, upload_file)

5. **D**ependency Inversion ⭐
   - High-level (main_server) doesn't depend on low-level (AG2)
   - Both depend on abstraction (BaseAgent)

### 📝 Comparison: Legacy vs Decoupled

| Aspect | Legacy | Decoupled |
|--------|--------|-----------|
| **Coupling** | AG2 ↔ WebSocket | AG2 ← BaseAgent → WebSocket |
| **Testable** | ❌ Needs WebSocket | ✅ Simple unit tests |
| **Reusable** | ❌ Only WebSocket | ✅ Any transport |
| **Blocking** | ❌ In AG2 layer | ✅ In transport layer |
| **Extensible** | ❌ Difficult | ✅ Easy (inherit BaseAgent) |



With 💗, Irene
