# AG2 Vacation Planner - Decoupled Architecture

## 🎯 Objetivo

Demostrar la **Inversión de Dependencias** (Dependency Inversion Principle) aplicada a AG2 y WebSockets.

### Problema anterior

```python
# En main_server.py (ACOPLADO)
async for event in response.events:
    if event.type == 'input_request':
        user_input = await websocket.receive_text()  # ❌ AG2 bloqueado en WebSocket
        await event.content.respond(user_input)
```

**Problemas:**
- ❌ AG2 está acoplado directamente a WebSockets
- ❌ Difícil de testear sin infraestructura de red
- ❌ No se puede reutilizar con otros transportes (HTTP, gRPC, CLI)
- ❌ El hilo de AG2 se bloquea esperando input de WebSocket

### Solución actual

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

## 📁 Estructura de archivos

```
new_interface_way/
├── base_agent.py              # Interfaz abstracta (ABC)
├── ag2_agent.py               # Implementación usando AG2
├── main_server.py             # Capa de transporte WebSocket
├── simple_vacation_agents.py  # Configuración de agentes AG2
├── index.html                 # Cliente WebSocket básico
├── index_improved.html        # Cliente WebSocket mejorado
└── README.md                  # Esta documentación
```

## 🚀 Cómo ejecutar

### 1. Instalar dependencias

```bash
pip install fastapi uvicorn websockets autogen python-dotenv
```

### 2. Configurar variables de entorno

Crea un archivo `.env` en esta carpeta:

```env
OPENAI_API_KEY=tu_api_key_aqui
```

### 3. Ejecutar el servidor

```bash
cd C:\Users\ilopez\Documents\ag2-web-interface\src\new_interface_way
python main_server.py
```

### 4. Abrir el navegador

```
http://localhost:8000
```

## 🧪 Testear sin WebSockets

El agente funciona **sin WebSockets**:

```bash
# Test en modo CLI
python ag2_agent.py
```

Esto demuestra el desacoplamiento: el agente funciona con cualquier capa de transporte.

## 🔑 Conceptos clave

### 1. Inversión de Dependencias

```python
# ❌ ANTES: Alto nivel depende de bajo nivel
class Ag2Agent:
    async def chat(self, websocket):
        user_input = await websocket.receive_text()  # Acoplamiento

# ✅ AHORA: Ambos dependen de abstracción
class BaseAgent(ABC):
    @abstractmethod
    async def chat(self) -> AsyncIterator[AgentEvent]:
        pass

class Ag2Agent(BaseAgent):  # NO conoce WebSockets
    async def chat(self):
        yield AgentEvent(...)

class WebSocketServer:  # NO conoce AG2
    async def handle(self):
        async for event in agent.chat():
            await websocket.send_json(event.to_dict())
```

### 2. El bloqueo está en el lugar correcto

```python
# En ag2_agent.py (NO bloquea)
async def chat(self, message):
    async for event in ag2_response.events:
        if event.type == 'input_request':
            yield AgentEvent(...)  # Solo emite evento
            # NO espera aquí, usa Future
            future = asyncio.Future()
            await future  # Espera a que respond() lo resuelva
```

```python
# En main_server.py (SÍ bloquea, pero es correcto)
async for event in agent.chat(message):
    if event.type == AgentEventType.INPUT_REQUEST:
        await websocket.send_json({...})
        user_input = await websocket.receive_text()  # ✅ Bloqueo en capa de transporte
        await agent.respond(event.uuid, user_input)
```

### 3. Separación de responsabilidades

| Componente | Responsabilidad | NO conoce |
|------------|----------------|-----------|
| `BaseAgent` | Define contrato | Nada (es interfaz) |
| `Ag2Agent` | Lógica de negocio AG2 | WebSockets, HTTP, CLI |
| `main_server.py` | Transporte WebSocket | Detalles internos de AG2 |
| `index.html` | UI del cliente | Lógica de negocio |

## 🎨 Ventajas de esta arquitectura

### ✅ Desacoplamiento
- AG2 no conoce el transporte
- Fácil cambiar de WebSocket a HTTP/gRPC/CLI

### ✅ Testeable
```python
# Test sin infraestructura
agent = Ag2VacationAgent()
events = []
async for event in agent.chat("test"):
    events.append(event)
assert len(events) > 0
```

### ✅ Reutilizable
```python
# Mismo agente, diferentes transportes

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

### ✅ Extensible
```python
# Nueva implementación sin tocar WebSocket
class OpenAIAgent(BaseAgent):
    async def chat(self, message):
        # Implementación con OpenAI Assistants API
        yield AgentEvent(...)

# El servidor funciona sin cambios
agent = OpenAIAgent()  # O Ag2VacationAgent()
async for event in agent.chat(message):
    await websocket.send_json(event.to_dict())
```

## 🔄 Flujo de ejecución

```
1. Cliente (HTML) conecta via WebSocket
                ↓
2. main_server.py crea Ag2VacationAgent()
                ↓
3. Llama agent.chat(message)
                ↓
4. Ag2Agent inicia AG2 y emite eventos
                ↓
5. main_server recibe eventos via yield
                ↓
6. main_server envía eventos al cliente
                ↓
7. Si evento es INPUT_REQUEST:
   - Cliente muestra input
   - Usuario escribe respuesta
   - Cliente envía via WebSocket
   - main_server llama agent.respond()
   - Ag2Agent resuelve Future y continúa
                ↓
8. Cuando AG2 termina, emite COMPLETED
                ↓
9. main_server envía COMPLETED al cliente
                ↓
10. Cliente muestra mensaje de éxito
```

## 📊 Comparación

| Aspecto | Versión anterior | Versión desacoplada |
|---------|-----------------|---------------------|
| **Acoplamiento** | AG2 ↔ WebSocket | AG2 ← BaseAgent → WebSocket |
| **Testeable** | ❌ Necesita WebSocket | ✅ Test unitario simple |
| **Reutilizable** | ❌ Solo WebSocket | ✅ Cualquier transporte |
| **Bloqueo** | ❌ En AG2 | ✅ En capa de transporte |
| **Extensible** | ❌ Difícil | ✅ Fácil (hereda BaseAgent) |

## 🎓 Principios aplicados

### SOLID

1. **S**ingle Responsibility
   - `BaseAgent`: Define contrato
   - `Ag2Agent`: Lógica de negocio
   - `main_server`: Transporte

2. **O**pen/Closed
   - Abierto a extensión: Nuevas implementaciones de BaseAgent
   - Cerrado a modificación: main_server no cambia

3. **L**iskov Substitution
   - Cualquier implementación de BaseAgent funciona en main_server

4. **I**nterface Segregation
   - Interfaces específicas (chat, respond, upload_file, etc.)

5. **D**ependency Inversion ⭐
   - Alto nivel (main_server) no depende de bajo nivel (AG2)
   - Ambos dependen de abstracción (BaseAgent)

## 🚧 Siguientes pasos

1. **Gestión de sesiones**: Mantener múltiples conversaciones simultáneas
2. **Persistencia**: Guardar historial en base de datos
3. **Autenticación**: Añadir JWT/OAuth
4. **Rate limiting**: Limitar peticiones por usuario
5. **Monitoring**: Métricas y logging
6. **Testing**: Tests unitarios y de integración

## 📝 Notas importantes

- El archivo `index.html` es compatible pero básico
- Usa `index_improved.html` para mejor UX
- El servidor usa `0.0.0.0:8000` por defecto
- Asegúrate de tener `OPENAI_API_KEY` configurada

## 🤝 Créditos

Arquitectura diseñada siguiendo el **Dependency Inversion Principle** (Robert C. Martin - Clean Architecture).
