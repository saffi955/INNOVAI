# Creative Trainer

Creative Trainer is a compact toolkit for building a creativity-focused training dataset and running iterative multi-agent training loops to improve a generative model's creative output.

Goal
- Train or fine-tune local LLMs (e.g., Ollama Phi-3 or compatible models) on curated prompt→response pairs that emphasize novelty, metaphorical thinking, and lateral ideation.

Key features
- Curated creativity dataset support: prompt/response JSONL files designed to teach imaginative, idea-generation behavior.
- Multi-agent iterative runner: a coordinator that can orchestrate questioner/answerer/experimenter/skeptic/QA agents to expand and refine solutions.
- Assembly utility: gather scattered resources (datasets, prompts) into a `collected/` folder for consistent training runs.

Repository structure
- `trainer.py` — lightweight orchestrator for iterative multi-agent problem-solving and dataset generation.
- `assemble_project.py` — copies source files (as listed in `manifest.json`) into `collected/` for a single, self-contained project folder.
- `manifest.json` — list of source paths to include automatically in `collected/`.
- `collected/` — target folder where the dataset, prompts, and runner scripts are copied (populated by `assemble_project.py`).
- `docs/` — documentation and original README excerpts.

Datasets
- The project expects creativity-focused prompt→response example files (JSONL or CSV). Example files in `collected/` may include `DATASET.txt`, `unified_dataset.jsonl`, and `dataset.jsonl`.

Requirements
- Python 3.8+ (venv recommended)
- Optional: Ollama installed locally if you want to run models like Phi-3

Quick start
1. Create a virtual environment and install dependencies (if present under `collected/requirements*.txt`):

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r collected/requirements_trainagain.txt
```

2. Assemble the project files into `collected/`:

```powershell
python assemble_project.py
```

3. Inspect `collected/` for dataset files (`.jsonl`, `.csv`) and `agent_prompts`.

4. Adapt `trainer.py` to point to your dataset and prompts, then run:

```powershell
python trainer.py
```

Notes on training
- `trainer.py` is a placeholder runner adapted from the original multi-agent implementation. To perform real model calls you should implement the `chat()` function using your preferred backend (Ollama, local API, or remote LLMs), and wire `agent_prompts.json` into `PROMPTS_FILE`.
- The assemble step is purely organizational — it does not alter your data.

Repository metadata
- Author: saffi955 (email: saffitheprice@gmail.com)
- Intended remote: https://github.com/saffi955/creative_trainer

Next steps (recommended)
- Verify `collected/` contains these source artifacts: datasets, `agent_prompts.json`, `utils.py`, and the original `main.py` runner.
- Implement `chat()` connectors for your chosen model runtime and add training/evaluation scripts.
- Add a small example `problems.csv` and a unit test demonstrating one end-to-end run.

License
- Add a license file you prefer (MIT recommended for open sharing).
