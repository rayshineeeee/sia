import os
import json
import anyio
import logging

from pathlib import Path
from datetime import datetime
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

TASK = open("../private/SAMPLE_TASK_DESCRIPTIONS.md").read()
logger.info("Task loaded from task.md")

INITIAL_TARGET_AGENT_PY = open("../private/initial_target_agent.py").read()
logger.info("Initial target agent loaded")

SAMPLE_AGENT_EXECUTION = json.load(open("../private/sample_agent_execution.json"))
logger.info("Sample agent execution loaded")


PROMPT = f"""You are a meta-agent. Your task is to create a target agent which can execute a task. Go ahead and create a target_agent.py for the target agent which in turn can solve the task

Here are a couple of sample task descriptions which the target agent has to solve.
{TASK}

Here is a sample target_agent.py
{INITIAL_TARGET_AGENT_PY}

Here is a sample agent execution trajectory:
{json.dumps(SAMPLE_AGENT_EXECUTION, indent=2)}

RULES:
1. The current working directory is {Path(__file__).parent}. Create the target_agent.py in the current working directory itself
2. The target_agent.py should accept a directory path as a command-line argument in its main block. This directory should contain the data folder and task.md file.
3. The target_agent.py should log its execution trajectory to a JSON file named 'agent_execution.json'. This log should include all messages, tool calls, and their results. Use the same format as the sample agent execution trajectory provided above.
"""

async def main():
    logger.info("=" * 80)
    logger.info("Starting agent execution with Claude Haiku model")
    logger.info(f"Working directory: {Path(__file__).parent}")
    logger.info(f"Max turns: 50")
    logger.info("=" * 80)

    turn_count = 0
    start_time = datetime.now()

    try:
        async for message in query(
            prompt=PROMPT,
            options=ClaudeAgentOptions(
                cwd=f"{Path(__file__).parent}",
                allowed_tools=["Bash", "Read", "Write", "Edit", "Glob"],
                permission_mode="bypassPermissions",
                max_turns=50,
                model="haiku",
            ),
        ):
            logged_content = False

            if hasattr(message, 'content') and message.content:
                for block in message.content:
                    # Log agent text responses
                    if hasattr(block, "text") and block.text:
                        if not logged_content:
                            turn_count += 1
                            logger.info(f"\n{'─' * 80}")
                            logger.info(f"TURN {turn_count}: Agent Response")
                            logger.info(f"{'─' * 80}")
                            logged_content = True
                        logger.info(f"{block.text}")

                    # Log tool calls
                    elif hasattr(block, "name"):
                        if not logged_content:
                            turn_count += 1
                            logger.info(f"\n{'─' * 80}")
                            logger.info(f"TURN {turn_count}: Tool Execution")
                            logger.info(f"{'─' * 80}")
                            logged_content = True

                        logger.info(f"🔧 Tool: {block.name}")
                        if hasattr(block, "input") and block.input:
                            # Pretty print tool input
                            import json
                            try:
                                input_str = json.dumps(block.input, indent=2)
                                logger.info(f"   Input: {input_str}")
                            except:
                                logger.info(f"   Input: {block.input}")

                    # Log tool results
                    elif hasattr(block, "type") and block.type == "tool_result":
                        if hasattr(block, "content"):
                            result = block.content if isinstance(block.content, str) else str(block.content)
                            # Truncate very long outputs
                            if len(result) > 500:
                                result = result[:500] + f"\n... (truncated, {len(result)} total chars)"
                            logger.info(f"   ✓ Result: {result}")

            # Log final result
            if isinstance(message, ResultMessage):
                elapsed_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"\n{'=' * 80}")
                logger.info(f"EXECUTION COMPLETE")
                logger.info(f"{'=' * 80}")
                logger.info(f"Total turns: {turn_count}")
                logger.info(f"Execution time: {elapsed_time:.2f} seconds")
                logger.info(f"Final result: {message.result}")
                logger.info(f"{'=' * 80}")

    except Exception as e:
        logger.error(f"\n{'!' * 80}")
        logger.error(f"ERROR: {str(e)}")
        logger.error(f"{'!' * 80}", exc_info=True)
        raise

anyio.run(main)
