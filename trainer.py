import pandas as pd
import json
import os
import sys
import signal
# from utils import chat, parse_json_response, log_step, append_to_dataset, timestamp

# Load configuration
PROMPTS_FILE = "agent_prompts.json"
DATASET_FILE = "problems_dataset.csv"


def load_prompts():
    if not os.path.exists(PROMPTS_FILE):
        print(f"Error: {PROMPTS_FILE} not found.")
        sys.exit(1)
    with open(PROMPTS_FILE, "r") as f:
        return json.load(f)


def load_problems():
    if not os.path.exists(DATASET_FILE):
        print(f"Error: {DATASET_FILE} not found.")
        sys.exit(1)
    return pd.read_csv(DATASET_FILE)

# Global flag for graceful exit
stop_requested = False

def signal_handler(sig, frame):
    global stop_requested
    print("\nCtrl+C detected! Finishing current operation and saving data...")
    stop_requested = True

signal.signal(signal.SIGINT, signal_handler)


def run_problem(row, prompts):
    problem_id = row['problem_id']
    problem_text = row['problem_text']
    correct_solution = row['correct_solution']
    hint_text = row.get('hint','')

    print(f"--- Processing Problem ID: {problem_id} ---")
    print(f"Problem: {problem_text}")

    history = {
        "questions": [],
        "answers": [],
        "experiments": [],
        "skepticism": []
    }

    max_tries = 4
    for try_number in range(1, max_tries + 1):
        if stop_requested:
            print("Process stopped by user.")
            return

        print(f"--- Try {try_number} / {max_tries} ---")

        hint_active = (try_number > 2)
        current_hint = hint_text if hint_active else "None"
        print(f"Hint Active: {hint_active}")

        if try_number == 1:
            boss_input = f"Problem: {problem_text}\nSolve this directly."
        else:
            q_context = f"Problem: {problem_text}\nPrevious Questions: {history['questions']}"
            # questions = chat(prompts['questioner'], q_context)
            questions = "[]"
            history['questions'].append(questions)
            print("Questioner generated questions (placeholder).")

            a_context = f"Problem: {problem_text}\nQuestions to Answer: {questions}"
            # answers = chat(prompts['answerer'], a_context)
            answers = "[]"
            history['answers'].append(answers)
            print("Answerer provided answers (placeholder).")

            e_context = f"Problem: {problem_text}\nCurrent Q&A: {questions}\n{answers}"
            # experiment = chat(prompts['experimenter'], e_context)
            experiment = "[]"
            history['experiments'].append(experiment)
            print("Experimenter ran simulations (placeholder).")

            s_context = f"Problem: {problem_text}\nQ&A: {questions}\n{answers}\nExperiment: {experiment}"
            # skepticism = chat(prompts['skeptic'], s_context)
            skepticism = "[]"
            history['skepticism'].append(skepticism)
            print("Skeptic critiqued the findings (placeholder).")

            boss_input = (
                f"Problem: {problem_text}\n"
                f"Hint: {current_hint}\n"
                f"Recent Questions: {questions}\n"
                f"Recent Answers: {answers}\n"
                f"Recent Experiments: {experiment}\n"
                f"Recent Skepticism: {skepticism}\n"
                f"Synthesize all this and provide the final answer."
            )

        # boss_response = chat(prompts['boss'], boss_input)
        boss_response = "(placeholder boss response)"
        print(f"Boss Proposed Answer: {boss_response}")

        # QA Check placeholder
        verdict = "thumbs down"

        # Save Data (placeholder print)
        record = {
            "problem_id": problem_id,
            "problem_text": problem_text,
            "actual_solution": correct_solution,
            "hint_used": hint_active,
            "questions": history['questions'][-1] if history['questions'] else "",
            "answers": history['answers'][-1] if history['answers'] else "",
            "experimenter_thoughts": history['experiments'][-1] if history['experiments'] else "",
            "skeptic_thoughts": history['skepticism'][-1] if history['skepticism'] else "",
            "boss_logic": boss_response,
            "qa_verdict": verdict,
            "try_number": try_number
        }
        print(f"Recorded attempt: {record}")

        if verdict == "thumbs up":
            print("Problem Solved!")
            return

    if not stop_requested:
        print("--- Hail Mary (Final Retry) ---")
        boss_final_resp = "(placeholder final boss response)"
        print(f"Boss Hail Mary Answer: {boss_final_resp}")


def main():
    print("Starting AI Agent System (placeholder trainer)...")
    # prompts = load_prompts()
    # df = load_problems()
    # for index, row in df.iterrows():
    #     if stop_requested:
    #         break
    #     run_problem(row, prompts)
    print("This is a placeholder runner. Run assemble_project.py and then adapt paths as needed.")

if __name__ == "__main__":
    main()
