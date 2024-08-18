import time
from utils import get_llm_response, get_output_filename
import re
import random
import sys
import json
from jinja2 import Template
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pydantic import BaseModel, Field

class World(BaseModel):
    concept: str
    world_name: str
    description: str
    twist: str
    
class WorldList(BaseModel):
    worlds: list[World]

SYSTEM_PROMPT = "Convert the text provided by the user into JSON."
SYSTEM_TEMPLATE = Template(SYSTEM_PROMPT)

MODEL = 'openai/Mistral-7B-Instruct-v0.3-GPTQ-4bit'
NUM_PARALLEL = 4  # Default number of parallel threads

schema = WorldList.model_json_schema()

def generate_prompts():
    prompts = []
    messages = [{'role': 'user', 'content': SYSTEM_TEMPLATE.render()}]
    prompts.append(messages)
    return prompts

def process_prompt(args):
    messages = args
    sampler = {
        'temperature': 1.0,
        'min_p': 0.05,
        'repetition_penalty': 1.1
    }
    sampler['guided_json'] = schema
    
    print(sampler)
    
    ideas = []
    answer = get_llm_response(messages, MODEL, seed=random.randint(0, 65535), **sampler)
    idea = {'timestamp': time.time(), 'result': answer, 'model': MODEL}
    ideas.append(idea)
    return ideas

def main():
    output_filename = get_output_filename(MODEL, 'cleaner')
    outf = open(output_filename, 'a')

    prompts = generate_prompts()
    total_prompts = len(prompts)

    with ThreadPoolExecutor(max_workers=NUM_PARALLEL) as executor:
        futures = [executor.submit(process_prompt, prompt) for prompt in prompts]
        
        with tqdm(total=total_prompts, desc="Processing prompts", unit="prompt") as pbar:
            for future in as_completed(futures):
                ideas = future.result()
                for idea in ideas:
                    outf.write(json.dumps(idea) + '\n')
                pbar.update(1)

    outf.close()

main()
