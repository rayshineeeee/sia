"""Tests for the JSON-defined agent-profile registry."""

import json

import pytest

from sia.profiles import CODEGEN_BACKEND, AgentProfile, available_profiles, load_profile


def test_bundled_profiles_present():
    assert set(available_profiles()) >= {"default-meta", "default-target", "kimi-nebius"}


def test_default_meta_profile():
    p = load_profile("default-meta")
    assert isinstance(p, AgentProfile)
    assert p.profile_id == "default-meta"
    assert p.backend == "claude"
    assert p.model == "haiku"
    assert p.provider.provider_id == "anthropic"


def test_default_target_profile_is_codegen():
    p = load_profile("default-target")
    assert p.backend == CODEGEN_BACKEND
    assert p.model == "claude-haiku-4-5-20251001"
    assert p.provider.client_kind == "anthropic"


def test_kimi_nebius_profile_resolves_provider():
    p = load_profile("kimi-nebius")
    assert p.backend == CODEGEN_BACKEND
    assert p.model == "moonshotai/Kimi-K2.6"
    assert p.provider.provider_id == "nebius"
    assert p.provider.base_url.endswith("nebius.com/v1/")


def test_unknown_profile_raises():
    with pytest.raises(SystemExit):
        load_profile("nope")


def _write_profile(tmp_path, data):
    path = tmp_path / "p.json"
    path.write_text(json.dumps(data))
    return str(path)


def test_invalid_backend_raises(tmp_path):
    path = _write_profile(
        tmp_path, {"profile_id": "p", "name": "p", "backend": "bogus", "model": "m", "provider_id": "anthropic"}
    )
    with pytest.raises(SystemExit):
        load_profile(path)


def test_claude_backend_requires_anthropic_provider(tmp_path):
    path = _write_profile(
        tmp_path, {"profile_id": "p", "name": "p", "backend": "claude", "model": "m", "provider_id": "nebius"}
    )
    with pytest.raises(SystemExit):
        load_profile(path)


def test_openhands_backend_allows_non_anthropic_provider(tmp_path):
    path = _write_profile(
        tmp_path, {"profile_id": "p", "name": "p", "backend": "openhands", "model": "m", "provider_id": "nebius"}
    )
    profile = load_profile(path)
    assert profile.backend == "openhands"
    assert profile.provider.provider_id == "nebius"
