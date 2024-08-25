import json
import sys
import hashlib
from typing import List, Dict
from cleaner import World
from pydantic import Field

class WorldID(World):
    id: str = Field(description='Unique identifier for the world')
    idea_id: int = Field(description='ID of the original idea')

def read_and_process_files(input_filenames: List[str]) -> tuple[List[WorldID], List[Dict], List[Dict]]:
    worlds = []
    errors = []
    ideas = []
    global_idea_id = 0

    for input_filename in input_filenames:
        with open(input_filename, 'r') as f:
            for line in f:
                data = json.loads(line)
                data['idea_id'] = global_idea_id
                ideas.append(data)

                if 'clean_error' in data:
                    errors.append({'idea_id': global_idea_id, 'error': data['clean_error']})
                elif 'clean' in data:
                    if 'worlds' not in data['clean']:
                        errors.append({'idea_id': global_idea_id, 'error': 'no worlds'})
                    else:                        
                        for world in data['clean']['worlds']:
                            world['id'] = hashlib.md5(data['result'].encode()).hexdigest()
                            world['idea_id'] = global_idea_id
                            for key, value in world.items():
                                if isinstance(value, list):
                                    world[key] = '\n'.join([f"{idx+1}. {v}" for idx,v in enumerate(value)])
                                if isinstance(value, dict):
                                    world[key] = '\n'.join([f"* {k}: {v}" for k,v in value.items()])
                            worlds.append(WorldID(**world))

                global_idea_id += 1

    return worlds, errors, ideas

def main():
    if len(sys.argv) < 2:
        print("Usage: python prepare.py <input_file1> [<input_file2> ...]")
        sys.exit(1)

    input_filenames = sys.argv[1:]
    output_filename = 'prepare.json'

    worlds, errors, ideas = read_and_process_files(input_filenames)
    with open(output_filename, 'w') as f:
        json.dump({ 'worlds': [world.model_dump() for world in worlds], 'ideas': ideas }, f, indent=2)
   
    print(f"Total number of input files: {len(input_filenames)}")
    print(f"Total number of output worlds: {len(worlds)}")
    print(f"Prepared data written to {output_filename}")
    
    if len(errors) > 0:
        print("\nRecords with clean_error:")
        for error in errors:
            print(f"Idea ID: {error['idea_id']}, Error: {error['error']}")

if __name__ == "__main__":
    main()
