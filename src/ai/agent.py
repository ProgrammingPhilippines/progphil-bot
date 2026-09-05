from src.bot.config import AIConfig
from src.utils.logging.logger import BotLogger

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider


class AI:
    config: AIConfig
    system_prompt: str
    agent: Agent

    def __init__(self, config: AIConfig, system_prompt: str) -> None:
        self.config = config
        self.system_prompt = system_prompt
        self.agent = _setup_agent(config)

    async def call(self, prompt: str, _message_history: list[str]) -> str:
        result = await self.agent.run(prompt)

        return result.output

def _setup_agent(config: AIConfig) -> Agent:
    print("[AGENT-SETUP] Setting up AGENT.\n")
    provider = OpenAIProvider(api_key=config.token, base_url=config.base_url)
    model = OpenAIChatModel(config.model, provider=provider)
    agent = Agent(model)

    @agent.instructions
    def add_the_users_name(ctx: RunContext[str]) -> str:
      return f"The user's name is {ctx.deps}."

    return agent
