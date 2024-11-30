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

def create_dictionaries():
    import nltk
    from nltk.corpus import words, brown
        
    nltk.download('brown', quiet=True)
    nltk.download('words', quiet=True)
    
    basic_words = words.words('en-basic')
    advanced_words = list(set(brown.words(categories=['adventure','fiction','humor','science_fiction','romance'])))
    
    with open('basic.txt', 'w') as f:
        for word in sorted(basic_words):
            f.write(f"{word}\n")
    
    with open('advanced.txt', 'w') as f:
        for word in sorted(advanced_words):
            if not (word[0].isdigit() or word[0].isalpha()): continue
            f.write(f"{word}\n")

class Scribe():
    def __init__(self, project, arglist):
        self.project = project
        self.arglist = arglist
        
        self.steps = {}
        
    def add_step(self, step):
        assert step.step not in self.steps
        step.setup(self, self.arglist)
        self.steps[step.step] = step

    def save(self, key, id, payload):
        pass
    
    def load(self, key, id):
        pass
    
    def find(self, key):
        pass
    
    def run_single_step(self, step_name):
        step = self.steps[step_name]      
        inputs = []
        
        if step.input is None:
            num_samples = step.params.get('num_samples')
            if num_samples is None: raise Exception('Pipeline step without input requires a num_samples parameter.')
            outputs = self.find(step.outkey)
            if len(outputs) < num_samples:
                inputs = [ (str(uuid.uuid4()), None) for _ in range(num_samples - len(outputs)) ]
        else:
            inputs = self.find(step.inkey)
        
        for id, input in inputs:
            if self.load(self.outkey, id) is None:
                print(f"{self.step} executing {id}")
                output, meta = self.step(id, input)
                if output is not None:
                    self.save(self.outkey, id, output)
                    self.save('_'+self.outkey, id, meta)

import sqlite3

class SQLiteScribe(Scribe):
    def __init__(self, project, arglist):
        super().__init__(project, arglist)
        
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

class PipelineStep:  
  def __init__(self, step:str, outkey:str, inkey:str = None, **params):
    self.step = step
    self.inkey = inkey
    self.outkey = outkey
    self.params = params
    self.core = None
    
  def step(self, id, input):
    raise Exception('step() must be implemented.')

  def setup(self, core, arglist):
    self.core = core

class StepExpandTemplate(PipelineStep):
    def generate_input(self):
        raise Exception('generate_input() must be implemented to use this Step without an input key.')
    
    def step(self, id, input):
        input = self.generate_input() if input is None else json.loads(input)
        tpl = Template(self.params.get('template'))
        text = tpl.render(**input)        
        return text, {}

class StepExpandTemplateWoldLists(StepExpandTemplate):
    def setup(self, core, arglist):
        super().setup(core, arglist)
                
        self.word_lists = {}
        if not os.path.isfile('basic.txt'): create_dictionaries()
        self.load_word_list('basic.txt', 'basic')
        self.load_word_list('advanced.txt', 'advanced')           

    def load_word_list(self, filename, list_name):
        with open(filename, 'r') as f:
            self.word_lists[list_name] = f.read().splitlines()

    def get_random_words(self, list_name, num_words):
        return random.sample(self.word_lists[list_name], num_words)
        
class StepLLMCompletion(PipelineStep):
    def setup(self, core, arglist):
        super().setup(core, arglist)
        
        self.model = self.arglist.get(f'{self.step}:model')
        if not self.model: raise Exception(f"LLMCompletion {self.step} requires model parameter.")
        
        self.tokenizer = self.arglist.get(f'{self.step}:tokenizer')        
        self.completion_tokenizer = build_tokenizer(self.tokenizer) if self.tokenizer else None
        
        # TODO: interface to configure this
        self.sampler = {
            'temperature': 1.0,
            'min_p': 0.05,
            'repetition_penalty': 1.1,
            'max_tokens': 2048,
            'min_tokens': 10 
        }
    
    def step(self, id, input):
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

class StepLLMExtraction(PipelineStep):
    def setup(self, core, arglist):
        self.core = core
        self.model = self.arglist.get(f'{self.step}:model')
        if not self.model: raise Exception(f"LLMExtraction {self.step} requires model parameter.")
        
        self.schema_mode = self.arglist.get(f'{self.step}:schema_mode', 'none')
        self.max_tokens = int(self.arglist.get(f'{self.step}:max_tokens', '3000'))

    def step(self, id, input):    
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
