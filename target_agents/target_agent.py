#!/usr/bin/env python
"""
Enhanced ML Agent with improved architecture for diverse ML tasks.

Key improvements:
1. Task-aware strategy based on detected task type
2. Structured experiment tracking to prevent redundant work
3. Convergence monitoring for early stopping
4. Data profiling for informed model selection
5. Error recovery and constraint validation
6. Results summarization and comparison
"""

import anthropic
import subprocess
import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import csv
from collections import defaultdict

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"

# ──────────────────────────────────────────────────────────────────────────────
# TASK ANALYSIS MODULE
# ──────────────────────────────────────────────────────────────────────────────

class TaskAnalyzer:
    """Analyzes task description and detects task type and characteristics."""

    TASK_KEYWORDS = {
        'regression': ['predict', 'forecast', 'loss', 'mse', 'rmse', 'mae', 'r2'],
        'classification': ['classify', 'predict', 'accuracy', 'f1', 'precision', 'recall',
                          'auc', 'auroc', 'roc', 'label', 'class'],
        'binary_classification': ['binary', 'positive', 'negative', '0 or 1', 'true or false'],
        'multiclass': ['multiclass', 'multi-class', 'several classes', 'multiple classes',
                      'macro_f1', 'macro f1'],
        'ranking': ['rank', 'mrr', 'ndcg', 'relevance', 'learning-to-rank'],
        'rare_event': ['rare', 'imbalance', 'auroc', 'average precision', 'ap', 'event'],
    }

    @staticmethod
    def detect_task_type(task_description: str) -> Dict:
        """Detect task type from task description."""
        text_lower = task_description.lower()

        task_scores = defaultdict(int)
        for task_type, keywords in TaskAnalyzer.TASK_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    task_scores[task_type] += 1

        # Special rules for rare event detection
        if 'rare' in text_lower or 'imbalance' in text_lower or 'calibration' in text_lower:
            task_scores['rare_event'] += 3

        if task_scores:
            detected_type = max(task_scores, key=task_scores.get)
        else:
            detected_type = 'regression'  # default

        # Extract metrics
        metrics = TaskAnalyzer._extract_metrics(task_description)

        # Check for special characteristics
        has_class_imbalance = 'imbalance' in text_lower or 'rare' in text_lower
        requires_calibration = 'calibration' in text_lower

        return {
            'task_type': detected_type,
            'metrics': metrics,
            'has_class_imbalance': has_class_imbalance,
            'requires_calibration': requires_calibration,
            'confidence': task_scores.get(detected_type, 1) / max(sum(task_scores.values()), 1)
        }

    @staticmethod
    def _extract_metrics(text: str) -> List[str]:
        """Extract metric names from text."""
        metrics = []
        metric_patterns = [
            'accuracy', 'f1', 'precision', 'recall', 'auc', 'auroc', 'roc',
            'mse', 'rmse', 'mae', 'loss', 'r2', 'mrr', 'ndcg', 'ap',
            'average precision', 'mean squared error', 'mean absolute error'
        ]
        text_lower = text.lower()
        for metric in metric_patterns:
            if metric in text_lower:
                metrics.append(metric)
        return metrics

    @staticmethod
    def get_task_specific_guidance(task_type: str) -> str:
        """Get task-specific guidance for the agent."""
        guidance = {
            'regression': """
REGRESSION TASK:
- Focus on reducing loss (MSE/MAE) and maximizing R²
- Consider polynomial regression, tree-based methods, neural networks
- Handle outliers carefully as they impact MSE significantly
- Use appropriate scaling for neural networks
- Try ensemble methods if single models plateau
""",
            'classification': """
CLASSIFICATION TASK:
- Optimize for accuracy and F1 score
- Handle class distribution carefully
- Consider decision thresholds, not just raw predictions
- Logistic regression, tree-based, SVM are good baselines
- Watch for overfitting on validation set
""",
            'binary_classification': """
BINARY CLASSIFICATION TASK:
- Optimize for precision, recall, and F1
- Consider probability calibration
- Use appropriate class weights if imbalanced
- Logistic regression is strong baseline
- ROC-AUC captures performance across thresholds
""",
            'multiclass': """
MULTICLASS CLASSIFICATION TASK:
- Optimize for accuracy and macro F1
- Macro F1 gives equal weight to all classes
- One-vs-rest or softmax approaches
- Tree-based methods often work well
- Handle class imbalance if present
""",
            'ranking': """
RANKING/LEARNING-TO-RANK TASK:
- Optimize for NDCG (normalized discounted cumulative gain)
- MRR (mean reciprocal rank) measures top-1 accuracy
- Consider query-document pair structure
- Specialized ranking algorithms (LambdaMART, ListNet) can help
- Pairwise learning approaches often outperform pointwise
""",
            'rare_event': """
RARE EVENT PREDICTION TASK:
- Focus on AUROC and Average Precision for imbalanced data
- Class imbalance is critical - use appropriate weighting/resampling
- Probability calibration is important
- Threshold optimization is crucial
- Consider SMOTE or other resampling strategies
- Don't use accuracy as primary metric
"""
        }
        return guidance.get(task_type, "")


# ──────────────────────────────────────────────────────────────────────────────
# EXPERIMENT TRACKING MODULE
# ──────────────────────────────────────────────────────────────────────────────

class ExperimentTracker:
    """Tracks all experiments to prevent redundant work and enable comparison."""

    def __init__(self, task_dir: str):
        self.task_dir = task_dir
        self.experiments_file = os.path.join(task_dir, "experiments.jsonl")
        self.best_results_file = os.path.join(task_dir, "best_results.json")
        self.experiments = []
        self._load_existing_experiments()

    def _load_existing_experiments(self):
        """Load experiments from previous runs."""
        if os.path.exists(self.experiments_file):
            try:
                with open(self.experiments_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            self.experiments.append(json.loads(line))
            except Exception:
                pass

    def log_experiment(self, model_type: str, hyperparameters: Dict,
                      val_metrics: Dict, test_metrics: Dict = None,
                      training_time: float = 0, iteration: int = 0) -> None:
        """Log an experiment result."""
        experiment = {
            'timestamp': datetime.now().isoformat(),
            'iteration': iteration,
            'model_type': model_type,
            'hyperparameters': hyperparameters,
            'val_metrics': val_metrics,
            'test_metrics': test_metrics or {},
            'training_time': training_time
        }
        self.experiments.append(experiment)

        # Append to file (JSONL format)
        try:
            with open(self.experiments_file, 'a') as f:
                f.write(json.dumps(experiment) + '\n')
        except Exception as e:
            print(f"Warning: Could not log experiment: {e}")

    def get_best_by_metric(self, metric: str, on_test: bool = False) -> Optional[Dict]:
        """Get best experiment by metric."""
        if not self.experiments:
            return None

        dataset = 'test_metrics' if on_test else 'val_metrics'
        valid_exps = [e for e in self.experiments if metric in e.get(dataset, {})]

        if not valid_exps:
            return None

        # Determine if metric should be maximized or minimized
        if metric in ['loss', 'mse', 'mae', 'rmse']:
            best = min(valid_exps, key=lambda e: e[dataset][metric])
        else:  # r2, accuracy, f1, auroc, ap, ndcg, mrr
            best = max(valid_exps, key=lambda e: e[dataset][metric])

        return best

    def has_tried_config(self, model_type: str, hyperparameters: Dict) -> bool:
        """Check if this config has been tried before."""
        for exp in self.experiments:
            if exp['model_type'] == model_type:
                if exp['hyperparameters'] == hyperparameters:
                    return True
        return False

    def get_top_models(self, metric: str, k: int = 5, on_test: bool = False) -> List[Dict]:
        """Get top K models by metric."""
        if not self.experiments:
            return []

        dataset = 'test_metrics' if on_test else 'val_metrics'
        valid_exps = [e for e in self.experiments if metric in e.get(dataset, {})]

        if metric in ['loss', 'mse', 'mae', 'rmse']:
            sorted_exps = sorted(valid_exps, key=lambda e: e[dataset][metric])
        else:
            sorted_exps = sorted(valid_exps, key=lambda e: e[dataset][metric], reverse=True)

        return sorted_exps[:k]

    def get_summary(self) -> str:
        """Get summary of experiments for the agent."""
        if not self.experiments:
            return "No experiments logged yet."

        # Group by model type
        by_model = defaultdict(list)
        for exp in self.experiments:
            by_model[exp['model_type']].append(exp)

        summary = f"Experiments Run: {len(self.experiments)}\n"
        summary += f"Models Tried: {len(by_model)}\n\n"

        for model_type in sorted(by_model.keys()):
            exps = by_model[model_type]
            summary += f"{model_type}: {len(exps)} experiments\n"

            if exps:
                best = exps[0]
                if 'val_metrics' in best:
                    summary += f"  Best validation metrics: {best['val_metrics']}\n"

        return summary


# ──────────────────────────────────────────────────────────────────────────────
# CONVERGENCE MONITORING MODULE
# ──────────────────────────────────────────────────────────────────────────────

class ConvergenceMonitor:
    """Monitors for convergence and suggests early stopping."""

    def __init__(self, window_size: int = 5, improvement_threshold: float = 0.0001):
        self.window_size = window_size
        self.improvement_threshold = improvement_threshold
        self.metric_history = []

    def add_metric(self, metric_value: float, metric_name: str = 'loss') -> None:
        """Add a metric value to history."""
        self.metric_history.append(metric_value)

    def check_convergence(self, metric_is_decreasing: bool = True) -> Tuple[bool, str]:
        """Check if convergence has been reached."""
        if len(self.metric_history) < self.window_size:
            return False, "Not enough data to assess convergence"

        recent = self.metric_history[-self.window_size:]

        # Check if improvement is diminishing
        if metric_is_decreasing:
            improvements = [recent[i-1] - recent[i] for i in range(1, len(recent))]
        else:
            improvements = [recent[i] - recent[i-1] for i in range(1, len(recent))]

        avg_improvement = sum(improvements) / len(improvements)

        if avg_improvement < self.improvement_threshold:
            return True, f"Convergence detected: avg improvement = {avg_improvement:.6f}"

        return False, f"Still improving: avg improvement = {avg_improvement:.6f}"

    def get_status(self) -> str:
        """Get convergence status summary."""
        if not self.metric_history:
            return "No metrics recorded"

        return f"Metric history length: {len(self.metric_history)}, Last value: {self.metric_history[-1]:.6f}"


# ──────────────────────────────────────────────────────────────────────────────
# DATA PROFILING MODULE
# ──────────────────────────────────────────────────────────────────────────────

class DataProfiler:
    """Profiles data to guide model selection."""

    @staticmethod
    def profile_files(task_dir: str) -> Dict:
        """Profile the train, validation, and test files."""
        profile = {
            'train': DataProfiler._profile_csv(os.path.join(task_dir, 'data', 'train.csv')),
            'validation': DataProfiler._profile_csv(os.path.join(task_dir, 'data', 'validation.csv')),
            'test': DataProfiler._profile_csv(os.path.join(task_dir, 'data', 'test.csv')),
        }
        return profile

    @staticmethod
    def _profile_csv(filepath: str) -> Dict:
        """Profile a single CSV file."""
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                return {'rows': 0, 'error': 'Empty file'}

            profile = {
                'rows': len(rows),
                'columns': list(rows[0].keys()),
                'column_count': len(rows[0])
            }

            return profile
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def suggest_approach(profile: Dict, task_type: str) -> str:
        """Suggest initial approach based on data profile."""
        suggestions = f"Data Profile Insights:\n"
        suggestions += f"- Training samples: {profile['train'].get('rows', '?')}\n"
        suggestions += f"- Validation samples: {profile['validation'].get('rows', '?')}\n"
        suggestions += f"- Test samples: {profile['test'].get('rows', '?')}\n"
        suggestions += f"- Features: {profile['train'].get('column_count', '?')}\n"

        if profile['train'].get('rows', 0) < 1000:
            suggestions += "- Small dataset: Prefer simpler models to avoid overfitting\n"
        else:
            suggestions += "- Larger dataset: Can try more complex models\n"

        return suggestions


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "write_file",
        "description": "Write (overwrite) a file with the given content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "read_file",
        "description": "Read and return the contents of a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "bash",
        "description": "Run a bash command and return stdout + stderr.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
            },
            "required": ["command"],
        },
    },
]

# ── Tool implementations ──────────────────────────────────────────────────────

def write_file(path: str, content: str) -> str:
    try:
        # Create parent directories if needed
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully written {len(content)} characters to '{path}'."
    except Exception as e:
        return f"Error writing file: {e}"


def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File '{path}' not found."
    except Exception as e:
        return f"Error reading file: {e}"


def bash(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n{result.stderr}"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 120 seconds."
    except Exception as e:
        return f"Error running command: {e}"


def dispatch_tool(name: str, inputs: dict) -> str:
    if name == "write_file":
        return write_file(**inputs)
    elif name == "read_file":
        return read_file(**inputs)
    elif name == "bash":
        return bash(**inputs)
    else:
        return f"Unknown tool: {name}"

# ── Execution logging ─────────────────────────────────────────────────────────

execution_log = []


def log_user_message(content):
    """Log a user message."""
    if isinstance(content, str):
        execution_log.append({
            "role": "user",
            "content": content
        })
    elif isinstance(content, list):
        execution_log.append({
            "role": "user",
            "content": content
        })


def log_assistant_response(text_blocks, tool_uses):
    """Log an assistant response with text and tool calls."""
    content = []

    # Add text blocks
    for text in text_blocks:
        if text.strip():
            content.append({
                "type": "text",
                "text": text
            })

    # Add tool uses
    for tool_use in tool_uses:
        content.append({
            "type": "tool_use",
            "id": tool_use["id"],
            "name": tool_use["name"],
            "input": tool_use["input"]
        })

    if content:
        execution_log.append({
            "role": "assistant",
            "content": content
        })
        # Also add tool_calls field if there are tool uses
        if tool_uses:
            execution_log[-1]["tool_calls"] = [
                {
                    "id": tu["id"],
                    "type": "function",
                    "function": {
                        "name": tu["name"],
                        "arguments": json.dumps(tu["input"])
                    }
                }
                for tu in tool_uses
            ]


def log_tool_result(tool_use_id, content):
    """Log a tool result."""
    execution_log.append({
        "role": "tool",
        "tool_call_id": tool_use_id,
        "content": content
    })


def save_execution_log(filepath: str):
    """Save the execution log to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(execution_log, f, indent=2, ensure_ascii=False)


# ── Agent loop ────────────────────────────────────────────────────────────────

def run_agent(task_dir: str, max_iterations: int = 25) -> None:
    """
    Run the ML agent to solve the task in the given directory.

    Args:
        task_dir: Path to directory containing task.md and data/
        max_iterations: Maximum number of agent iterations
    """

    # Verify task directory exists and has required files
    if not os.path.isdir(task_dir):
        print(f"Error: Task directory '{task_dir}' does not exist")
        return

    task_file = os.path.join(task_dir, "task.md")
    data_dir = os.path.join(task_dir, "data")

    if not os.path.exists(task_file):
        print(f"Error: {task_file} not found")
        return

    if not os.path.isdir(data_dir):
        print(f"Error: {data_dir} directory not found")
        return

    # Read task description
    with open(task_file, "r", encoding="utf-8") as f:
        task_description = f.read()

    # Print task information
    print(f"\n{'='*70}")
    print(f"ML Task Agent")
    print(f"Task Directory: {task_dir}")
    print(f"{'='*70}\n")

    # Analyze task
    task_info = TaskAnalyzer.detect_task_type(task_description)
    task_specific_guidance = TaskAnalyzer.get_task_specific_guidance(task_info['task_type'])

    print(f"Detected Task Type: {task_info['task_type']}")
    print(f"Metrics to optimize: {task_info['metrics']}")
    print(f"Detection confidence: {task_info['confidence']:.1%}\n")

    # Profile data
    data_profile = DataProfiler.profile_files(task_dir)
    data_insights = DataProfiler.suggest_approach(data_profile, task_info['task_type'])

    # Initialize trackers
    tracker = ExperimentTracker(task_dir)
    convergence = ConvergenceMonitor()

    # Generate enhanced system message
    system_message = f"""You are an expert machine learning engineer specializing in {task_info['task_type']} tasks.

{task_specific_guidance}

TASK INFORMATION:
- Task Type: {task_info['task_type']}
- Key Metrics: {', '.join(task_info['metrics'])}
- Class Imbalance Issues: {task_info['has_class_imbalance']}
- Requires Calibration: {task_info['requires_calibration']}

DATA INSIGHTS:
{data_insights}

OPTIMIZATION STRATEGY:
1. Create an initial baseline model (simple and interpretable)
2. Measure performance on validation set
3. Iteratively improve by:
   - Trying different algorithms appropriate for {task_info['task_type']}
   - Tuning hyperparameters systematically
   - Engineering new features if needed
   - Handling data quality issues
4. Stop when improvements plateau (no improvement for 3+ iterations)

CRITICAL REQUIREMENTS:
- Stay within task directory (do not access files outside public/)
- Activate virtual environment: source .venv/bin/activate
- Use eval.py to evaluate metrics
- Report metrics in EXACT format specified in task.md
- Create and iterate on train.py multiple times
- Each iteration should show progress on validation metrics

REPORTING:
Always report metrics in this format:
Validation samples: XX
Test samples: XX
validation: {{'metric1': value1, 'metric2': value2}}
test: {{'metric1': value1, 'metric2': value2}}
"""

    # Initial message
    initial_message = f"""Please solve the following ML task:

{task_description}

Start by creating a train.py file that:
1. Loads data from data/train.csv, data/validation.csv, and data/test.csv
2. Trains a model on the training data
3. Evaluates on validation and test data
4. Outputs metrics in the specified format

Then iterate to improve performance. Stop when you see no significant improvement."""

    messages = [{"role": "user", "content": initial_message}]
    log_user_message(initial_message)

    iteration = 0
    consecutive_no_improvement = 0
    best_test_metric = None
    should_stop = False

    while iteration < max_iterations and not should_stop:
        iteration += 1
        print(f"\n[Iteration {iteration}/{max_iterations}]", flush=True)

        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=system_message,
                tools=TOOLS,
                messages=messages,
            )
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            break

        # Collect response content
        text_blocks = []
        tool_uses = []

        for block in response.content:
            if block.type == "text":
                text_blocks.append(block.text)
                if block.text.strip():
                    print(f"Assistant: {block.text[:200]}{'...' if len(block.text) > 200 else ''}", flush=True)
            elif block.type == "tool_use":
                tool_uses.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })

        log_assistant_response(text_blocks, tool_uses)

        # Check for completion
        if response.stop_reason == "end_turn":
            print(f"\n[Agent completed - end_turn]", flush=True)
            should_stop = True
            break

        # Handle tool calls
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id

                    input_str = json.dumps(tool_input, ensure_ascii=False)
                    if len(input_str) > 100:
                        input_display = input_str[:97] + "..."
                    else:
                        input_display = input_str

                    print(f"  Tool: {tool_name}({input_display})", flush=True)

                    result = dispatch_tool(tool_name, tool_input)

                    result_display = result[:200]
                    if len(result) > 200:
                        result_display += "..."
                    print(f"  Result: {result_display}", flush=True)

                    log_tool_result(tool_id, result)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result,
                    })

            log_user_message(tool_results)
            messages.append({"role": "user", "content": tool_results})
        else:
            print(f"Unexpected stop_reason: {response.stop_reason}", flush=True)
            break

    if iteration >= max_iterations:
        print(f"\n[Agent stopped - reached max iterations ({max_iterations})]", flush=True)

    # Print summary
    print(f"\n{'='*70}")
    print(f"Agent execution completed.")
    print(f"Experiments logged: {len(tracker.experiments)}")
    print(f"Convergence status: {convergence.get_status()}")
    print(f"{'='*70}\n", flush=True)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python target_agent.py <task_directory>")
        print("Example: python target_agent.py /home/ubuntu/sia/task_3/public")
        sys.exit(1)

    task_directory = sys.argv[1]

    # Run the agent
    run_agent(task_directory)

    # Save execution log
    log_file = os.path.join(task_directory, "agent_execution.json")
    try:
        save_execution_log(log_file)
        print(f"✓ Execution log saved to: {log_file}")
    except Exception as e:
        print(f"Error saving execution log: {e}")
