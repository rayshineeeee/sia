"""Run/task setup: load task reference files and create the run directory.

Hosts the TaskFiles/RunSetup containers and the filesystem-prep helpers previously
defined in orchestrator.py (re-exported there for the existing test contract).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import venv
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from sia.config import Config
from sia.context_manager import ContextManager
from sia.layout import RunLayout, TaskLayout, venv_pip_path, venv_python_path
from sia.logging_setup import get_logger

if TYPE_CHECKING:
    from sia.agent_reference import ResolvedAgentReference

logger = get_logger(__name__)


@dataclass
class TaskFiles:
    """Container for task reference files loaded from disk."""

    sample_task_descriptions: str
    reference_target_agent_py: str
    sample_agent_execution: dict
    task_md: str


@dataclass
class RunSetup:
    """Container for run directory paths and managers."""

    run_directory: str
    meta_agent_working_directory: str
    venv_dir: str
    context_mgr: ContextManager


def load_task_files(
    task_dir: str,
    shared_dir: str,
    resolved_ref: ResolvedAgentReference | None = None,
) -> TaskFiles:
    """Load all reference files from the task directory.

    The seed shown to the meta-agent comes from ``resolved_ref`` (the target profile's
    agent_reference) when provided: its ``inline_seed`` for a default/single-file
    reference, or empty for a multi-file directory reference (the agent reads that from
    disk). When ``resolved_ref`` is None, fall back to the task's bundled reference.
    """
    logger.info("Loading files from task directory...")
    paths = TaskLayout(task_dir, shared_dir)

    sample_task_descriptions = Path(paths.sample_descriptions).read_text()
    logger.info("  ✓ Sample task descriptions loaded")

    if resolved_ref is None:
        reference_target_agent_py = Path(paths.reference_agent).read_text()
    else:
        reference_target_agent_py = resolved_ref.inline_seed or ""
    logger.info("  ✓ Reference target agent loaded")

    with open(paths.sample_execution) as f:
        sample_agent_execution = json.load(f)
    logger.info("  ✓ Sample agent execution loaded")

    task_md = Path(paths.task_md).read_text()
    logger.info("  ✓ Task specification loaded")

    return TaskFiles(
        sample_task_descriptions=sample_task_descriptions,
        reference_target_agent_py=reference_target_agent_py,
        sample_agent_execution=sample_agent_execution,
        task_md=task_md,
    )


def _create_venv(venv_dir: str, packages: list[str]) -> None:
    """Create a virtual environment and install packages."""
    if shutil.which("uv"):
        subprocess.run(["uv", "venv", venv_dir], check=True)
        subprocess.run(
            ["uv", "pip", "install", "--python", venv_python_path(venv_dir), *packages],
            check=True,
        )
    else:
        venv.create(venv_dir, with_pip=True)
        subprocess.run([venv_pip_path(venv_dir), "install", *packages], check=True)


def install_requirements(venv_dir: str, requirements_path: str) -> None:
    """Install a requirements.txt into an existing venv (augmenting the baseline packages).

    Used per generation so the meta/feedback agents can evolve the target's
    dependencies by editing requirements.txt across generations.
    """
    if shutil.which("uv"):
        cmd = ["uv", "pip", "install", "--python", venv_python_path(venv_dir), "-r", requirements_path]
    else:
        cmd = [venv_pip_path(venv_dir), "install", "-r", requirements_path]
    logger.info(f"Installing generation dependencies from {requirements_path}")
    subprocess.run(cmd, check=True)


def setup_run_directory(
    run_id: int,
    task_dir: str,
    meta_model: str,
    task_model: str,
    agent_impl: str,
    max_gen: int,
    config: Config | None = None,
) -> RunSetup:
    """Create run directories, venv, and context manager."""
    cfg = config or Config()
    layout = RunLayout.for_run_id(run_id)
    run_directory = layout.run_dir
    meta_agent_working_directory = layout.gen_dir(1)

    if os.path.exists(run_directory):
        logger.error(f"Run directory already exists: {run_directory}")
        logger.error("Please use a different run_id or remove the existing directory")
        sys.exit(1)

    logger.info(f"Creating run directory: {run_directory}")
    os.makedirs(run_directory, exist_ok=False)

    logger.info(f"Creating meta_agent working directory: {meta_agent_working_directory}")
    os.makedirs(meta_agent_working_directory, exist_ok=False)

    venv_dir = layout.venv_dir
    logger.info(f"Creating virtual environment at: {venv_dir}")
    _create_venv(venv_dir, cfg.VENV_PACKAGES)

    logger.info("Initializing context manager...")
    context_mgr = ContextManager(
        run_directory,
        {
            "task_dir": task_dir,
            "meta_model": meta_model,
            "task_model": task_model,
            "agent_impl": agent_impl,
            "max_gen": max_gen,
        },
    )
    context_mgr.initialize()
    logger.info("  ✓ Context manager initialized")

    return RunSetup(
        run_directory=run_directory,
        meta_agent_working_directory=meta_agent_working_directory,
        venv_dir=venv_dir,
        context_mgr=context_mgr,
    )
