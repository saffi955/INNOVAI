# Self-Learning AI System

A Python-based multi-agent AI system that uses Ollama's Phi-3 model to solve problems through iterative question-answer cycles, building a training dataset from the learning process.

## Overview

This application runs **completely offline** using locally installed Ollama with the Phi-3 model. Six AI agents collaborate to solve problems:

- **Boss Agent**: Attempts direct solutions and connects dots from Q&A
- **QA Agent**: Validates proposed answers against correct solutions with reasoning
- **Questioner Agent**: Generates 16-17 diverse questions per iteration
- **Answerer Agent**: Provides creative, cross-domain answers
- **Experimenter Agent**: Simulates outcomes using code/mathematical thinking
- **Skeptic Agent**: Challenges assumptions and stress-tests approaches

## Prerequisites

1. **Python 3.7+** installed on your system
2. **Ollama** installed and running ([Download here](https://ollama.ai))
3. **Phi-3 model** pulled in Ollama:
   ```bash
   ollama pull phi3
   ```

## Installation

### Windows

1. Open Command Prompt in the project directory
2. Run the setup script:
   ```bash
   setup.bat
   ```

This will:
- Create a virtual environment
- Install all required dependencies (ollama, pandas)

### Manual Setup (All Platforms)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Quick Start (Windows)

```bash
run.bat
```

### Manual Run

```bash
# Activate virtual environment first
venv\Scripts\activate

# Run with default settings
python main.py

# Run with custom options
python main.py --problems my_problems.csv --max-tries 3 --log my_log.txt
```

### Command-Line Options

```bash
python main.py [OPTIONS]

Options:
  --config FILE       Agent prompts config file (default: agent_prompts.json)
  --problems FILE     Problems input CSV file (default: problems.csv)
  --log FILE          Log file path (default: app_logs.txt)
  --dataset FILE      Dataset output CSV (default: dataset.csv)
  --max-tries N       Maximum tries per problem (default: 5)
  --kill              Exit immediately (killer switch)
```

## File Structure

```
trainyourself/
├── main.py                 # Main application
├── agent_prompts.json      # Agent system prompts (editable)
├── problems.csv            # Input problems with solutions
├── dataset.csv             # Generated training dataset
├── app_logs.txt            # Detailed execution logs
├── requirements.txt        # Python dependencies
├── setup.bat              # Windows setup script
├── run.bat                # Windows run script
└── README.md              # This file
```

## Configuration

### Agent Prompts (`agent_prompts.json`)

Edit this file to customize agent behavior:

```json
{
  "boss": "Your custom Boss agent prompt...",
  "qa": "Your custom QA agent prompt...",
  "questioner": "Your custom Questioner prompt...",
  "answerer": "Your custom Answerer prompt..."
}
```

### Problems File (`problems.csv`)

Format:
```csv
problem_id,problem_text,correct_solution
1,"What is 2+2?","4"
2,"Capital of France?","Paris"
```

## Workflow

1. **Initial Attempt**: Boss tries to solve directly
2. **QA Check**: If correct, move to next problem
3. **Iterative Loop** (if initial fails):
   - Questioner generates 16-17 unique questions
   - Answerer provides creative answers
   - **User Instruction Pause** (10 seconds to add guidance)
   - Boss connects dots from all Q&A
   - QA validates the answer
   - Repeat up to max_tries

## Interactive Features

### User Instruction Pauses

The system pauses twice per problem for 10 seconds:
1. Before Boss's initial attempt
2. Before each Boss dot-connecting phase

You can:
- Type `yes` to provide custom instructions
- Type `no` or wait 10 seconds to skip

### Killer Switch

Press **Ctrl+C** at any time to stop gracefully, or use:
```bash
python main.py --kill
```

## Output Files

### `app_logs.txt`
Timestamped log of all operations:
```
2025-12-19 10:00:00: Starting problem 1: What is 2+2?
2025-12-19 10:00:05: Boss initial attempt: The answer is 4
2025-12-19 10:00:06: QA response: thumbs up
2025-12-19 10:00:06: Problem 1 SOLVED on initial attempt!
```

### `dataset.csv`
Training dataset with columns:
- `problem_id`: Unique identifier
- `problem_text`: The problem statement
- `actual_solution`: Correct answer
- `questions`: JSON array of all questions asked
- `answers`: JSON array of all answers given
- `agent_opinions`: Boss's reasoning attempts
- `user_instructions`: Any instructions you provided
- `try_number`: Number of attempts made
- `final_outcome`: success/fail
- `timestamp`: When processed

## Troubleshooting

### "Ollama connection failed"
- Ensure Ollama is running: `ollama serve`
- Verify Phi-3 is installed: `ollama list`
- Pull if needed: `ollama pull phi3`

### "Virtual environment not found"
- Run `setup.bat` (Windows) or create manually
- Ensure Python is in your PATH

### "No questions generated"
- Check Ollama is responding
- Review agent prompts in `agent_prompts.json`
- Check logs in `app_logs.txt`

### Timeout issues
- The 10-second instruction pause is intentional
- Type quickly or press Enter to skip
- Adjust timeout in code if needed (search for `TimeoutInput(timeout=10)`)

## Advanced Usage

### Custom Problem Sets

Create your own CSV with complex problems:
```csv
problem_id,problem_text,correct_solution
101,"Explain quantum entanglement","Quantum entanglement is a phenomenon where..."
102,"Design a sustainable city","A sustainable city should include..."
```

### Analyzing Results

Load the dataset in Python:
```python
import pandas as pd
import json

df = pd.read_csv('dataset.csv')

# View successful solutions
successful = df[df['final_outcome'] == 'success']

# Parse questions from a specific problem
questions = json.loads(df.loc[0, 'questions'])
```

### Fine-Tuning Preparation

The `dataset.csv` is structured for fine-tuning:
- Questions and answers are paired
- Agent reasoning is captured
- Success/failure is labeled
- User guidance is included

## Performance Tips

1. **Start Small**: Test with 2-3 simple problems first
2. **Monitor Logs**: Watch `app_logs.txt` in real-time
3. **Adjust Max Tries**: Lower for faster iteration, higher for complex problems
4. **Customize Prompts**: Edit `agent_prompts.json` to improve agent performance
5. **Use Instructions**: Provide guidance during pauses for better results

## System Requirements

- **RAM**: 8GB minimum (16GB recommended for Phi-3)
- **Storage**: 2GB for Phi-3 model + dataset space
- **CPU**: Multi-core recommended for faster inference
- **OS**: Windows, Linux, or macOS

## License

This project is provided as-is for educational and research purposes.

## Support

For issues:
1. Check `app_logs.txt` for detailed error messages
2. Verify Ollama and Phi-3 are working: `ollama run phi3`
3. Ensure all dependencies are installed: `pip list`

---

**Note**: This system learns through iteration. Initial runs may have lower success rates as the agents explore different reasoning paths. The generated dataset becomes more valuable over time as patterns emerge.
