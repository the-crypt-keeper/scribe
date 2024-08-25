import time
from utils import get_llm_response, get_output_filename
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
    story_seeds: str = Field(description = 'Story ideas or conflicts that could arise in this world')
    sensory: str = Field(description='Specific sensory information about the world')
    challenges_opportunities: str = Field(description='Difficulties or opportunities faced by inhabitants of this world')
    
class WorldList(BaseModel):
    worlds: list[World]

SYSTEM_PROMPT = """The text provided by the user describes a number of Worlds, providing sections of information for each one.

Convert it to a list of JSON object with the following schema:

{ 'worlds': [
    {
        world_name: "<The World Name>",
        concept: "<The way in which the concept was applied to create this world>",
        description: "<Description of the world>",
        twist: "<Unique Twist that makes this world interesting>",
        story_seeds: "<Story ideas or conflicts that could arise in this world>",
        sensory: "<Specific sensory information about the world>",
        challenges_opportunities: "<Difficulties or opportunities faced by inhabitants of this world>"
    },
    {
        ... same as above for next world
    }
]}

If the user text does not contain a list of worlds, return an empty list: `{ 'worlds': [] }`

### INPUT:
"""

SYSTEM_TEMPLATE = Template(SYSTEM_PROMPT)

MODEL = 'openai/Mistral-7B-Instruct-v0.3-GPTQ-4bit'
NUM_PARALLEL = 4
SCHEMA = WorldList.model_json_schema()

def process_prompt(data, text_key):
    if 'clean' in data:
        return data

    user_text = data.get(text_key, '')
    if user_text.strip() == '': return None
    
    messages = [{'role': 'user', 'content': SYSTEM_PROMPT+user_text}]
    sampler = { 'temperature': 0.0, 'max_tokens': 3072 }
    sampler['guided_json'] = SCHEMA
    
    answer = None
    try:
        answer = get_llm_response(messages, MODEL, **sampler)       
        clean_data = json.loads(answer)
        data['clean'] = clean_data
    except Exception as e:
        data['clean_error'] = str(e)
        data['clean_raw'] = answer

    data['clean_timestamp'] = time.time()
    data['clean_model'] = MODEL
    return data

def run(input_file: str, key_name: str = 'result'):
    output_filename = input_file.replace('ideas','cleaner')
    outf = open(output_filename, 'w')

    with open(input_file, 'r') as f:
        data = [json.loads(line) for line in f]

    total_prompts = len(data)
    
    with ThreadPoolExecutor(max_workers=NUM_PARALLEL) as executor:
        futures = [executor.submit(process_prompt, item, key_name) for item in data]
        
        with tqdm(total=total_prompts, desc="Processing prompts", unit="prompt") as pbar:
            for future in as_completed(futures):
                result = future.result()
                if result is not None: outf.write(json.dumps(result) + '\n')
                pbar.update(1)

    outf.close()

if __name__ == "__main__":
    Fire(run)
