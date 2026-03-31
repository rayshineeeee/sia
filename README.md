# SIA (Self-Improving Agent)

An agent scaffolding system that uses meta-learning to evolve and improve AI agents across generations.

## Overview

SIA creates AI agents that iteratively improve themselves through:
1. **Meta-Agent**: Creates initial target agents from task descriptions
2. **Target Agent**: Executes tasks and logs its performance
3. **Feedback Agent**: Analyzes execution and suggests improvements
4. **Evolution**: Each generation builds on learnings from previous iterations

## Directory Structure

```
sia/
├── orchestration/
│   ├── orchestrator.py           # Main orchestration logic
│   ├── meta_agent.py             # Meta-agent implementation
│   ├── feedback_agent.py         # Feedback agent implementation
│   └── prepare_sia_dataset.py    # Dataset preparation script
├── tasks/
│   ├── _shared/
│   │   ├── reference_target_agent.py
│   │   └── sample_agent_execution.json
│   └── {competition-id}/         # Created by prepare script
│       ├── data/
│       │   ├── public/           # Public dataset
│       │   │   ├── task.md           # Task description
│       │   │   └── *.csv             # Data files
│       │   └── private/          # Private dataset
│       └── spec/
│           ├── SAMPLE_TASK_DESCRIPTIONS.md
│           └── reference_target_agent.py
└── runs/                         # Generated during execution
    └── run_{id}/
        ├── venv/                 # Isolated Python environment
        └── gen_{n}/              # Each generation's artifacts
            ├── target_agent.py
            ├── agent_execution.json
            └── improvement.md    # (from gen_2 onwards)
```

## Setup

### Prerequisites

1. **Python 3.11+** with venv support
2. **MLE-Bench** installed:
   ```bash
   pip install mle-bench
   ```
3. **Google Generative AI** (for Gemini API):
   ```bash
   pip install google-generativeai
   ```
4. **Anthropic API key** set in environment:
   ```bash
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   ```
5. **Gemini API key** (optional, for similar task generation):
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   ```

### Installation

```bash
# Clone and navigate to the sia directory
cd /path/to/sia

# Install dependencies
pip install google-generativeai mle-bench anthropic python-dotenv
```

## Usage

### Step 1: Prepare Dataset

Use the `prepare_sia_dataset.py` script to prepare a competition dataset from MLE-Bench:

```bash
cd orchestration
python prepare_sia_dataset.py -c "spaceship-titanic"
```

This will:
1. Run `mlebench prepare -c "spaceship-titanic"`
2. Copy public and private datasets from `~/.cache/mle-bench/data/prepared/`
3. Rename `description.md` to `task.md` in `data/public/`
4. Use Gemini to generate similar tasks (optional)
5. Create `SAMPLE_TASK_DESCRIPTIONS.md` in `spec/`
6. Copy `reference_target_agent.py` from `_shared/` to `spec/`

**Options:**
- `--skip-gemini`: Skip Gemini API call for similar tasks
- `--tasks-dir PATH`: Specify custom tasks directory (default: `./tasks`)

**Example with custom directory:**
```bash
python prepare_sia_dataset.py -c "house-prices-advanced-regression-techniques" --tasks-dir /path/to/tasks
```

**Skip Gemini (faster, no API call):**
```bash
python prepare_sia_dataset.py -c "spaceship-titanic" --skip-gemini
```

### Step 2: Run the Orchestrator

**IMPORTANT:** Always run the orchestrator from the `orchestration/` directory because it uses relative paths like `./tasks` and `./runs`.

```bash
cd orchestration
python orchestrator.py --task_dir ./tasks/spaceship-titanic --max_gen 3 --run_id 1
```

**Arguments:**
- `--task_dir`: Path to the task directory (e.g., `./tasks/spaceship-titanic`)
- `--max_gen`: Number of generations to evolve (default: 3)
- `--run_id`: Unique identifier for this run (default: 1)

**What happens during execution:**

1. **Generation 1:**
   - Meta-agent reads task and creates initial `target_agent.py`
   - Target agent executes task and logs to `agent_execution.json`
   - Feedback agent analyzes and creates improved agent for Gen 2

2. **Generation 2-N:**
   - Target agent from previous generation executes task
   - Feedback agent analyzes and creates next generation
   - Continues until `max_gen` is reached

3. **Output:**
   - All artifacts saved in `runs/run_{run_id}/gen_{n}/`
   - Each generation has its own `target_agent.py` and execution logs
   - Improvement notes in `improvement.md`

### Step 3: Analyze Results

```bash
# View execution logs
cat runs/run_1/gen_1/agent_execution.json

# View improvements made
cat runs/run_1/gen_2/improvement.md

# Compare agent versions
diff runs/run_1/gen_1/target_agent.py runs/run_1/gen_2/target_agent.py
```

## Example Workflow

```bash
# 1. Prepare dataset for a Kaggle competition
cd orchestration
python prepare_sia_dataset.py -c "spaceship-titanic"

# 2. Verify the dataset structure
ls -R ../tasks/spaceship-titanic/

# 3. Run orchestrator for 3 generations
python orchestrator.py --task_dir ./tasks/spaceship-titanic --max_gen 3 --run_id 1

# 4. Check results
ls -R ../runs/run_1/
cat ../runs/run_1/gen_3/agent_execution.json
```

## Task Requirements

Each task directory must follow this structure:

```
tasks/{competition-id}/
├── data/
│   ├── public/
│   │   ├── task.md                    # Task description (orchestrator reads this)
│   │   ├── train.csv
│   │   ├── test.csv
│   │   └── sample_submission.csv
│   └── private/
│       └── ...                        # Private evaluation data
└── spec/
    ├── SAMPLE_TASK_DESCRIPTIONS.md    # Similar tasks (for meta-agent context)
    └── reference_target_agent.py      # Template agent structure
```

### Creating Custom Tasks

If you want to add a custom task (not from MLE-Bench):

1. Create the directory structure manually:
   ```bash
   mkdir -p tasks/my-custom-task/{data/public,data/private,spec}
   ```

2. Add your datasets:
   ```bash
   cp train.csv test.csv tasks/my-custom-task/data/public/
   cp ground_truth.csv tasks/my-custom-task/data/private/
   ```

3. Write task description:
   ```bash
   # Create task.md in data/public/
   cat > tasks/my-custom-task/data/public/task.md << 'EOF'
   # Task Description

   Your task description here...
   EOF
   ```

4. Copy templates:
   ```bash
   cp tasks/_shared/reference_target_agent.py tasks/my-custom-task/spec/
   ```

5. Optionally create `SAMPLE_TASK_DESCRIPTIONS.md` manually in `spec/`

## Troubleshooting

### "Run directory already exists"
The orchestrator prevents overwriting existing runs. Either:
- Use a different `--run_id`
- Delete the existing run: `rm -rf runs/run_1`

### "No GEMINI_API_KEY environment variable set"
The prepare script will skip similar task generation. Either:
- Set the environment variable: `export GEMINI_API_KEY="your-key"`
- Use `--skip-gemini` flag to skip this step

### "Reference agent not found at tasks/_shared/reference_target_agent.py"
Create the `_shared` directory and add template files:
```bash
mkdir -p tasks/_shared
# Copy your reference agent and sample execution JSON to this directory
```

### Target agent fails during execution
Check the logs in the generation directory:
```bash
cat runs/run_1/gen_1/agent_execution.json
```

Common issues:
- Dataset paths incorrect (ensure absolute paths are used)
- Missing Python packages in the venv
- ANTHROPIC_API_KEY not set

### ImportError: No module named 'anthropic'
The orchestrator creates a fresh venv for each run. If packages are missing:
1. Check the venv creation in the orchestrator logs
2. Manually install: `runs/run_1/venv/bin/pip install anthropic`

## Configuration

### Model Selection

The default model is `haiku` (claude-haiku-4-5-20251001). To use a different model:

1. Edit `orchestrator.py`:
   ```python
   asyncio.run(run_agent(
       model_name="sonnet",  # Change here
       max_turns="20",
       prompt=META_AGENT_PROMPT,
       agent_working_directory=META_AGENT_WORKING_DIRECTORY
   ))
   ```

2. Update the META_AGENT_PROMPT to specify the model for target agents

### Customizing Prompts

Edit the prompts in `orchestrator.py`:
- `META_AGENT_PROMPT`: Controls how the initial agent is created
- `FEEDBACK_AGENT_PROMPT`: Controls how improvements are suggested

## Development

### Running Tests

```bash
# Test dataset preparation
python prepare_sia_dataset.py -c "spaceship-titanic" --skip-gemini

# Test orchestrator with 1 generation
python orchestrator.py --task_dir ./tasks/spaceship-titanic --max_gen 1 --run_id test
```

### Debugging

Enable verbose logging:
```python
# In orchestrator.py
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

## FAQ

**Q: Can I run multiple experiments in parallel?**
A: Yes, use different `--run_id` values for each experiment.

**Q: How do I use a different competition?**
A: Just run `prepare_sia_dataset.py -c "competition-name"` with any MLE-Bench competition ID.

**Q: Can I modify the target agent manually between generations?**
A: Yes, but it defeats the purpose of self-improvement. The system is designed to evolve autonomously.

**Q: What if the meta-agent creates a broken target agent?**
A: The feedback agent should identify issues and fix them in the next generation. If not, you may need to adjust the prompts or provide better examples.

**Q: How much does it cost to run?**
A: Depends on the model and task complexity. Using `haiku` (cheapest) for 3 generations typically costs $0.10-0.50 per run.

## Contributing

When adding new features:
1. Test with a simple competition first (e.g., spaceship-titanic)
2. Ensure the directory structure is preserved
3. Update this README with new functionality

## License

See repository root for license information.
