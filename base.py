import random
import time
import os
import re
import uuid
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from llm_tools import build_tokenizer, universal_llm_request
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
    def __init__(self, model):
        self.model = model
        self.word_lists = {}
        if not os.path.isfile('basic.txt'): create_dictionaries()
        self.load_word_list('basic.txt', 'basic')
        self.load_word_list('advanced.txt', 'advanced')        
        self.chat_mode()
        
    def completion_mode(self, tokenizer):
        self.completion = True
        self.completion_tokenizer = build_tokenizer(tokenizer)
        
    def chat_mode(self):
        self.completion = False
        self.completion_tokenizer = None

    def load_word_list(self, filename, list_name):
        with open(filename, 'r') as f:
            self.word_lists[list_name] = f.read().splitlines()

    def get_random_words(self, list_name, num_words):
        return random.sample(self.word_lists[list_name], num_words)
    
    def generate_vars(self):
        raise Exception("Implement me.")
    
    def prompt_template(self):
        raise Exception("Implement me.")
    
    def _build_prompt(self):
        vars = self.generate_vars()
        tpl = Template(self.prompt_template())
        text = tpl.render(**vars)
        messages = [{'role': 'user', 'content': text}]
        
        if self.completion_tokenizer:
          vars['tokenizer'] = self.completion_tokenizer.name_or_path
          messages = [{"role": "user", "content": self.completion_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, bos_token='')}]

        return (messages, vars)

    def _process_prompt(self, messages, params, n, vars):
        answers = universal_llm_request(self.completion, self.model, messages, params, n)           
        ideas = [{'timestamp': time.time(), 'uuid': str(uuid.uuid4()), 'model': self.model, 'result': answer, 'vars': vars} for answer in answers]
        return ideas
    
    def parallel_generator(self, num_parallel, num_samples, params, n):      
        with ThreadPoolExecutor(max_workers=num_parallel) as executor:
            prompts = [ self._build_prompt() for _ in range(num_samples)]
            futures = [executor.submit(self._process_prompt, messages, params, n, vars) for messages, vars in prompts]           
            with tqdm(total=len(prompts), desc="Processing prompts", unit="prompt") as pbar:
                for future in as_completed(futures):
                    ideas = future.result()
                    for idea in ideas:
                        yield idea
                    pbar.update(1)

    def make_output_filename(self, prefix):
        # Extract the model name after the last '/'
        model_name = self.model.split('/')[-1]
        # Replace any non-alphanumeric characters with underscores
        safe_model_name = re.sub(r'[^a-zA-Z0-9]', '_', model_name)
        current_time = int(time.time())
        return f"{prefix}_{safe_model_name}_{current_time}.json"
