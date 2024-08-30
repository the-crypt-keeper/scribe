import time
from utils import get_llm_response, get_llama_completion
import json
from jinja2 import Template
from fire import Fire
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pydantic import BaseModel, Field
from typing import List

class World(BaseModel):
    world_name: str = Field(description='The World Name')
    concept: str = Field(description='The way in which the concept was applied to create this world')
    description: str = Field(description = 'Description of the world')
    twist: str = Field(description = 'Unique Twist that makes this world interesting')
    story_seeds: List[str] = Field(description = 'Story ideas or conflicts that could arise in this world')
    sensory: str = Field(description='Specific sensory information about the world')
    challenges_opportunities: str = Field(description='Difficulties or opportunities faced by inhabitants of this world')
    
class WorldList(BaseModel):
    worlds: list[World]

SYSTEM_PROMPT = """The text provided by the user describes imaginary worlds and is always organized into 7 sections: Concept, World Name, Description, Twist, Sensory Details, Story Seeds, Challenges and Opportunities.

FULLY AND COMPLETELY map the user input into a list of JSON objects with the following schema:

{
    "concept": "<Concept including key principles or elements>",
    "world_name": "<The World Name>",
    "description": "<Description>",
    "twist": "<Twist>",
    "story_seeds": ["<A story idea that could arise in this world>","<another story idea...>"],
    "sensory": "<Sensory Details>",
    "challenges_opportunities": "<Difficulties or opportunities faced by inhabitants of this world>"
}

INSTRUCTIONS:
* All fields are required.
* Preserve sub-headings.
* Escape quotes, convert any newlines into \n and otherwise ensure the output JSON is valid.
* Make sure ALL text between relevant headings is captured"""

SYSTEM_TEMPLATE = Template(SYSTEM_PROMPT)
SCHEMA = WorldList.model_json_schema()

def process_prompt(data, text_key, model, delay, schema_mode):
    if 'clean' in data:
        return data

    user_text = data.get(text_key, '')
    if user_text.strip() == '': return None
    
    #messages = [{'role': 'user', 'content': SYSTEM_PROMPT+"\n\n### INPUT:\n"+user_text}]
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT},{'role': 'user', 'content': user_text}]
    
    sampler = { 'temperature': 0.0, 'max_tokens': 4095 }
    if schema_mode == "none": 
        pass
    elif schema_mode == "openai-schema":
        sampler['response_format'] = { 'type': "json_schema", 'json_schema': {"strict": True, "name": "WorldList", "schema": SCHEMA } }
    elif schema_mode == "openai-json":
        sampler['response_format'] = { 'type': "json_object" }
    elif schema_mode == "vllm":
        sampler['guided_json'] = SCHEMA
    elif schema_mode == "llama":
        sampler['json_schema'] = SCHEMA
    else:
        raise Exception("bad schema_mode")
    
    answer = None
    try:
        if model[0:6] == 'llama/':
            answer = get_llama_completion(messages, model, **sampler)            
        else:
            answer = get_llm_response(messages, model, **sampler)
        
        if schema_mode == 'none':
            first_obj = answer.find('{')
            last_obj = answer.rfind('{')
            first_list = answer.find('[')
            last_list = answer.rfind(']')
            if first_list is None or first_obj < first_list:
                clean_answer = answer[first_obj:last_obj+1]
            else:
                clean_answer = answer[first_list:last_list+1]
        else:
            clean_answer = answer
            
        clean_data = json.loads(clean_answer)
        data['clean'] = clean_data
    except Exception as e:
        data['clean_error'] = str(e)
        data['clean_raw'] = answer

    data['clean_timestamp'] = time.time()
    data['clean_model'] = model
    if delay > 0: time.sleep(delay)
    return data

def run(input_file: str, model: str = 'openai/Mistral-Nemo-Instruct-2407-gptq-4bit', num_parallel : int = 2, delay : int = 0, key_name: str = 'result', schema : str = "vllm"):
    output_filename = input_file.replace('ideas','cleaner')
    outf = open(output_filename, 'w')

    with open(input_file, 'r') as f:
        data = [json.loads(line) for line in f]

    total_prompts = len(data)
    
    with ThreadPoolExecutor(max_workers=num_parallel) as executor:
        futures = [executor.submit(process_prompt, item, key_name, model, delay, schema) for item in data]
        
        with tqdm(total=total_prompts, desc="Processing prompts", unit="prompt") as pbar:
            for future in as_completed(futures):
                result = future.result()
                if result is not None: outf.write(json.dumps(result) + '\n')
                pbar.update(1)

    outf.close()

if __name__ == "__main__":
    Fire(run)
