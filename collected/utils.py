import ollama
import json
import re
import pandas as pd
import datetime
import os

LOG_FILE = "app_logs.txt"
DATASET_FILE = "training_data.csv"

def timestamp():
    """Returns the current timestamp."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_step(message):
    """
    Logs a message with a timestamp to the log file and prints it to the console.
    """
    ts = timestamp()
    entry = f"[{ts}] {message}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def chat(system_prompt, user_input, model="phi3"):
    """
    Sends a chat request to the Ollama model.
    """
    try:
        response = ollama.chat(model=model, messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_input},
        ])
        return response['message']['content']
    except Exception as e:
        error_msg = f"Error communicating with Ollama: {e}"
        log_step(error_msg)
        return error_msg

def parse_json_response(response_text):
    """
    Attempts to extract and parse a JSON object from a string.
    Finds the first occurring JSON object in the text.
    """
    try:
        # Regex to find JSON block
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            # Try parsing the whole string if regex doesn't match
            return json.loads(response_text)
    except json.JSONDecodeError:
        log_step(f"Failed to parse JSON from response: {response_text[:100]}...")
        return None

def append_to_dataset(row_dict):
    """
    Appends a dictionary as a new row to the training_data.csv file.
    Creates the file with headers if it doesn't exist.
    """
    file_exists = os.path.isfile(DATASET_FILE)
    
    # Ensure all expected columns are present (based on spec), handle missing ones gracefully
    expected_columns = [
        "problem_id", "problem_text", "actual_solution", "hint_used", 
        "questions", "answers", "experimenter_thoughts", "skeptic_thoughts", 
        "boss_logic", "qa_verdict", "qa_reasoning", "try_number", 
        "timestamp", "outcome"
    ]
    
    # Filter/Order row_dict to match expected columns if needed, but pandas handles extra keys ok.
    # We just explicitly select columns to ensure order if we want, but simple to_csv is fine.
    
    df = pd.DataFrame([row_dict])
    
    # If file exists, append without header. If not, write with header.
    mode = 'a' if file_exists else 'w'
    header = not file_exists
    
    try:
        df.to_csv(DATASET_FILE, mode=mode, header=header, index=False)
        log_step(f"Data saved to {DATASET_FILE}")
    except Exception as e:
        log_step(f"Error saving to dataset: {e}")
