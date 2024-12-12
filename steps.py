from llm_tools import build_tokenizer, universal_llm_request, simple_extract_json
from jinja2 import Template
import uuid
import time
import requests
import os

class TransformStep:
  def __init__(self, step:str, outkey:str, inkey:str = None, **params):
    self.step = step
    self.inkey = inkey
    self.outkey = outkey
    self.params = params
    
    self.core = None
    self.queue = None
    self.futures = {}
    
  def run(self, id, input):
    raise Exception('run() must be implemented.')

  def pending_inputs(self, all_inputs = None, all_outputs = None):
    if all_inputs is None: all_inputs = self.core.find(key=self.inkey)
    if all_outputs is None: all_outputs = self.core.find(key=self.outkey)
    inputs = [ (id, payload) for key, id, payload, meta in all_inputs if payload ]
    outputs = [ id for key, id, payload, meta in all_outputs ]
    queued = list(self.futures.keys())
    return [ (input_id, payload) for input_id, payload in inputs if input_id not in outputs and input_id not in queued ]

  def setup(self, core):
    self.core = core

  def queue_full(self):
    qdepth = self.params.get('qdepth')
    if qdepth is None: return False
    return len(self.unfinished_futures()) >= int(qdepth)

  def unfinished_futures(self):
    if self.queue is None: return []
    return [future for id, future in self.futures.items() if not future.done()]
        
class GenerateStep(TransformStep):
  def __init__(self, step:str, outkey:str, **params):
    super().__init__(step, outkey, None, **params)
    
  def pending_inputs(self):
    num_samples = int(self.params.get('max', '0'))
    if not num_samples: raise Exception(f'{self.step} requires a max parameter.')
    outputs = [x[0] for x in self.core.find(self.outkey)]
    return [ (str(uuid.uuid4()), None) for _ in range(max(0,num_samples - len(outputs))) ]

class StepExpandTemplate(TransformStep):
    def run(self, id, input):
        tpl = Template(self.params.get('template'))
        text = tpl.render(**input)        
        return text, {}
        
class StepLLMCompletion(TransformStep):
    def pending_inputs(self):        
        all_inputs = self.core.find(key=self.inkey)
        all_outputs = self.core.find(key=self.outkey)
        
        model_max = self.params.get('model_max')
        if model_max is not None: 
            model = self.params.get('model')
            model_max = int(model_max)
            model_count = len([id for key, id, payload, meta in all_outputs if meta is not None and meta['model'] == model])
            if model_count >= model_max:
                print(f"{self.step} hit model_max={model_max} for model={model}")
                return []
        
        # Original logic if model_max isn't hit.
        return super().pending_inputs(all_inputs, all_outputs)
    
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

class StepLLMExtraction(StepLLMCompletion):
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

class StepText2Image(TransformStep):
    def run(self, id, input):
        width = int(self.params.get('width', 512))
        height = int(self.params.get('height', 512))
        steps = int(self.params.get('steps', 20))

        payload = {
            "prompt": input,
            "steps": steps,
            "width": width,
            "height": height
        }
        
        IMAGE_API_URL = os.getenv('IMAGE_API_URL', 'http://127.0.0.1:5001')
        response = requests.post(url=f"{IMAGE_API_URL}/sdapi/v1/txt2img", json=payload)
        
        if response.status_code != 200:
            raise Exception(f"AUTOMATIC1111 API request failed with status code {response.status_code}")

        r = response.json()
        image = r['images'][0]
        
        meta = {
            'timestamp': time.time(),
            'width': width,
            'height': height,
            'steps': steps
        }

        return image, meta
