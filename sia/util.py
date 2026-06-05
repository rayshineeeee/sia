"""Backward-compatible shim.

Agent backends moved to the ``sia.backends`` package. This module is kept so
existing imports (``from sia.util import run_agent``) continue to work.
"""

from sia.backends import available_backends, get_backend, run_agent

__all__ = ["available_backends", "get_backend", "run_agent"]
