from llm_tools import build_tokenizer, universal_llm_request, simple_extract_json
from jinja2 import Template
import uuid
import time

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
        return data, meta
    
