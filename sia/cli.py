"""Command-line argument parsing and resolution for the SIA orchestrator.

Extracted from orchestrator.main() so the parser and the arg→params resolution
can be tested independently. main() remains the entry point and calls into here.

Agent configuration is selected via JSON *profiles* (see sia/profiles.py): the
meta/feedback agent via ``--meta-profile`` and the target agent via ``--target-profile``.
Each value is a bundled/user profile name or a path to a ``.json`` file.
"""

from __future__ import annotations

import argparse

from sia.config import Config
from sia.layout import BUNDLED_TASKS
from sia.logging_setup import get_logger

logger = get_logger(__name__)


def build_parser(env_config: Config) -> argparse.ArgumentParser:
    """Build the orchestrator argument parser (defaults come from env_config)."""
    parser = argparse.ArgumentParser(description="Run the orchestrator for agent evolution")
    parser.add_argument(
        "--max_gen",
        type=int,
        default=env_config.DEFAULT_MAX_GENERATIONS,
        help="Maximum number of generations to run (default: 3)",
    )
    parser.add_argument("--run_id", type=int, default=1, help="Run ID for this experiment (default: 1)")
    task_group = parser.add_mutually_exclusive_group(required=True)
    task_group.add_argument(
        "--task",
        type=str,
        choices=BUNDLED_TASKS,
        help=f"Name of a bundled task shipped with sia-agent ({', '.join(BUNDLED_TASKS)})",
    )
    task_group.add_argument(
        "--task_dir",
        type=str,
        help="Path to an external task directory (e.g., ./tasks/my-task)",
    )
    parser.add_argument(
        "--meta-profile",
        dest="meta_profile",
        type=str,
        default=env_config.DEFAULT_META_PROFILE,
        help=(
            "Agent profile for the meta/feedback agent: a bundled/user profile name or a path "
            f"to a .json file (default: {env_config.DEFAULT_META_PROFILE}). A profile bundles "
            "backend + model + provider."
        ),
    )
    parser.add_argument(
        "--target-profile",
        dest="target_profile",
        type=str,
        default=env_config.DEFAULT_TARGET_PROFILE,
        help=(
            "Agent profile for the target agent: a bundled/user profile name or a path to a "
            f".json file (default: {env_config.DEFAULT_TARGET_PROFILE}). The model + provider "
            "the generated target_agent.py will call."
        ),
    )
    parser.add_argument(
        "--sandbox",
        type=str,
        default=env_config.SANDBOX_MODE,
        choices=["none", "docker"],
        help="Sandbox mode for target agent execution: none (default) or docker (requires Docker)",
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity (default: INFO, or the $SIA_LOG_LEVEL env var).",
    )
    return parser


def parse_args(env_config: Config, argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments using env_config-derived defaults."""
    return build_parser(env_config).parse_args(argv)
