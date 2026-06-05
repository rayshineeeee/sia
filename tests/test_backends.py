"""Tests for the agent-backend registry and the PydanticAI backend."""

import asyncio

import pytest

from sia.backends import available_backends, get_backend


def test_registry_lists_builtin_backends():
    assert set(available_backends()) >= {"claude", "openhands", "pydantic-ai"}


def test_get_backend_returns_callable():
    assert callable(get_backend("claude"))
    assert callable(get_backend("pydantic-ai"))


def test_get_backend_unknown_raises():
    with pytest.raises(ValueError):
        get_backend("does-not-exist")


def test_util_reexports_registry_run_agent():
    from sia.backends import run_agent as backend_run_agent
    from sia.util import run_agent as util_run_agent

    assert util_run_agent is backend_run_agent


def test_pydantic_ai_backend_runs_with_test_model(tmp_path):
    pytest.importorskip("pydantic_ai")
    from pydantic_ai.models.test import TestModel

    from sia.backends.pydantic_ai import run_agent_pydantic_ai

    # TestModel drives the agent without network; it exercises each registered tool,
    # so write_file should create a file in the working directory.
    asyncio.run(
        run_agent_pydantic_ai(
            TestModel(),
            "5",
            "Create a file with some content using the write_file tool.",
            str(tmp_path),
        )
    )
    assert any(tmp_path.iterdir())


def test_pydantic_ai_model_passthrough():
    from sia.backends.pydantic_ai import _resolve_model

    # Model specs are passed through unchanged to PydanticAI's native parsing.
    assert _resolve_model("openai:gpt-4o") == "openai:gpt-4o"
    assert _resolve_model("anthropic:claude-sonnet-4-5") == "anthropic:claude-sonnet-4-5"
    # No provider -> still a plain passthrough.
    assert _resolve_model("openai:gpt-4o", None) == "openai:gpt-4o"


def test_openhands_model_gets_openai_prefix_for_compatible_provider():
    """An OpenAI-compatible provider (base_url) gets an explicit litellm 'openai/' prefix."""
    from sia.backends.openhands import _resolve_model
    from sia.providers import load_provider

    nebius = load_provider("nebius")  # client_kind=openai, has base_url
    assert _resolve_model("moonshotai/Kimi-K2.6", nebius) == "openai/moonshotai/Kimi-K2.6"
    # Already prefixed -> not double-prefixed.
    assert _resolve_model("openai/gpt-4o", nebius) == "openai/gpt-4o"


def test_openhands_model_passthrough_without_compatible_provider():
    """Native (anthropic) and provider-less specs pass through unchanged."""
    from sia.backends.openhands import _resolve_model
    from sia.providers import load_provider

    assert _resolve_model("claude-sonnet-4-5", None) == "claude-sonnet-4-5"
    anthropic = load_provider("anthropic")  # client_kind=anthropic, no base_url
    assert _resolve_model("claude-sonnet-4-5", anthropic) == "claude-sonnet-4-5"


def test_run_agent_threads_provider_to_backend():
    """run_agent forwards the optional provider kwarg to the dispatched backend."""
    import asyncio

    from sia.backends import base
    from sia.providers import load_provider

    captured = {}

    async def fake_runner(model, max_turns, prompt, cwd, provider=None):
        captured["provider"] = provider

    base.register("capture-test", fake_runner)
    nebius = load_provider("nebius")
    asyncio.run(base.run_agent("m", "5", "p", "/tmp", backend="capture-test", provider=nebius))
    assert captured["provider"] is nebius
