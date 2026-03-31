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


SAMPLE_TASKS = open("../private/SAMPLE_TASK_DESCRIPTIONS.md").read()
logger.info("Task loaded from SAMPLE_TASK_DESCRIPTIONS.md")

AGENT_PY = open("../target_public/target_agent.py").read()
logger.info("Target agent loaded")

AGENT_EXECUTION = json.load(open("../public/agent_execution.json"))
logger.info("Sample agent execution loaded")

TASK = open("../public/task.md").read()
logger.info("Task loaded from task.md")

PROMPT = f"""You are an expert AI Engineer. Your task is to analyze an agent scaffold and its execution logs to suggest improvements to the scaffold.

Here are a couple of sample task descriptions which the agent is designed to solve.
```
{SAMPLE_TASKS}
```
Here is a agent.py which you created earlier
```
{AGENT_PY}
```
Here is the task which you worked on:
```
{TASK}
```
Here is the agent execution trajectory:
```
{json.dumps(AGENT_EXECUTION, indent=2)}
```
Your task is to analyze the agent.py and identify improvements that could be made to it. 

RULES:
- Focus on the structure, approach, and methodology of the target agent itself
- Do NOT optimize for the specific task shown above
- Instead, think about how to make the target agent more robust and generalizable across the variety of tasks shown in the sample task descriptions
- Consider improvements to reasoning strategies, and overall agent architecture
- Provide thoughtful recommendations for enhancing the target agent's capabilities across diverse tasks.
- Consolidate all the improvements and write it to improvement.md in the current working directory: {Path(__file__).parent}
- Once you have written improvement.md , go ahead and implement the improvements to the agent in ../target_public/target_agent.py
"""

async def main():
    logger.info("=" * 80)
    logger.info("Starting agent execution with Claude Haiku model")
    logger.info(f"Working directory: {Path(__file__).parent}")
    logger.info(f"Max turns: 50")
    logger.info("=" * 80)

    turn_count = 0
    start_time = datetime.now()
    
    # Save the prompt to prompt.md for reference
    prompt_path = Path(__file__).parent / "prompt.md"
    logger.info(f"Saving prompt to {prompt_path}")
    with open(prompt_path, 'w') as f:
        f.write(PROMPT)
    logger.info("Prompt saved successfully")
    
    return

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
