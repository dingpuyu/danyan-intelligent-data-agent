from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState


async def fail_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """Stop safely after the bounded SQL repair budget is exhausted."""
    runtime.stream_writer({"stage": "sql校验失败", "error": state.get("error")})
    return {}
