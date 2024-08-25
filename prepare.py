import json
import sys
import uuid
from typing import List, Dict
from cleaner import World
from pydantic import Field

class WorldID(World):
    id: str = Field(description='Unique identifier for the world')
    idea_id: int = Field(description='ID of the original idea')

def read_and_process_file(input_filename: str) -> tuple[List[WorldID], List[Dict]]:
    worlds = []
    errors = []
    ideas = []

    with open(input_filename, 'r') as f:
        for idea_id, line in enumerate(f, start=1):
            data = json.loads(line)
            ideas.append(data)

            if 'clean_error' in data:
                errors.append({'idea_id': idea_id, 'error': data['clean_error']})
            elif 'clean' in data:
                if 'worlds' not in data['clean']:
                    errors.append({'idea_id': idea_id, 'error': 'no worlds'})
                    
                for world in data['clean']['worlds']:
                    world['id'] = str(uuid.uuid4())
                    world['idea_id'] = idea_id
                    for key, value in world.items():
                        if isinstance(value, list):
                            world[key] = '\n'.join([f"{idx+1}. {v}" for idx,v in enumerate(value)])
                        if isinstance(value, dict):
                            world[key] = '\n'.join([f"* {k}: {v}" for k,v in value.items()])
                    worlds.append(WorldID(**world))

    return worlds, errors, ideas

def main():
    input_filename = sys.argv[1]
    output_filename = input_filename.replace('cleaner','prepare')
    if output_filename == input_filename: output_filename = 'prepare.json'

    worlds, errors, ideas = read_and_process_file(input_filename)
    with open(output_filename, 'w') as f:
        json.dump({ 'worlds': [world.model_dump() for world in worlds], 'ideas': ideas }, f, indent=2)
   
    print(f"Total number of output worlds: {len(worlds)}")
    print(f"Prepared data written to {output_filename}")
    
    if len(errors) > 0:
        print("\nRecords with clean_error:")
        for error in errors:
            print(f"Idea ID: {error['idea_id']}, Error: {error['error']}")

if __name__ == "__main__":
    main()
