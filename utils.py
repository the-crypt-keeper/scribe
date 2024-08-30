import litellm
import json
import os
import re
import time
from transformers import AutoTokenizer

import requests

API_BASE_URL = os.getenv('OPENAI_BASE_URL',"http://100.109.96.89:3333/v1")
API_KEY = os.getenv('OPENAI_API_KEY', "xx-ignored")

def get_output_filename(model, prefix):
    # Extract the model name after the last '/'
    model_name = model.split('/')[-1]
    # Replace any non-alphanumeric characters with underscores
    safe_model_name = re.sub(r'[^a-zA-Z0-9]', '_', model_name)
    current_time = int(time.time())
    return f"{prefix}_{safe_model_name}_{current_time}.json"

def decode_json(response, first_key = True):
    result = response[response.find('{'):response.rfind('}')+1]
    try:
        data = json.loads(result)
        if first_key: data = data.get(list(data.keys())[0])
        return first_key
    except Exception as e:
        print(result)
        print(e)
        return None

def get_llm_response(messages, model, n=1, **params):
    try:
        response = litellm.completion(
            model=model,
            n=n,
            messages=messages,
            api_base=API_BASE_URL,
            api_key=API_KEY,
            **params
        )
        answers = [x.message.content for x in response.choices]
        return answers[0] if n==1 else answers
    except Exception as e:
        print(f"Error in LLM call: {e}")
        return None

def get_llama_completion(messages, model, **params):
    if 'max_tokens' in params:
        params['n_predict'] = params['max_tokens']
    
    payload = {
        'model': model.replace('llama/',''),
        'prompt': messages[0]['content'],
        **params
    }
    
    headers = { 'Authentication': 'Bearer '+API_KEY }
    
    try:
        response = requests.post(API_BASE_URL+'/completions', json=payload, headers=headers)
        return response.json()['content']
    except Exception as e:
        print(f"Error in LLM call: {e}")
        return None
    
def get_llm_response_stream(messages, model, max_tokens=3072, **params):
    try:
        response = litellm.completion(
            model=model,
            messages=messages,
            api_base=API_BASE_URL,
            api_key=API_KEY,
            max_tokens=max_tokens,
            min_tokens=8,
            stream=True,
            **params
        )

        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                print(content, end='', flush=True)
        
        yield full_response
        
    except Exception as e:
        print(f"Error in LLM call: {e}")
        yield None

class InternalTokenizer:    
    def __init__(self, name, fn):
        self.fn = fn
        self.name_or_path = name
        
    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, bos_token=''):
        system = [x['content'] for x in messages if x['role'] == 'system']
        user = [x['content'] for x in messages if x['role'] == 'user']
        assistant = [x['content'] for x in messages if x['role'] == 'assistant']
        
        system = "You are a helpful assistant." if len(system) == 0 else system[0]
        user = user[0]
        assistant = "" if len(assistant) == 0 else assistant[0]
        
        return self.fn(system, user, assistant)

tokenizer_internal = {
    'internal:vicuna': InternalTokenizer('vicuna', lambda system, user, assistant:
f"""SYSTEM: {system}

USER: {user}

ASSISTANT:{assistant}"""),

    'internal:alpaca': InternalTokenizer('alpaca', lambda system, user, assistant:
f"""### Instruction:
{system}

### Input:
{user}

### Response:{assistant}""")
}

def build_tokenizer(tokenizer_name):
    if tokenizer_name is None:
        return None
    elif tokenizer_name in tokenizer_internal:
        return tokenizer_internal[tokenizer_name]
    else: 
        return AutoTokenizer.from_pretrained(tokenizer_name, trust_remote_code=True)