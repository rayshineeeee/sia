import os
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

if os.path.exists('train.py'):
    os.remove('train.py')
TASK = open("task.md").read()

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
    turn_count = 0
    async for message in query(
        prompt=PROMPT,
        options=ClaudeAgentOptions(
            cwd="/home/ubuntu/sia/task_1/public",
            allowed_tools=["Bash", "Read", "Write", "Edit", "Glob"],
            permission_mode="bypassPermissions",
            max_turns=50,
        ),
    ):
        if hasattr(message, 'content'):
            turn_count += 1
            for block in message.content:
                if hasattr(block, "text"):
                    print(f"\nClaude at count {turn_count} says:\n{block.text}")
                elif hasattr(block, "name"):
                    print(f"\nAt count {turn_count} using tool: {block.name}")
        if isinstance(message, ResultMessage):
            print(f"\nFinal Result at count {turn_count}: {message.result}")

anyio.run(main)
