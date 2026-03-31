"""

orchestration
    orchestrator.py
    feedback_agent.py
    meta_agent.py

agents 
    target_agent.py
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
1b. Git commit

LOOP START
2a. The target agent works on the task autonomously and completes it
2b. Git commit

3a. The feedback agent goes through the TASK_PUBLIC_DIRECTORY and creates feedback on how to improve the target agent and also implements the feedback.
3b. Git commit
LOOP END

runs (unique meta_agent and unique feedback_agent and unique_task and config)
    run_1 (meta_agent, task_1)
        gen_1: (meta_agent,     initial_target) -> target_agent_1 -> gen_1
        gen_2: (feedback_agent, target_agent_1) -> target_agent_2 -> gen_2
        gen_3: (feedback_agent, target_agent_2) -> target_agent_3 -> gen_3
    run_2 (meta_agent, task_2)
        gen_1: (meta_agent,     initial_target) -> target_agent_1 -> gen_1
        gen_2: (feedback_agent, target_agent_1) -> target_agent_2 -> gen_2
        gen_3: (feedback_agent, target_agent_2) -> target_agent_3 -> gen_3
    run_3 (meta_agent_2, task_2)
        gen_1: (meta_agent,     initial_target) -> target_agent_1 -> gen_1
        gen_2: (feedback_agent, target_agent_1) -> target_agent_2 -> gen_2
        gen_3: (feedback_agent, target_agent_2) -> target_agent_3 -> gen_3
"""

