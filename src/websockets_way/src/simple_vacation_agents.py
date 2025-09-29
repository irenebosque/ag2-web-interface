"""
Ultra simple AG2 vacation planning system
Just 2 agents: vacation_planner + reviewer_user
"""

import os
from dotenv import load_dotenv
from autogen import ConversableAgent, LLMConfig
from autogen.agentchat.group.patterns import AutoPattern
from autogen.agentchat.group import ContextVariables
from autogen.agentchat.group.multi_agent_chat import a_run_group_chat
import asyncio

load_dotenv()

# Simple LLM config
llm_config = LLMConfig(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.7
)

# Context variables
context = ContextVariables(data={
    "destination": "",
    "budget": "",
    "duration": "",
    "vacation_plan": ""
})

# Vacation planner agent
vacation_planner = ConversableAgent(
    name="vacation_planner",
    system_message="""You are a vacation planning expert.

Your job is to create amazing vacation plans based on user preferences.

When you receive a request, create a detailed vacation plan that includes:
- Destination recommendations
- Daily itinerary (3-5 days)
- Budget breakdown
- Accommodation suggestions
- Must-see attractions
- Food recommendations

Be enthusiastic and creative! Present your plan in a clear, organized way.""",
    llm_config=llm_config
)

# Plan modifier agent
plan_modifier = ConversableAgent(
    name="plan_modifier",
    system_message="""You are a vacation plan modifier.

When users provide feedback on vacation plans, you:
1. Acknowledge their feedback
2. Modify the plan according to their preferences
3. Create an updated vacation plan

If they want a different country, suggest alternatives.
If they want changes to budget, activities, or duration, adjust accordingly.

Always be helpful and responsive to their needs.""",
    llm_config=llm_config
)

# Human reviewer
reviewer_user = ConversableAgent(
    name="reviewer_user",
    human_input_mode="ALWAYS",
    system_message="You are the human reviewing vacation plans. Provide feedback or approve the plan."
)

# Pattern configuration
pattern = AutoPattern(
    initial_agent=vacation_planner,
    agents=[vacation_planner, plan_modifier],  # Now we have 2 agents
    user_agent=reviewer_user,
    context_variables=context,
    group_manager_args={"llm_config": llm_config}
)




# SHARED AG2 CHAT FUNCTION
async def start_a_run_group_chat(messages, max_rounds=10):
    """Start AG2 chat and return response"""
    response = await a_run_group_chat(
        pattern=pattern,
        messages=messages,
        max_rounds=max_rounds
    )
    return response


# STANDALONE MODE
async def run_vacation_chat():
    """Run the vacation planning chat"""
    print("🏖️ Starting vacation planning...")

    messages = """I want to plan a vacation!

My preferences:
- Budget: Around $2000
- Duration: 5 days
- Interests: Culture, food, history
- Preferred location: Europe

Please create a vacation plan for me!"""

    # Run AG2 chat
    response = await start_a_run_group_chat(messages, max_rounds=10)

    # Process events
    async for event in response.events:
        print(f"📡 Event: {event.type}")

        if hasattr(event, 'content'):
            print(f"Content: {event.content}")

        # Handle input requests
        if event.type == 'input_request':
            print(f"\n🔔 {getattr(event, 'prompt', 'Input needed:')}")
            user_input = input("Your response: ")

            # Use event.content.respond for AG2 input handling
            if hasattr(event, 'content') and hasattr(event.content, 'respond'):
                await event.content.respond(user_input)

    print("✅ Vacation planning completed!")
    return response

# For CLI testing
if __name__ == "__main__":
    asyncio.run(run_vacation_chat())