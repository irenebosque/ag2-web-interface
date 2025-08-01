"""
Pure AG2 agents implementation without web dependencies.

This module contains the core AG2 agent logic separated from any web or streaming
concerns. It can be run standalone for testing or integrated into web applications
via the streaming service layer.

The implementation uses AG2's a_run_group_chat with AutoPattern for agent coordination,
which was the key breakthrough for getting AG2 working with web UIs. This approach
allows proper event streaming and bidirectional communication.

Agents:
- triage_agent: Routes queries to appropriate specialized agents
- tech_agent: Handles technical issues and troubleshooting
- general_agent: Handles non-technical support questions
- user: Human user with ALWAYS input mode for interactive conversations
"""

import os
from dotenv import load_dotenv
from autogen.agentchat.conversable_agent import ConversableAgent
from autogen.agentchat.group.multi_agent_chat import a_run_group_chat
from autogen.agentchat.group.patterns.auto import AutoPattern
from autogen.llm_config import LLMConfig

load_dotenv()


async def run_chat(message, max_rounds=15):
    """
    Execute an AG2 agent conversation and return the response with events.
    
    This is the core AG2 function that can be used standalone or via web interface.
    It creates the agent configuration, sets up the conversation pattern, and
    executes the group chat using AG2's async event system.
    
    Args:
        message: The initial user message to start the conversation
        max_rounds: Maximum number of conversation rounds (default: 15)
        
    Returns:
        AsyncRunResponse: AG2 response object containing async event stream
    """
    llm_config = LLMConfig(
        api_type="openai",
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create agents within LLM config context
    with llm_config:
        # Agent that routes queries to appropriate specialists
        triage_agent = ConversableAgent(
            name="triage_agent",
            system_message="""You are a triage agent. For each user query,
            identify whether it is a technical issue or a general question. Route
            technical issues to the tech agent and general questions to the general agent.
            Do not provide suggestions or answers, only route the query.""",
        )

        # Specialist for technical issues and troubleshooting
        tech_agent = ConversableAgent(
            name="tech_agent",
            system_message="""You solve technical problems like software bugs
            and hardware issues.""",
        )

        # Specialist for general, non-technical support questions
        general_agent = ConversableAgent(
            name="general_agent", 
            system_message="You handle general, non-technical support questions."
        )

    # Human user agent - ALWAYS mode enables interactive input when needed
    user = ConversableAgent(name="user", human_input_mode="ALWAYS")

    # AutoPattern coordinates multi-agent conversations with automatic transitions
    # This was the key discovery for making AG2 work with web UIs
    pattern = AutoPattern(
        initial_agent=triage_agent,
        agents=[triage_agent, tech_agent, general_agent],
        user_agent=user,
        group_manager_args={"llm_config": llm_config},
    )

    # Execute the group chat - this returns an async response with event stream
    # The event stream is what enables real-time web UI integration
    response = await a_run_group_chat(
        pattern=pattern, 
        messages=message, 
        max_rounds=max_rounds
    )
    
    return response


if __name__ == "__main__":
    import asyncio
    
    async def main():
        """Standalone test function for running AG2 agents directly from command line."""
        message = input("Enter your message: ")
        response = await run_chat(message)
        
        # Print all events from the AG2 conversation
        # Note: input_request events won't work properly in CLI mode
        # as they need the web-based queue system for user interaction
        async for event in response.events:
            print(f"[{event.type}] {event.content}")
    
    asyncio.run(main())