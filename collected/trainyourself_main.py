import sys
import signal
import json
import pandas as pd
import ollama
from datetime import datetime
import argparse
import re

class SelfLearningAI:
    def __init__(self, config_file, dataset_file, log_file, max_tries=4):
        self.config_file = config_file
        self.dataset_file = dataset_file
        self.log_file = log_file
        self.max_tries = max_tries
        self.agent_prompts = {}
        self.killed = False
        
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.load_agent_prompts()
        self.initialize_dataset()
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\nKiller switch activated! Shutting down gracefully...")
        self.killed = True
        sys.exit(0)
    
    def load_agent_prompts(self):
        """Load agent prompts from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                self.agent_prompts = json.load(f)
            self.log("Agent prompts loaded successfully")
        except Exception as e:
            self.log(f"ERROR: Failed to load agent prompts: {e}")
            sys.exit(1)
    
    def initialize_dataset(self):
        """Initialize dataset CSV if it doesn't exist"""
        try:
            pd.read_csv(self.dataset_file)
        except FileNotFoundError:
            # Extended schema for new data
            df = pd.DataFrame(columns=[
                'problem_id', 'problem_text', 'actual_solution', 'hint', 
                'questions', 'answers', 'agent_opinions', 
                'experimenter_thoughts', 'skeptic_thoughts',
                'qa_reasons', 'user_instructions', 'try_number',
                'final_outcome', 'tries_data', 'timestamp'
            ])
            df.to_csv(self.dataset_file, index=False)
            self.log("Dataset file initialized")
    
    def log(self, message):
        """Log message to file with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp}: {message}\n"
        print(log_entry.strip())
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def call_agent(self, agent_name, prompt):
        """Call an Ollama agent"""
        try:
            full_prompt = f"{self.agent_prompts[agent_name]}\n\n{prompt}"
            response = ollama.chat(
                model='phi3',
                messages=[{'role': 'user', 'content': full_prompt}]
            )
            return response['message']['content'].strip()
        except Exception as e:
            self.log(f"ERROR: Agent {agent_name} failed: {e}")
            return ""
    
    def parse_list(self, text, min_length=5):
        """Generic list parser"""
        lines = text.split('\n')
        items = []
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                cleaned = re.sub(r'^[\d\-•\.\)]+\s*', '', line)
                if cleaned and len(cleaned) > min_length:
                    items.append(cleaned)
        return items
    
    def check_qa(self, proposed_answer, correct_solution):
        """Check if answer is correct via QA agent, return (success, reason)"""
        if not proposed_answer:
            return False, "No answer proposed"
            
        prompt = f"Proposed answer: {proposed_answer}\nCorrect solution (hidden): {correct_solution}"
        
        response = self.call_agent('qa', prompt)
        
        # Parse Verdict and Reason
        verdict_match = 'thumbs up' in response.lower() or 'up' in response.lower()
        
        # Try to extract reason
        reason = response
        if ':' in response:
            parts = response.split(':', 1)
            if len(parts) > 1:
                reason = parts[1].strip()
        
        self.log(f"QA check: {verdict_match} | Reason: {reason[:100]}...")
        return verdict_match, reason
    
    def process_problem(self, problem_data):
        """Process a single problem through the workflow"""
        p_id = problem_data.get('problem_id', 'unknown')
        p_text = problem_data.get('problem_text', '')
        p_sol = problem_data.get('actual_solution', '')  # Updated column name
        p_hint = problem_data.get('hint', '')
        
        self.log(f"Starting problem {p_id}: {p_text[:50]}...")
        
        # State tracking
        state = {
            'questions': [],
            'answers': [],
            'experimenter': [],
            'skeptic': [],
            'boss_opinions': [],
            'qa_reasons': [],
            'tries_log': [],
            'user_instructions': []
        }
        
        # === Try 1: Initial Boss Answer ===
        self.log("\n=== Try 1: Initial Boss Attempt ===")
        boss_prompt = f"Problem: {p_text}\nTry to solve it directly if simple. Output your answer in format: 'Proposed Answer: [solution]'."
        boss_initial = self.call_agent('boss', boss_prompt)
        self.log(f"Boss Initial: {boss_initial}")
        
        success, reason = self.check_qa(boss_initial, p_sol)
        state['boss_opinions'].append(f"Try 1 (Initial): {boss_initial}")
        state['qa_reasons'].append(f"Try 1: {reason}")
        state['tries_log'].append({'try': 1, 'output': boss_initial, 'success': success, 'qa_reason': reason})
        
        if success:
            self.log("Solved on Try 1!")
            self.save_result(problem_data, state, 'success', 1)
            return True
            
        # === Tries 2 to Max (Full Loop) ===
        for try_num in range(2, self.max_tries + 1):
            if self.killed: break
            
            self.log(f"\n=== Try {try_num}/{self.max_tries} ===")
            current_context = ""
            
            # Inject Hint after 2 tries (starting at Try 3)
            if try_num >= 3 and p_hint:
                self.log(f"Injecting Hint: {p_hint}")
                current_context += f"\n\nHINT/INSTRUCTION: {p_hint}\n"
                state['user_instructions'].append(f"Try {try_num}: Hint provided - {p_hint}")
            
            # 1. Questioner
            q_prompt = f"Problem: {p_text}\n{current_context}\nGenerate 16-17 diverse questions. No repeats from previous tries: {json.dumps(state['questions'][-10:])}"
            q_text = self.call_agent('questioner', q_prompt)
            questions = self.parse_list(q_text)
            state['questions'].extend(questions)
            self.log(f"Generated {len(questions)} questions")
            
            # 2. Answerer
            if questions:
                a_prompt = f"Answer these questions creatively:\n" + "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions[:17])])
                a_text = self.call_agent('answerer', a_prompt)
                answers = self.parse_list(a_text)
                state['answers'].extend(answers)
                self.log(f"Generated {len(answers)} answers")
            
            # 3. Experimenter (Code/Math Simulation)
            exp_prompt = f"Problem: {p_text}\n{current_context}\nRecent Q&A pairs:\n"
            recent_qa = list(zip(state['questions'][-10:], state['answers'][-10:]))
            for q, a in recent_qa:
                exp_prompt += f"Q: {q}\nA: {a}\n\n"
            exp_prompt += "Simulate outcomes, test hypotheses, and validate approaches using code/mathematical thinking."
            exp_text = self.call_agent('experimenter', exp_prompt)
            state['experimenter'].append(f"Try {try_num}: {exp_text}")
            self.log(f"Experimenter analysis completed")
            
            # 4. Skeptic (Challenge Assumptions)
            skep_prompt = f"Problem: {p_text}\nExperimenter analysis: {exp_text}\nRecent answers: {state['answers'][-5:]}\nChallenge assumptions, identify logical fallacies, and stress-test these approaches."
            skep_text = self.call_agent('skeptic', skep_prompt)
            state['skeptic'].append(f"Try {try_num}: {skep_text}")
            self.log(f"Skeptic analysis completed")
            
            # 5. Boss Connect Dots
            boss_prompt = (f"Problem: {p_text}\n{current_context}\n"
                           f"Experimenter insights: {exp_text}\n"
                           f"Skeptic challenges: {skep_text}\n"
                           f"All Q&A so far: {json.dumps(list(zip(state['questions'], state['answers']))[-5:])}\n"
                           f"Connect all dots and provide final answer in format: 'Proposed Answer: [solution]'.")
            boss_res = self.call_agent('boss', boss_prompt)
            state['boss_opinions'].append(f"Try {try_num}: {boss_res}")
            
            # QA Check
            success, reason = self.check_qa(boss_res, p_sol)
            state['qa_reasons'].append(f"Try {try_num}: {reason}")
            state['tries_log'].append({'try': try_num, 'output': boss_res, 'success': success, 'qa_reason': reason})
            
            if success:
                self.log(f"Solved on Try {try_num}!")
                self.save_result(problem_data, state, 'success', try_num)
                return True
        
        # === Final Chance: Connect All Dots ===
        self.log("\n=== Final Chance: Connect All Accumulated Data ===")
        boss_final_prompt = (f"Problem: {p_text}\n\n"
                            f"We have failed {self.max_tries} times. Here is ALL accumulated data:\n\n"
                            f"HINT: {p_hint}\n\n"
                            f"TOTAL QUESTIONS ASKED: {len(state['questions'])}\n"
                            f"TOTAL ANSWERS PROVIDED: {len(state['answers'])}\n\n"
                            f"EXPERIMENTER THOUGHTS:\n" + "\n".join(state['experimenter'][-3:]) + "\n\n"
                            f"SKEPTIC CHALLENGES:\n" + "\n".join(state['skeptic'][-3:]) + "\n\n"
                            f"RECENT Q&A PAIRS:\n" + "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(state['questions'][-5:], state['answers'][-5:])]) + "\n\n"
                            f"Connect ALL dots and provide ONE final answer in format: 'Proposed Answer: [solution]'.")
        boss_final = self.call_agent('boss', boss_final_prompt)
        
        success, reason = self.check_qa(boss_final, p_sol)
        state['boss_opinions'].append(f"Final Chance: {boss_final}")
        state['qa_reasons'].append(f"Final Chance: {reason}")
        state['tries_log'].append({'try': 'Final', 'output': boss_final, 'success': success, 'qa_reason': reason})
        
        if success:
            self.log("Solved on Final Chance!")
            self.save_result(problem_data, state, 'success', self.max_tries + 1)
            return True
        
        self.log(f"Failed after all attempts. Total tries: {self.max_tries + 1}")
        self.save_result(problem_data, state, 'fail', self.max_tries + 1)
        return False

    def save_result(self, problem_data, state, outcome, try_number):
        """Save to CSV with all data including failed attempts"""
        try:
            df = pd.read_csv(self.dataset_file)
        except:
            return # Should exist
            
        row = {
            'problem_id': problem_data.get('problem_id'),
            'problem_text': problem_data.get('problem_text'),
            'actual_solution': problem_data.get('actual_solution'),
            'hint': problem_data.get('hint'),
            'questions': json.dumps(state['questions']),
            'answers': json.dumps(state['answers']),
            'agent_opinions': json.dumps(state['boss_opinions']),
            'experimenter_thoughts': json.dumps(state['experimenter']),
            'skeptic_thoughts': json.dumps(state['skeptic']),
            'qa_reasons': json.dumps(state['qa_reasons']),
            'user_instructions': json.dumps(state['user_instructions']),
            'try_number': try_number,
            'final_outcome': outcome,
            'tries_data': json.dumps(state['tries_log']),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(self.dataset_file, index=False)
        self.log(f"Saved result for {problem_data.get('problem_id')} - Outcome: {outcome}")

    def run(self):
        self.log("=== Self-Learning AI System Started (Enhanced Version) ===")
        try:
            # Read from dataset.csv as input (not problems.csv)
            problems = pd.read_csv(self.dataset_file)
            # Filter for problems that haven't been processed yet (empty final_outcome)
            unprocessed = problems[problems['final_outcome'].isna() | (problems['final_outcome'] == '')]
            
            if len(unprocessed) == 0:
                self.log("No unprocessed problems found in dataset.csv")
                return
                
            self.log(f"Found {len(unprocessed)} unprocessed problems")
            
        except Exception as e:
            self.log(f"Error reading dataset: {e}")
            return
            
        total_problems = len(unprocessed)
        solved_count = 0
        
        for idx, (_, row) in enumerate(unprocessed.iterrows()):
            if self.killed: break
            
            self.log(f"\n{'='*60}")
            self.log(f"Processing problem {idx+1}/{total_problems}")
            self.log(f"{'='*60}")
            
            if self.process_problem(row.to_dict()):
                solved_count += 1
        
        self.log(f"\n=== Session Complete ===")
        self.log(f"Total problems processed: {total_problems}")
        self.log(f"Solved: {solved_count}")
        self.log(f"Failed: {total_problems - solved_count}")
        self.log(f"Success rate: {(solved_count/total_problems*100):.1f}%")

def main():
    parser = argparse.ArgumentParser(description='Self-Learning AI System - Enhanced Version')
    parser.add_argument('--config', default='agent_prompts.json', help='Agent prompts config file')
    parser.add_argument('--dataset', default='dataset.csv', help='Dataset file (input and output)')
    parser.add_argument('--log', default='app_logs.txt', help='Log file')
    parser.add_argument('--max-tries', type=int, default=4, help='Maximum tries per problem')
    parser.add_argument('--kill', action='store_true', help='Exit immediately')
    
    args = parser.parse_args()
    
    if args.kill:
        print("Kill flag detected. Exiting...")
        sys.exit(0)
    
    ai = SelfLearningAI(args.config, args.dataset, args.log, args.max_tries)
    ai.run()

if __name__ == '__main__':
    main()
