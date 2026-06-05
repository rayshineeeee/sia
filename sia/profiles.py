"""Agent profiles — JSON-defined ``(backend, model, provider)`` bundles.

An ``AgentProfile`` fully describes how to run/define one agent role:

- the **meta/feedback** agent runs inside SIA via a registered ``backend``
  (claude / openhands / pydantic-ai);
- the **target** agent is generated code SIA never runs, so its backend is the
  sentinel :data:`CODEGEN_BACKEND` — the meta-agent refactors the task's reference
  agent to the profile's model/provider.

Profiles are JSON files (bundled under ``sia/defaults/profiles/`` and user-extensible
via ``$SIA_PROFILES_DIR`` or ``./profiles``). Each references a :class:`~sia.providers.Provider`
by name. Adding a profile is dropping a JSON file — no code change.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sia.backends import available_backends
from sia.config_files import available_names, read_config_text
from sia.providers import Provider, load_provider

ENV_VAR = "SIA_PROFILES_DIR"
SUBDIR = "profiles"

# Sentinel backend for the target agent: it is generated code, not a SIA backend.
CODEGEN_BACKEND = "codegen"


@dataclass(frozen=True)
class AgentProfile:
    """Full configuration for one agent role."""

    profile_id: str  # stable identifier (also the value passed to --meta-profile/--target-profile)
    name: str  # human-readable display name
    backend: str  # a registered backend, or CODEGEN_BACKEND for the target agent
    model: str
    provider: Provider


def available_profiles() -> list[str]:
    """Names of all profiles discoverable in the bundled + user directories."""
    return available_names(env_var=ENV_VAR, subdir=SUBDIR)


def load_profile(name_or_path: str) -> AgentProfile:
    """Load and validate a profile by bundled/user name or by path to a .json file."""
    text, source = read_config_text(name_or_path, env_var=ENV_VAR, subdir=SUBDIR, kind="profile")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid profile JSON at {source}: {exc}") from exc

    missing = {"profile_id", "name", "backend", "model", "provider_id"} - data.keys()
    if missing:
        raise SystemExit(f"Profile at {source} is missing required keys: {', '.join(sorted(missing))}")

    provider = load_provider(data["provider_id"])
    profile = AgentProfile(
        profile_id=data["profile_id"],
        name=data["name"],
        backend=data["backend"],
        model=data["model"],
        provider=provider,
    )
    _validate(profile, source)
    return profile


def _validate(profile: AgentProfile, source: str) -> None:
    """Reject incoherent backend/provider combinations."""
    valid_backends = (*available_backends(), CODEGEN_BACKEND)
    if profile.backend not in valid_backends:
        raise SystemExit(
            f"Profile at {source} has invalid backend '{profile.backend}'. "
            f"Expected one of: {', '.join(valid_backends)}."
        )
    # The Claude Code SDK only talks to Anthropic; pairing it with another provider
    # would silently authenticate against the wrong endpoint.
    if profile.backend == "claude" and profile.provider.client_kind != "anthropic":
        raise SystemExit(
            f"Profile at {source} pairs backend 'claude' with provider "
            f"'{profile.provider.name}' (client_kind={profile.provider.client_kind}). "
            f"The claude backend requires an anthropic provider; use the openhands or "
            f"pydantic-ai backend for other providers."
        )
