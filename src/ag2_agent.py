"""
AG2 Agent Implementation - Implementación concreta de BaseAgent

Esta clase implementa BaseAgent usando AG2, pero NO sabe nada
sobre WebSockets ni ningún otro transporte.
"""

import uuid
from typing import AsyncIterator, Dict, Any, Optional
from base_agent import BaseAgent, AgentEvent, AgentEventType
from simple_vacation_agents import start_a_run_group_chat
import asyncio


class Ag2Agent(BaseAgent):
    """
    Implementación de BaseAgent usando AG2 para planificación de vacaciones.

    Esta clase:
    - NO conoce WebSockets
    - NO bloquea esperando input del usuario
    - Emite eventos que la capa de transporte maneja
    - Mantiene eventos pendientes en self.pending_events
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.context = {"step": 0}
        self.history = []
        self.files = []

    # region Storage - Implementaciones básicas

    async def list_files(self) -> list:
        return self.files

    async def upload_file(self, file_path: str) -> Dict[str, Any]:
        file_info = {
            "id": str(uuid.uuid4()),
            "path": file_path,
            "name": file_path.split("\\")[-1]
        }
        self.files.append(file_info)
        return file_info

    async def delete_file(self, file_id: str) -> bool:
        self.files = [f for f in self.files if f["id"] != file_id]
        return True

    async def reset(self) -> bool:
        self.context = {"step": 0}
        self.history = []
        self.files = []
        self.pending_events = {}
        return True

    # endregion

    # region History

    async def load_agent(self, agent: Any) -> bool:
        # Implementación futura
        return True

    async def load_history(self, history: list) -> bool:
        self.history = history
        return True

    async def unload_history(self) -> bool:
        self.history = []
        return True

    # endregion

    # region Context

    async def set_context(self, context: Dict[str, Any]) -> bool:
        self.context.update(context)
        return True

    async def get_context(self, name: str) -> Any:
        return self.context.get(name)

    async def delete_context(self, name: str) -> bool:
        if name in self.context:
            del self.context[name]
            return True
        return False

    # endregion

    # region Chat - Implementación principal

    async def chat(self, message: str) -> AsyncIterator[AgentEvent]:
        """
        Inicia chat con AG2.

        IMPORTANTE: Este método NO bloquea esperando input del usuario.
        Cuando AG2 necesita input:
        1. Emite un evento INPUT_REQUEST con un UUID
        2. Guarda el evento en self.pending_events
        3. Continúa el yield (no bloquea)
        4. El cliente llama a respond() cuando tiene el input
        """
        try:
            # Incrementar step
            self.context["step"] += 1

            # Iniciar AG2 chat
            response = await start_a_run_group_chat(message, max_rounds=15)

            # Procesar eventos de AG2
            async for event in response.events:
                event_id = str(uuid.uuid4())

                # Emitir evento según el tipo
                if event.type == 'input_request':
                    print(f"\n🔔 [chat] INPUT_REQUEST detected, event_id={event_id}")

                    # Extraer info serializable del evento
                    prompt = getattr(event, 'prompt', 'Please provide input:')
                    content_str = str(event.content) if hasattr(event, 'content') else "Input needed"

                    # Guardar el evento AG2 original para responder después
                    self.pending_events[event_id] = event
                    print(f"💾 [chat] Saved event to pending_events[{event_id}]")

                    # IMPORTANTE: Crear el Future ANTES del yield
                    # Si lo creamos después, el código no se ejecuta hasta el próximo next()
                    future = asyncio.Future()
                    self.pending_events[f"{event_id}_future"] = future
                    print(f"💾 [chat] Created future: {event_id}_future")

                    agent_event = AgentEvent(
                        type=AgentEventType.INPUT_REQUEST,
                        uuid=event_id,
                        content=content_str,
                        metadata={
                            "prompt": str(prompt),
                            "event_type": event.type
                        }
                    )

                    print(f"📤 [chat] Yielding INPUT_REQUEST event")
                    yield agent_event

                    print(f"⏸️ [chat] Waiting for future to be resolved...")
                    await future  # Esperamos la respuesta
                    print(f"▶️ [chat] Future resolved! Continuing AG2 event processing...")

                elif event.type == 'agent_response' or hasattr(event, 'content'):
                    # Mensaje del agente
                    yield AgentEvent(
                        type=AgentEventType.AGENT_RESPONSE,
                        uuid=event_id,
                        content=getattr(event, 'content', str(event)),
                        metadata={
                            "agent": getattr(event, 'agent_name', 'unknown'),
                            "event_type": event.type
                        }
                    )

                else:
                    # Otros eventos
                    yield AgentEvent(
                        type=AgentEventType.MESSAGE,
                        uuid=event_id,
                        content=str(event),
                        metadata={"event_type": event.type}
                    )

            # Completado
            yield AgentEvent(
                type=AgentEventType.COMPLETED,
                uuid=str(uuid.uuid4()),
                content="Chat completed successfully",
                metadata={"final_context": self.context}
            )

        except Exception as e:
            yield AgentEvent(
                type=AgentEventType.ERROR,
                uuid=str(uuid.uuid4()),
                content=str(e),
                metadata={"error_type": type(e).__name__}
            )

    async def chat_with(self, agent: str, message: str) -> AsyncIterator[AgentEvent]:
        """Implementación futura para chat con agente específico"""
        yield AgentEvent(
            type=AgentEventType.ERROR,
            uuid=str(uuid.uuid4()),
            content="chat_with not implemented yet",
            metadata={}
        )

    async def respond(self, event_id: str, message: str) -> None:
        """
        Responde a un evento de input_request.

        CLAVE: Este método es llamado por la capa de transporte
        cuando tiene la respuesta del usuario.
        """
        print(f"\n🔧 [respond] Called with event_id={event_id}, message='{message[:50]}'")

        if event_id not in self.pending_events:
            print(f"❌ [respond] ERROR: event_id {event_id} not in pending_events")
            print(f"📋 [respond] Available events: {list(self.pending_events.keys())}")
            raise ValueError(f"No pending event with id {event_id}")

        # Obtener el evento original de AG2
        original_event = self.pending_events[event_id]
        print(f"✅ [respond] Found original event: {type(original_event)}")
        print(f"📄 [respond] Event details: {original_event}")

        # Responder al evento de AG2
        if hasattr(original_event, 'content') and hasattr(original_event.content, 'respond'):
            print(f"🔧 [respond] Calling original_event.content.respond()")
            await original_event.content.respond(message)
            print(f"✅ [respond] AG2 respond() completed")
        else:
            print(f"⚠️ [respond] WARNING: Event doesn't have content.respond method")

        # Resolver el Future para continuar el flujo
        future_key = f"{event_id}_future"
        if future_key in self.pending_events:
            print(f"🔧 [respond] Resolving future: {future_key}")
            future = self.pending_events[future_key]
            future.set_result(True)
            del self.pending_events[future_key]
            print(f"✅ [respond] Future resolved successfully")
        else:
            print(f"⚠️ [respond] WARNING: No future found for {future_key}")

        # Limpiar evento
        del self.pending_events[event_id]
        print(f"✅ [respond] Cleaned up event {event_id}")
        print(f"✅ [respond] Method completed, returning to caller\n")

    # endregion


# Ejemplo de uso en modo standalone (CLI)
async def test_ag2_agent():
    """
    Test del agente en modo CLI.

    Demuestra que el agente funciona sin WebSockets.
    """
    print("🏖️ Testing AG2 Agent (CLI mode)\n")

    agent = Ag2Agent()

    message = """I want to plan a vacation!

My preferences:
- Budget: Around $2000
- Duration: 5 days
- Interests: Culture, food, history
- Preferred location: Europe

Please create a vacation plan for me!"""

    async for event in agent.chat(message):
        print(f"\n📡 Event: {event.type}")
        print(f"   UUID: {event.uuid}")
        print(f"   Content: {str(event.content)[:200]}...")

        if event.type == AgentEventType.INPUT_REQUEST:
            print(f"\n🔔 Input needed!")
            user_input = input("Your response: ")
            await agent.respond(event.uuid, user_input)

    print("\n✅ Test completed!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ag2_agent())
