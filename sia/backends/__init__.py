"""Agent-backend registry package.

Importing this package registers all built-in backends (claude, openhands,
pydantic-ai) without importing their optional SDKs.
"""

# Import backend modules for their registration side effects.
from sia.backends import claude, openhands, pydantic_ai  # noqa: F401  (registers backends)
from sia.backends.base import available_backends, get_backend, register, run_agent

__all__ = ["available_backends", "get_backend", "register", "run_agent"]
