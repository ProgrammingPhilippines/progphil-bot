from collections.abc import Sequence
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.bot.config import AIConfig
from src.data.ai.history import AIHistoryDB, format_search_results


@dataclass(frozen=True, slots=True)
class AIDeps:
    history_db: AIHistoryDB
    guild_id: int
    channel_id: int
    searchable_channel_ids: tuple[int, ...] = ()


class AI:
    config: AIConfig
    agent: Agent[AIDeps, str]

    def __init__(self, config: AIConfig, system_prompt: str) -> None:
        self.config = config
        self.agent = _setup_agent(config, system_prompt)

    async def call(
        self,
        prompt: str,
        message_history: Sequence[ModelMessage],
        deps: AIDeps,
    ) -> str:
        result = await self.agent.run(
            prompt,
            message_history=message_history,
            deps=deps,
            usage_limits=UsageLimits(request_limit=8, tool_calls_limit=4),
        )
        return result.output


def _setup_agent(config: AIConfig, system_prompt: str) -> Agent[AIDeps, str]:
    provider = OpenAIProvider(api_key=config.token, base_url=config.base_url)
    model = OpenAIChatModel(config.model, provider=provider)
    agent: Agent[AIDeps, str] = Agent(
        model,
        system_prompt=system_prompt,
        deps_type=AIDeps,
        retries=1,
        tool_timeout=20,
    )

    @agent.tool
    async def search_history(ctx: RunContext[AIDeps], query: str) -> str:
        """Search this guild's archive for relevant Discord context."""
        records = await ctx.deps.history_db.search_history(
            guild_id=ctx.deps.guild_id,
            query=query,
            channel_ids=ctx.deps.searchable_channel_ids
            or (ctx.deps.channel_id,),
            limit=5,
        )
        return format_search_results(records)

    return agent
