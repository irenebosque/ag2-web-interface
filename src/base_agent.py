"""
Base Agent Interface - Dependency Inversion Principle

Esta interfaz abstracta desacopla la lógica de negocio (AG2)
del transporte (WebSockets, HTTP, CLI, etc.)
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_serializer


class AgentEventType(str, Enum):
    """Tipos de eventos que puede emitir un agente"""
    MESSAGE = "message"
    INPUT_REQUEST = "input_request"
    AGENT_RESPONSE = "agent_response"
    ERROR = "error"
    COMPLETED = "completed"
    THINKING = "thinking"
    TOOL_CALL = "tool_call"


class AgentEvent(BaseModel):
    """
    Evento emitido por el agente.

    El agente emite eventos y no sabe nada sobre el transporte.
    La capa de transporte (WebSocket, HTTP, etc.) decide cómo serializar y enviar.

    Pydantic maneja automáticamente:
    - Validación de tipos
    - Serialización a dict/JSON
    - Conversión de tipos complejos
    """
    type: AgentEventType
    uuid: str
    content: Any
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        # Permite usar Enums directamente
        use_enum_values = True
        # Serializa cualquier tipo a JSON-safe automáticamente
        json_encoders = {
            Enum: lambda e: e.value
        }

    @field_serializer('content')
    def serialize_content(self, content: Any) -> str:
        """Convierte el contenido a string si no es serializable"""
        if content is None:
            return ""
        if isinstance(content, (str, int, float, bool)):
            return content
        return str(content)


class BaseAgent(ABC):
    """
    Interfaz base para todos los agentes.

    Principios:
    - El agente NO conoce el transporte (WebSockets, HTTP, etc.)
    - El agente emite eventos a través de generadores async
    - El agente mantiene un registro de eventos pendientes
    - La capa de transporte decide cómo manejar los eventos
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.pending_events: Dict[str, Any] = {}

    # region Storage

    @abstractmethod
    async def list_files(self) -> list:
        """Lista archivos disponibles"""
        pass

    @abstractmethod
    async def upload_file(self, file_path: str) -> Dict[str, Any]:
        """Sube un archivo al agente"""
        pass

    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """Elimina un archivo"""
        pass

    @abstractmethod
    async def reset(self) -> bool:
        """Resetea el estado del agente"""
        pass

    # endregion

    # region History

    @abstractmethod
    async def load_agent(self, agent: Any) -> bool:
        """Carga un agente específico"""
        pass

    @abstractmethod
    async def load_history(self, history: list) -> bool:
        """Carga historial de conversación"""
        pass

    @abstractmethod
    async def unload_history(self) -> bool:
        """Descarga el historial"""
        pass

    # endregion

    # region Context

    @abstractmethod
    async def set_context(self, context: Dict[str, Any]) -> bool:
        """Establece contexto del agente"""
        pass

    @abstractmethod
    async def get_context(self, name: str) -> Any:
        """Obtiene un valor del contexto"""
        pass

    @abstractmethod
    async def delete_context(self, name: str) -> bool:
        """Elimina un valor del contexto"""
        pass

    # endregion

    # region Chat - Métodos principales

    @abstractmethod
    async def chat(self, message: str) -> AsyncIterator[AgentEvent]:
        """
        Inicia una conversación con el agente.

        Retorna un generador asíncrono de eventos.
        El cliente (WebSocket, HTTP, CLI) decide cómo manejar cada evento.

        Ejemplo:
            async for event in agent.chat("Hello"):
                if event.type == AgentEventType.INPUT_REQUEST:
                    # El cliente decide cómo obtener el input
                    user_input = await get_user_input()
                    await agent.respond(event.uuid, user_input)

        Args:
            message: Mensaje del usuario

        Yields:
            AgentEvent: Eventos emitidos por el agente
        """
        pass

    @abstractmethod
    async def chat_with(self, agent: str, message: str) -> AsyncIterator[AgentEvent]:
        """
        Inicia conversación con un agente específico.

        Args:
            agent: Nombre del agente
            message: Mensaje

        Yields:
            AgentEvent: Eventos emitidos
        """
        pass

    @abstractmethod
    async def respond(self, event_id: str, message: str) -> None:
        """
        Responde a un evento pendiente (como input_request).

        Este método NO bloquea esperando input del usuario.
        El agente mantiene el evento pendiente y la capa de transporte
        llama a este método cuando tiene la respuesta.

        Args:
            event_id: UUID del evento al que se responde
            message: Respuesta del usuario
        """
        pass

    # endregion
