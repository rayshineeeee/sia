import os
import logging
import anyio
from datetime import datetime
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

if os.path.exists('train.py'):
    logger.info("Removing existing train.py file")
    os.remove('train.py')

TASK = open("task.md").read()
logger.info("Task loaded from task.md")

PROMPT = f"""You are a software engineering agent. Your job is to solve the following ML task by iterating on train.py.

{TASK}

Work inside /home/ubuntu/sia/task_1/public. Use the virtual environment at .venv (activate with `source .venv/bin/activate`).

Steps:
1. Read the data files to understand the data.
2. Create or improve train.py to train a model and report validation/test metrics.
3. Iterate: run train.py, observe metrics, improve the model, repeat until metrics are good.
4. Report the final metrics in the required format.
"""

async def main():
    logger.info("=" * 80)
    logger.info("Starting agent execution with Claude Haiku model")
    logger.info(f"Working directory: /home/ubuntu/product/prod_scale/hades/test-agents/agent-scaffolds/agents/sia/task_1/public")
    logger.info(f"Max turns: 50")
    logger.info("=" * 80)

    turn_count = 0
    start_time = datetime.now()

    try:
        async for message in query(
            prompt=PROMPT,
            options=ClaudeAgentOptions(
                cwd="/home/ubuntu/product/prod_scale/hades/test-agents/agent-scaffolds/agents/sia/task_1/public",
                allowed_tools=["Bash", "Read", "Write", "Edit", "Glob"],
                permission_mode="bypassPermissions",
                max_turns=50,
                model="haiku",
            ),
        ):
            # Track if we logged anything for this message
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
