import logging

from datetime import datetime
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def run_agent(model_name, max_turns, prompt, agent_working_directory):
    logger.info("=" * 80)
    logger.info(f"Starting agent execution with {model_name} model")
    logger.info(f"Working directory: {agent_working_directory}")
    logger.info(f"Max turns: {max_turns}")
    logger.info("=" * 80)

    turn_count = 0
    start_time = datetime.now()

    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                cwd=agent_working_directory,
                allowed_tools=["Bash", "Read", "Write", "Edit", "Glob"],
                permission_mode="bypassPermissions",
                max_turns=max_turns,
                model=model_name,
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
