"""
orchestration
    orchestrator.py
    feedback_agent.py
    meta_agent.py



tasks
    task_1
        data/public
        data/private
        task.md
    task_2
        data/public
        data/private
        task.md

# Feedback agent gives feedback on how to improve target agent
1a. The Meta Agent reads a scientific task and creates a target_agent.py in TASK_PUBLIC_DIRECTORY

LOOP START
2a. The target agent works on the task autonomously and completes it

3a. The feedback agent goes through the TASK_PUBLIC_DIRECTORY and creates feedback on how to improve the target agent and also implements the feedback.
LOOP END

runs (unique meta_agent, unique feedback_agent, unique_task, reference_target_agent and config)
    run_1 (meta_agent, task_1)
        gen_1: (meta_agent, reference_target_agent) -> target_agent_1 -> gen_1
        gen_2: (feedback_agent, target_agent_1) -> target_agent_2 -> gen_2
        gen_3: (feedback_agent, target_agent_2) -> target_agent_3 -> gen_3
    run_2 (meta_agent, task_2)
        gen_1: (meta_agent,     reference_target_agent) -> target_agent_1 -> gen_1
        gen_2: (feedback_agent, target_agent_1) -> target_agent_2 -> gen_2
        gen_3: (feedback_agent, target_agent_2) -> target_agent_3 -> gen_3
    run_3 (meta_agent_2, task_2)
        gen_1: (meta_agent,     reference_target_agent) -> target_agent_1 -> gen_1
        gen_2: (feedback_agent, target_agent_1) -> target_agent_2 -> gen_2
        gen_3: (feedback_agent, target_agent_2) -> target_agent_3 -> gen_3
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

run_id = 2
gen_num = 1
RUN_DIRECTORY = f"../runs/run_{run_id}"
META_AGENT_WORKING_DIRECTORY = f"{RUN_DIRECTORY}/gen_{gen_num}"

# Create run directory and meta_agent working directory
if os.path.exists(RUN_DIRECTORY):
    logger.error(f"Run directory already exists: {RUN_DIRECTORY}")
    logger.error("Please use a different run_id or remove the existing directory")
    sys.exit(1)

logger.info(f"Creating run directory: {RUN_DIRECTORY}")
os.makedirs(RUN_DIRECTORY, exist_ok=False)

logger.info(f"Creating meta_agent working directory: {META_AGENT_WORKING_DIRECTORY}")
os.makedirs(META_AGENT_WORKING_DIRECTORY, exist_ok=False)


META_AGENT_PROMPT = f"""You are a meta-agent. Your task is to create a target agent which can execute a task. Go ahead and create a target_agent.py for the target agent which in turn can solve the task

Here are a couple of sample task descriptions which the target agent has to solve.
{SAMPLE_TASK_DESCRIPTIONS}

Here is a sample target_agent.py
{REFERENCE_TARGET_AGENT_PY}

Here is a sample agent execution trajectory:
{json.dumps(SAMPLE_AGENT_EXECUTION, indent=2)}

RULES:
1. The current working directory is {META_AGENT_WORKING_DIRECTORY}. Create the target_agent.py in the current working directory itself
2. The target_agent.py should accept a directory path as a command-line argument in its main block. This directory should contain the data folder and task.md file.
3. The target_agent.py should log its execution trajectory to a JSON file named 'agent_execution.json'. This log should include all messages, tool calls, and their results. Use the same format as the sample agent execution trajectory provided above.
"""

asyncio.run(run_agent(model_name="haiku",
                      max_turns=10,
                      prompt=META_AGENT_PROMPT,
                      agent_working_directory=META_AGENT_WORKING_DIRECTORY))

# Create a venv file in run directory
# Run target agent and pass the working directory