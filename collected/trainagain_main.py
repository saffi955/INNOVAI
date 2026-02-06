import pandas as pd
import json
import os
import sys
import signal
from utils import chat, parse_json_response, log_step, append_to_dataset, timestamp

# Load configuration
PROMPTS_FILE = "agent_prompts.json"
DATASET_FILE = "problems_dataset.csv"

def load_prompts():
    if not os.path.exists(PROMPTS_FILE):
        log_step(f"Error: {PROMPTS_FILE} not found.")
        sys.exit(1)
    with open(PROMPTS_FILE, "r") as f:
        return json.load(f)

def load_problems():
    if not os.path.exists(DATASET_FILE):
        log_step(f"Error: {DATASET_FILE} not found.")
        sys.exit(1)
    return pd.read_csv(DATASET_FILE)

# Global flag for graceful exit
stop_requested = False

def signal_handler(sig, frame):
    global stop_requested
    log_step("\nCtrl+C detected! Finishing current operation and saving data...")
    stop_requested = True

signal.signal(signal.SIGINT, signal_handler)

def run_problem(row, prompts):
    problem_id = row['problem_id']
    problem_text = row['problem_text']
    correct_solution = row['correct_solution']
    hint_text = row['hint']

    log_step(f"--- Processing Problem ID: {problem_id} ---")
    log_step(f"Problem: {problem_text}")

    # Initialize State
    history = {
        "questions": [],
        "answers": [],
        "experiments": [],
        "skepticism": []
    }
    
    # Try Loop (1 to 4)
    max_tries = 4
    for try_number in range(1, max_tries + 1):
        if stop_requested:
            log_step("Process stopped by user.")
            return

        log_step(f"--- Try {try_number} / {max_tries} ---")
        
        hint_active = (try_number > 2)
        current_hint = hint_text if hint_active else "None"
        log_step(f"Hint Active: {hint_active}")

        # Boss Initial Attempt (Try 1) or Collaboration Synthesis
        if try_number == 1:
            # Direct attempt for Try 1, or minimal context
            boss_input = f"Problem: {problem_text}\nSolve this directly."
        else:
            # Collaborative Context
            # 1. Questioner
            q_context = f"Problem: {problem_text}\nPrevious Questions: {history['questions']}"
            questions = chat(prompts['questioner'], q_context)
            history['questions'].append(questions)
            log_step("Questioner generated questions.")

            # 2. Answerer
            a_context = f"Problem: {problem_text}\nQuestions to Answer: {questions}"
            answers = chat(prompts['answerer'], a_context)
            history['answers'].append(answers)
            log_step("Answerer provided answers.")

            # 3. Experimenter
            e_context = f"Problem: {problem_text}\nCurrent Q&A: {questions}\n{answers}"
            experiment = chat(prompts['experimenter'], e_context)
            history['experiments'].append(experiment)
            log_step("Experimenter ran simulations/thoughts.")

            # 4. Skeptic
            s_context = f"Problem: {problem_text}\nQ&A: {questions}\n{answers}\nExperiment: {experiment}"
            skepticism = chat(prompts['skeptic'], s_context)
            history['skepticism'].append(skepticism)
            log_step("Skeptic critiqued the findings.")

            # Boss Synthesis
            boss_input = (
                f"Problem: {problem_text}\n"
                f"Hint: {current_hint}\n"
                f"Recent Questions: {questions}\n"
                f"Recent Answers: {answers}\n"
                f"Recent Experiments: {experiment}\n"
                f"Recent Skepticism: {skepticism}\n"
                f"Synthesize all this and provide the final answer."
            )

        # Boss speaks
        boss_response = chat(prompts['boss'], boss_input)
        log_step(f"Boss Proposed Answer: {boss_response}")

        # QA Check
        qa_input = (
            f"Problem: {problem_text}\n"
            f"Proposed Answer: {boss_response}\n"
            f"Hidden Correct Solution: {correct_solution}\n"
            f"Compare these. If they match in meaning, return 'thumbs up'. If not, 'thumbs down'."
        )
        qa_response_raw = chat(prompts['qa'], qa_input)
        qa_json = parse_json_response(qa_response_raw)
        
        verdict = "thumbs down"
        reason = "Failed to parse QA response"
        
        if qa_json:
            verdict = qa_json.get('verdict', 'thumbs down').lower()
            reason = qa_json.get('reason', 'No reason provided')
        
        log_step(f"QA Verdict: {verdict} | Reason: {reason}")
        
        # Save Data
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
            "qa_reasoning": reason,
            "try_number": try_number,
            "timestamp": timestamp(),
            "outcome": "Success" if verdict == "thumbs up" else "Fail"
        }
        append_to_dataset(record)

        if verdict == "thumbs up":
            log_step("Problem Solved!")
            return

    # Hail Mary (Try > 4)
    if not stop_requested:
        log_step("--- Hail Mary (Final Retry) ---")
        full_history = f"HISTORY:\nQuestions: {history['questions']}\nAnswers: {history['answers']}\nExperiments: {history['experiments']}\nSkepticism: {history['skepticism']}"
        boss_retry_input = (
            f"Problem: {problem_text}\n"
            f"{full_history}\n"
            f"Previous attempts failed. Re-read all data, ignore previous wrong conclusions, and try one last time."
        )
        
        boss_final_resp = chat(prompts['boss'], boss_retry_input)
        log_step(f"Boss Hail Mary Answer: {boss_final_resp}")
        
        qa_final_input = (
            f"Problem: {problem_text}\n"
            f"Proposed Answer: {boss_final_resp}\n"
            f"Hidden Correct Solution: {correct_solution}\n"
            f"Compare these. If they match in meaning, return 'thumbs up'. If not, 'thumbs down'."
        )
        qa_final_raw = chat(prompts['qa'], qa_final_input)
        qa_final_json = parse_json_response(qa_final_raw)
        
        f_verdict = "thumbs down"
        f_reason = "Failed to parse QA response"
        if qa_final_json:
            f_verdict = qa_final_json.get('verdict', 'thumbs down').lower()
            f_reason = qa_final_json.get('reason', 'No reason provided')
            
        log_step(f"Final QA Verdict: {f_verdict}")
        
        final_record = {
            "problem_id": problem_id,
            "problem_text": problem_text,
            "actual_solution": correct_solution,
            "hint_used": True, # Technically true for final retry
            "questions": "ALL HISTORY",
            "answers": "ALL HISTORY",
            "experimenter_thoughts": "ALL HISTORY",
            "skeptic_thoughts": "ALL HISTORY",
            "boss_logic": boss_final_resp,
            "qa_verdict": f_verdict,
            "qa_reasoning": f_reason,
            "try_number": 5, # Hail Mary
            "timestamp": timestamp(),
            "outcome": "Success" if f_verdict == "thumbs up" else "Fail"
        }
        append_to_dataset(final_record)

def main():
    log_step("Starting AI Agent System...")
    prompts = load_prompts()
    df = load_problems()
    
    for index, row in df.iterrows():
        if stop_requested:
            break
        run_problem(row, prompts)
        
    log_step("All problems processed or stopped.")

if __name__ == "__main__":
    main()
