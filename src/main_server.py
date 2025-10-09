"""
FastAPI WebSocket Server - Capa de Transporte

IMPORTANTE: Este servidor NO conoce los detalles de AG2.
Solo conoce la interfaz BaseAgent.

Ventajas:
- Desacoplamiento total de AG2 y WebSockets
- Fácil de testear
- Fácil de reemplazar (HTTP, gRPC, etc.)
- Fácil de cambiar la implementación del agente
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import os
import json
from ag2_agent import Ag2Agent
from base_agent import AgentEventType

app = FastAPI(title="AG2 Vacation Planner - Decoupled Architecture")


@app.get("/")
async def get_index():
    """Sirve el HTML"""
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(html_path)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket completamente desacoplado de AG2.

    Este endpoint:
    1. Solo conoce la interfaz BaseAgent
    2. Maneja la serialización de eventos
    3. Gestiona el ciclo de vida del WebSocket
    4. NO tiene lógica de negocio de AG2
    """
    await websocket.accept()

    # Crear instancia del agente (podría ser cualquier implementación de BaseAgent)
    agent = Ag2Agent(config={
        "max_rounds": 15,
        "temperature": 0.7
    })

    try:
        # Mensaje inicial del usuario
        user_message = """I want to plan a vacation!

My preferences:
- Budget: Around $2000
- Duration: 5 days
- Interests: Culture, food, history
- Preferred location: Europe

Please create a vacation plan for me!"""

        # Enviar mensaje de inicio
        await websocket.send_json({
            "type": "started",
            "content": "Starting vacation planning..."
        })

        # CLAVE: Iterar sobre eventos del agente
        # El agente NO sabe que estamos usando WebSockets
        async for event in agent.chat(user_message):

            print(f"📡 Server received event: {event.type} (UUID: {event.uuid})")

            # Pydantic serializa automáticamente a dict JSON-safe
            event_data = event.model_dump()

            await websocket.send_json(event_data)

            # CLAVE: Si el agente necesita input, esperamos respuesta del cliente
            # El BLOQUEO está AQUÍ (en la capa de transporte), NO en el agente
            if event.type == AgentEventType.INPUT_REQUEST:
                print("⏸️  Waiting for user input via WebSocket...")

                # Enviar señal especial para que el frontend muestre el input
                await websocket.send_json({
                    "type": "input_needed",
                    "uuid": event.uuid,
                    "prompt": event.metadata.get("prompt", "Please provide input:")
                })

                # AQUÍ es donde bloqueamos esperando la respuesta del usuario
                # Pero el agente NO está bloqueado, solo esta capa de transporte
                user_input = await websocket.receive_text()
                print(f"✅ Received user input: {user_input[:50]}...")

                # Enviar la respuesta al agente
                await agent.respond(event.uuid, user_input)
                print("✅ Response sent to agent, continuing...")

        # Enviar mensaje de completado
        await websocket.send_json({
            "type": "completed",
            "content": "Vacation planning completed! 🏖️"
        })

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "content": str(e),
                "error_type": type(e).__name__
            })
        except:
            pass


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ag2-vacation-planner"}


# Endpoints adicionales que demuestran el desacoplamiento
@app.post("/api/chat")
async def http_chat_endpoint(message: dict):
    """
    Ejemplo de endpoint HTTP usando el mismo agente.

    Demuestra que el agente funciona con cualquier transporte.
    """
    agent = Ag2Agent()
    events = []

    try:
        async for event in agent.chat(message.get("message", "")):
            events.append(event.model_dump())

            # En HTTP, no podemos esperar input del usuario de forma interactiva
            # Esto es una limitación del protocolo HTTP, no del agente
            if event.type == AgentEventType.INPUT_REQUEST:
                return {
                    "status": "input_required",
                    "event_id": event.uuid,
                    "prompt": event.metadata.get("prompt"),
                    "events": events
                }

        return {
            "status": "completed",
            "events": events
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "events": events
        }


@app.post("/api/respond")
async def http_respond_endpoint(data: dict):
    """
    Endpoint para responder a un evento pendiente.

    En una implementación real, necesitarías mantener
    las instancias de agentes en una sesión/caché.
    """
    return {
        "status": "not_implemented",
        "message": "Requires session management"
    }


if __name__ == "__main__":

    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)