"""Agent-backend registry.

A backend runs a meta/feedback agent: an async runner with the signature
``run(model_name, max_turns, prompt, agent_working_directory)``. Backends register
themselves by name; the orchestrator and CLI discover them via this registry, so
adding one is a single ``register(...)`` call. Optional SDK imports happen lazily
inside each runner, so the registry lists every backend regardless of what's installed.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from sia.logging_setup import get_logger

if TYPE_CHECKING:
    from sia.providers import Provider

logger = get_logger(__name__)

# Runners accept (model_name, max_turns, prompt, working_dir) and an optional provider
# (keyword, default None) describing the endpoint/credentials for the meta agent.
AgentRunner = Callable[..., Awaitable[None]]

REGISTRY: dict[str, AgentRunner] = {}


def register(name: str, runner: AgentRunner) -> AgentRunner:
    """Register an agent-backend runner under ``name``."""
    REGISTRY[name] = runner
    return runner


def available_backends() -> list[str]:
    """Names of all registered backends."""
    return list(REGISTRY)


def get_backend(name: str) -> AgentRunner:
    """Return the runner registered under ``name`` (raises ValueError if unknown)."""
    if name not in REGISTRY:
        available = ", ".join(available_backends())
        raise ValueError(f"Unknown backend: {name}. Available: {available}")
    return REGISTRY[name]


async def run_agent(
    model_name: str,
    max_turns: str,
    prompt: str,
    agent_working_directory: str,
    backend: str = "claude",
    provider: Provider | None = None,
) -> None:
    """Dispatch to the named backend.

    Args:
        model_name: The model to use (format depends on backend).
        max_turns: Maximum number of turns for the agent.
        prompt: The task prompt to send to the agent.
        agent_working_directory: Working directory for the agent.
        backend: Which registered backend to use (e.g. "claude", "openhands", "pydantic-ai").
        provider: Optional endpoint/credentials for the model (api_key_env, base_url).
    """
    logger.info(f"Using {backend} backend")
    await get_backend(backend)(model_name, max_turns, prompt, agent_working_directory, provider=provider)
