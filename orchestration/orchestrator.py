"""
Directory structure (conceptual)

orchestration/
  orchestrator.py
  feedback_agent.py
  meta_agent.py

tasks/
  task_1/
    spec/
      reference_target_agent.py
      SAMPLE_TASK_DESCRIPTIONS.md
    data/
      public/
      private/
    task.md
  task_2/
    spec/
      reference_target_agent.py
      SAMPLE_TASK_DESCRIPTIONS.md
    data/
      public/
      private/
    task.md

tasks/_shared/                 # cross-task examples/templates (public)
  sample_agent_execution.json

runs/
  run_1/ (unique meta_agent, unique feedback_agent, unique_task, reference_target_agent, config)
    gen_1: (meta_agent, reference_target_agent) -> target_agent_1 -> gen_1
    gen_2: (feedback_agent, target_agent_1) -> target_agent_2 -> gen_2
    gen_3: (feedback_agent, target_agent_2) -> target_agent_3 -> gen_3
  run_2/ (meta_agent, task_2)
    gen_1: (meta_agent, reference_target_agent) -> target_agent_1 -> gen_1
    gen_2: (feedback_agent, target_agent_1) -> target_agent_2 -> gen_2
    gen_3: (feedback_agent, target_agent_2) -> target_agent_3 -> gen_3
  run_3/ (meta_agent_2, task_2)
    gen_1: (meta_agent, reference_target_agent) -> target_agent_1 -> gen_1
    gen_2: (feedback_agent, target_agent_1) -> target_agent_2 -> gen_2
    gen_3: (feedback_agent, target_agent_2) -> target_agent_3 -> gen_3

Workflow
- Feedback agent gives feedback on how to improve the target agent.
- 1a. The Meta Agent reads a scientific task and creates a `target_agent.py` in `TASK_PUBLIC_DIRECTORY`.

LOOP START
- 2a. The target agent works on the task autonomously and completes it.
- 3a. The feedback agent goes through `TASK_PUBLIC_DIRECTORY`, creates feedback on how to improve the target agent,
      and applies the feedback.
LOOP END
"""

import os
import sys
import json
import asyncio
import logging

from meta_agent import run_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

SAMPLE_TASK_DESCRIPTIONS = open("../tasks/task_1/private/SAMPLE_TASK_DESCRIPTIONS.md").read()
logger.info("Task loaded from task.md")

REFERENCE_TARGET_AGENT_PY = open("../tasks/task_1/private/reference_target_agent.py").read()
logger.info("Initial target agent loaded")

SAMPLE_AGENT_EXECUTION = json.load(open("../tasks/task_1/private/sample_agent_execution.json"))
logger.info("Sample agent execution loaded")

run_id = 1
gen_num = 1
RUN_DIRECTORY = f"../runs/run_{run_id}"
META_AGENT_WORKING_DIRECTORY = os.path.abspath(f"{RUN_DIRECTORY}/gen_{gen_num}")
FEEDBACK_AGENT_WORKING_DIRECTORY = META_AGENT_WORKING_DIRECTORY


# Create run directory and meta_agent working directory
if os.path.exists(RUN_DIRECTORY):
    logger.error(f"Run directory already exists: {RUN_DIRECTORY}")
    logger.error("Please use a different run_id or remove the existing directory")
    sys.exit(1)

logger.info(f"Creating run directory: {RUN_DIRECTORY}")
os.makedirs(RUN_DIRECTORY, exist_ok=False)

logger.info(f"Creating meta_agent working directory: {META_AGENT_WORKING_DIRECTORY}")
os.makedirs(META_AGENT_WORKING_DIRECTORY, exist_ok=False)


META_AGENT_PROMPT = f"""You are a meta-agent. Your task is to create a target agent which can execute a task. Go ahead and create a target_agent.py for the target agent, which in turn can solve the given task.

Here are a couple of sample task descriptions which the target agent has to solve:
{SAMPLE_TASK_DESCRIPTIONS}

Here is a sample target_agent.py:
{REFERENCE_TARGET_AGENT_PY}

Here is a sample agent execution trajectory:
{json.dumps(SAMPLE_AGENT_EXECUTION, indent=2)}

RULES:
1. The current working directory is {META_AGENT_WORKING_DIRECTORY}. Create the target_agent.py in the current working directory itself.
2. The target_agent.py must accept two command-line arguments: --dataset_dir (the absolute path to the dataset directory, which is strictly read-only), and --working_dir (the absolute path to the directory where the agent can write files, such as python scripts or execution logs).
3. The target agent can only read from the dataset directory provided via --dataset_dir, and can write only in the runs directory specified by --working_dir.
4. The target_agent.py should log its execution trajectory to a JSON file named 'agent_execution.json' in its working directory. This log should include all messages, tool calls, and their results. Use the same format as the sample agent execution trajectory provided above.
5. Do not attempt to write to or modify files inside the dataset directory.
6. The target_agent.py should use only the "haiku" or "claude-haiku-4-5-20251001" model from Anthropic/Claude when invoking the language model (do not use any other model).

Example invocation:
    python target_agent.py --dataset_dir {os.path.abspath('../datadd')} --working_dir {os.path.abspath(META_AGENT_WORKING_DIRECTORY)}
"""

FEEDBACK_AGENT_PROMPT = """You are an expert AI Engineer. Your task is to analyze an agent scaffold and its execution logs to suggest improvements to the scaffold.

Here are a couple of sample task descriptions which the agent is designed to solve.
```
{SAMPLE_TASK_DESCRIPTIONS}
```

Here is a target_agent.py which you created earlier
```
{AGENT_PY}
```

Here is the task which you worked on:
```
{TASK}
```

Here is the agent execution trajectory:
```
{AGENT_EXECUTION}
```

Your task is to analyze the target_agent.py and identify improvements that could be made to it. 

RULES:
- Focus on the structure, approach, and methodology of the target agent itself
- Do NOT optimize for the specific task shown above
- Instead, think about how to make the target agent more robust and generalizable across the variety of tasks shown in the sample task descriptions
- Consider improvements to reasoning strategies, and overall agent architecture
- Provide thoughtful recommendations for enhancing the target agent's capabilities across diverse tasks.
- Consolidate all the improvements and write them to improvement.md in the current working directory: {IMPROVEMENT_DIR}
- Once you have written improvement.md, go ahead and implement the improvements ONLY in target_agent.py. Do not create or modify any other files.
"""



# ========================
# SECTION 1: Create Virtual Environment
# ========================

import venv
import subprocess

venv_dir = os.path.join(RUN_DIRECTORY, "venv")
logger.info(f"Creating virtual environment at: {venv_dir}")
venv.create(venv_dir, with_pip=True)

# Path to the pip executable inside the venv
pip_executable = os.path.join(venv_dir, "bin", "pip")

# Install required packages: anthropic, python-dotenv
logger.info("Installing required packages: anthropic, python-dotenv in the virtual environment")
subprocess.run([pip_executable, "install", "anthropic", "python-dotenv"], check=True)


# ========================
# SECTION 2: Run Target Agent Creation (Meta-Agent)
# ========================

asyncio.run(run_agent(
    model_name="haiku",
    max_turns="20",
    prompt=META_AGENT_PROMPT,
    agent_working_directory=META_AGENT_WORKING_DIRECTORY
))


# ========================
# SECTION 3: Run Target Agent
# ========================

# Define the dataset directory and working directory to pass as arguments
DATASET_DIRECTORY = "../tasks/task_1/public/data"  # Adjust as needed, or make configurable
ABS_DATASET_DIRECTORY = os.path.abspath(DATASET_DIRECTORY)

target_agent_path = os.path.join(FEEDBACK_AGENT_WORKING_DIRECTORY, "target_agent.py")

logger.info(f"Running target agent: {target_agent_path}")

subprocess.run([
    os.path.join(venv_dir, "bin", "python"),
    target_agent_path,
    "--dataset_dir", ABS_DATASET_DIRECTORY,
    "--working_dir", FEEDBACK_AGENT_WORKING_DIRECTORY
], check=True)


# ========================
# SECTION 4: Run Feedback Agent
# ========================

from pathlib import Path

# Load artifacts produced by the target agent so the feedback prompt is fully populated.
AGENT_PY = Path(FEEDBACK_AGENT_WORKING_DIRECTORY, "target_agent.py").read_text(encoding="utf-8")
TASK = Path(DATASET_DIRECTORY, "task.md").read_text(encoding="utf-8")
with open(Path(FEEDBACK_AGENT_WORKING_DIRECTORY, "agent_execution.json"), "r", encoding="utf-8") as f:
    AGENT_EXECUTION = json.load(f)

AGENT_EXECUTION_PRETTY = json.dumps(AGENT_EXECUTION, indent=2)

gen_num += 1
FEEDBACK_AGENT_WORKING_DIRECTORY = os.path.abspath(f"{RUN_DIRECTORY}/gen_{gen_num}")

# call feedback agent
feedback_agent_prompt_prepared = FEEDBACK_AGENT_PROMPT.format(
    SAMPLE_TASK_DESCRIPTIONS=SAMPLE_TASK_DESCRIPTIONS,
    AGENT_PY=AGENT_PY,
    TASK=TASK,
    AGENT_EXECUTION=AGENT_EXECUTION_PRETTY,
    IMPROVEMENT_DIR=FEEDBACK_AGENT_WORKING_DIRECTORY,
)

os.makedirs(FEEDBACK_AGENT_WORKING_DIRECTORY, exist_ok=True)
asyncio.run(
    run_agent(
        model_name="haiku",
        max_turns="20",
        prompt=feedback_agent_prompt_prepared,
        agent_working_directory=FEEDBACK_AGENT_WORKING_DIRECTORY,
    )
)
