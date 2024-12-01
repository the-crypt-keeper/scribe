import random
import time
import os
import json
import uuid
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from llm_tools import build_tokenizer, universal_llm_request, simple_extract_json
from jinja2 import Template

SAMPLER = {
    'temperature': 1.0,
    'min_p': 0.05,
    'repetition_penalty': 1.1,
    'max_tokens': 3072,
    'min_tokens': 10 
}

class Scribe():
    def __init__(self, project):
        self.project = project       
        self.steps = {}
        
    def add_step(self, step):
        assert step.step not in self.steps
        step.setup(self)
        seq = len(list(self.steps.keys()))
        self.steps[step.step] = {
            'fn': step,
            'seq': seq,
            'queue': None
        }

    def save(self, key, id, payload):
        pass
    
    def load(self, key, id):
        pass
    
    def find(self, key):
        pass

    def all(self):
        pass
        
    def _execute_single_step(self, step_name, id, input):
        st = self.steps[step_name]['fn']
        print(f"> {step_name} executing {id}")
        output, meta = st.run(id, input)
        if output is not None:
            self.save(st.outkey, id, output)
            self.save('_'+st.outkey, id, json.dumps(meta))
            
    def _create_work_thread(self, step_name):
        st = self.steps[step_name]['fn']       
        num_parallel = int(st.params.get('num_parallel', '1'))
        self.steps[step_name]['queue'] = ThreadPoolExecutor(max_workers=num_parallel)
        self.steps[step_name]['futures'] = []
    
    def _queue_work(self, step_name, id, input):
        if self.steps[step_name]['queue'] is None:
            self._create_work_thread(step_name)
        future = self.steps[step_name]['queue'].submit(self._execute_single_step, step_name, id, input)
        self.steps[step_name]['futures'].append(future)
        return future
    
    def _unfinished_futures(self, step_name):
        if self.steps[step_name]['queue'] is None:
            return []
        return [future for future in self.steps[step_name]['futures'] if not future.done()]

    def _join_work_thread(self, step_name):
        if self.steps[step_name]['queue'] is not None:
            # Wait for all futures to complete
            for future in self.steps[step_name]['futures']:
                future.result()
            self.steps[step_name]['queue'].shutdown(wait=True)
            self.steps[step_name]['queue'] = None
            self.steps[step_name]['futures'] = []
    
    def run_all_steps(self, sleep_delay = 5):
        while True:
            new_work = False
            for step_name, step_info in sorted(self.steps.items(), key=lambda x: x[1]['seq']):
                step = step_info['fn']
                pending_inputs = list(step.pending_inputs())
                if pending_inputs:
                    for id, input in pending_inputs:
                        self._queue_work(step_name, id, input)
                    new_work = True
                    
            if new_work:
                time.sleep(sleep_delay)
                continue
            
            for step_name in self.steps:
                if self._unfinished_futures(step_name):
                    time.sleep(sleep_delay)
                    continue

            # If there was no new work and there are no pending futures, the process is complete
            for step_name in self.steps:
                self._join_work_thread(step_name)
                
            break  # Exit the while loop

import sqlite3

class SQLiteScribe(Scribe):
    def __init__(self, project):
        super().__init__(project)
        
        self.dbname = f'{project}.db'
        self.db = sqlite3.connect(self.dbname)
        self.db.execute('''CREATE TABLE IF NOT EXISTS data
                           (key TEXT, id TEXT, payload TEXT,
                            PRIMARY KEY (key, id))''')
        self.db.commit()
           
    def save(self, key, id, payload):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO data (key, id, payload) VALUES (?, ?, ?)',
                            (key, id, json.dumps(payload)))
    
    def load(self, key, id):
        cursor = self.db.execute('SELECT payload FROM data WHERE key = ? AND id = ?', (key, id))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else None
    
    def find(self, key):
        cursor = self.db.execute('SELECT id, payload FROM data WHERE key = ?', (key,))
        return [(row[0], json.loads(row[1])) for row in cursor.fetchall()]

    def all(self):
        cursor = self.db.execute('SELECT id, payload, key FROM data')
        return [(row[2], row[0], json.loads(row[1])) for row in cursor.fetchall()]
    
class TransformStep:
  def __init__(self, step:str, outkey:str, inkey:str = None, **params):
    self.step = step
    self.inkey = inkey
    self.outkey = outkey
    self.params = params
    
    self.core = None
    self.enabled = False
    
  def run(self, id, input):
    raise Exception('run() must be implemented.')

  def pending_inputs(self):
    inputs = self.core.find(self.inkey)
    outputs = [x[0] for x in self.core.find(self.outkey)]
    return [ (input_id, payload) for input_id, payload in inputs if input_id not in outputs ]

  def setup(self, core):
    self.core = core
    
class GenerateStep(TransformStep):
  def __init__(self, step:str, outkey:str, **params):
    super().__init__(step, outkey, None, **params)
    
  def pending_inputs(self):
    num_samples = int(self.params.get('num_samples', '0'))
    if not num_samples: raise Exception(f'{self.step} requires a num_samples parameter.')
    outputs = [x[0] for x in self.core.find(self.outkey)]
    return [ (str(uuid.uuid4()), None) for _ in range(max(0,num_samples - len(outputs))) ]

class StepExpandTemplate(TransformStep):
    def run(self, id, input):
        input = json.loads(input)
        tpl = Template(self.params.get('template'))
        text = tpl.render(**input)        
        return text, {}
        
class StepLLMCompletion(TransformStep):
    def run(self, id, input):
        self.model = self.params.get('model')
        self.tokenizer = self.params.get('tokenizer')
        self.completion_tokenizer = build_tokenizer(self.tokenizer) if self.tokenizer else None
        # TODO: interface to configure this
        self.sampler = {
            'temperature': 1.0,
            'min_p': 0.05,
            'repetition_penalty': 1.1,
            'max_tokens': 2048,
            'min_tokens': 10 
        }
                        
        if not self.model: raise Exception(f"LLMCompletion {self.step} requires model parameter.")
                
        meta = {
            'timestamp': time.time(),
            'model': self.model,
            'tokenizer': self.tokenizer,
            'sampler': self.sampler
        }        
        messages = [{'role': 'user', 'content': input}]
        if self.completion_tokenizer:
            messages = [{"role": "user", "content": self.completion_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, bos_token='')}]
        answers = universal_llm_request(self.completion_tokenizer != None, self.model, messages, self.sampler, 1)        
        return answers[0], meta

class StepLLMExtraction(TransformStep):
    def run(self, id, input):
        self.model = self.params.get('model')   
        self.schema_mode = self.params.get('schema_mode','none')
        self.max_tokens = int(self.params.get('max_tokens', '3000'))

        if not self.model: raise Exception(f"LLMExtraction {self.step} requires model parameter.")

        messages = [{'role': 'user', 'content': self.params['prompt']+"\n\n"+input}]
        sampler = { 'temperature': 0.0, 'max_tokens': self.max_tokens }
        
        if self.schema_mode == "none": 
            pass
        elif self.schema_mode == "openai-schema":
            sampler['response_format'] = { 'type': "json_schema", 'json_schema': {"strict": True, "name": "WorldList", "schema": self.params['schema_json'] } }
        elif self.schema_mode == "openai-json":
            sampler['response_format'] = { 'type': "json_object" }
        elif self.schema_mode == "vllm":
            sampler['guided_json'] = self.params['schema_json']
        elif self.schema_mode == "llama":
            sampler['json_schema'] = self.params['schema_json']
        else:
            raise Exception("bad schema_mode")

        meta = {
            'timestamp': time.time(),
            'model': self.model,
            'sampler': sampler
        }
                    
        answers = universal_llm_request(False, self.model, messages, sampler, 1)       
        data = simple_extract_json(answers[0])        
        return json.dumps(data), meta
    
    # def parallel_generator(self, num_parallel, num_samples, params, n):      
    #     with ThreadPoolExecutor(max_workers=num_parallel) as executor:
    #         prompts = [ self._build_prompt() for _ in range(num_samples)]
    #         futures = [executor.submit(self._process_prompt, messages, params, n, vars) for messages, vars in prompts]           
    #         with tqdm(total=len(prompts), desc="Processing prompts", unit="prompt") as pbar:
    #             for future in as_completed(futures):
    #                 ideas = future.result()
    #                 for idea in ideas:
    #                     yield idea
    #                 pbar.update(1)

    # def make_output_filename(self, prefix):
    #     # Extract the model name after the last '/'
    #     model_name = self.model.split('/')[-1]
    #     # Replace any non-alphanumeric characters with underscores
    #     safe_model_name = re.sub(r'[^a-zA-Z0-9]', '_', model_name)
    #     current_time = int(time.time())
    #     return f"{prefix}_{safe_model_name}_{current_time}.json"

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scribe CLI")
    parser.add_argument("--project", type=str, required=True, help="Project name")
    args = parser.parse_args()
    
    sc = SQLiteScribe(project=args.project)
    docs = sc.all()
    for key, id, content in docs:
        print(id, key, str(content)[0:40])
