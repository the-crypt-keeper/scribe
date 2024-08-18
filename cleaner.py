import time
from utils import get_llm_response, get_output_filename
import re
import random
import sys
import json
from jinja2 import Template
from fire import Fire
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from pydantic import BaseModel, Field

class World(BaseModel):
    world_name: str = Field(description='The World Name')
    concept: str = Field(description='The way in which the concept was applied to create this world')
    description: str = Field(description = 'Description of the world')
    twist: str = Field(description = 'Unique Twist that makes this world interesting')
    
class WorldList(BaseModel):
    worlds: list[World]

SYSTEM_PROMPT = "Convert the following text provided by the user into a list of JSON objects with the keys { world_name, concept, description, twist }:\n\n{{text}}"
SYSTEM_TEMPLATE = Template(SYSTEM_PROMPT)

MODEL = 'openai/Mistral-7B-Instruct-v0.3-GPTQ-4bit'
NUM_PARALLEL = 4  # Default number of parallel threads

schema = WorldList.model_json_schema()


def process_prompt(data):
    if 'clean' in data:
        return data

    user_text = data.get('user_text', '')
    messages = [{'role': 'user', 'content': SYSTEM_TEMPLATE.render(text=user_text)}]    
    sampler = { 'temperature': 0.0 }
    sampler['guided_json'] = schema
    
    try:
        answer = get_llm_response(messages, MODEL, seed=random.randint(0, 65535), **sampler)
        clean_data = json.loads(answer)
        data['clean'] = clean_data
    except Exception as e:
        data['clean_error'] = str(e)

    data['timestamp'] = time.time()
    data['model'] = MODEL
    return data

def run(input_file: str, key_name: str):
    output_filename = get_output_filename(MODEL, 'cleaner')
    outf = open(output_filename, 'w')

    with open(input_file, 'r') as f:
        data = [json.loads(line) for line in f]

    total_prompts = len(data)
    
    with ThreadPoolExecutor(max_workers=NUM_PARALLEL) as executor:
        futures = [executor.submit(process_prompt, item) for item in data]
        
        with tqdm(total=total_prompts, desc="Processing prompts", unit="prompt") as pbar:
            for future in as_completed(futures):
                result = future.result()
                outf.write(json.dumps(result) + '\n')
                pbar.update(1)

    outf.close()

if __name__ == "__main__":
    Fire(run)
