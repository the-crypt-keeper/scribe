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

    with open(input_filename, 'r') as f:
        for idea_id, line in enumerate(f, start=1):
            data = json.loads(line)

            if 'clean_error' in data:
                errors.append({'idea_id': idea_id, 'error': data['clean_error']})
            elif 'clean' in data:
                if 'worlds' not in data['clean']:
                    errors.append({'idea_id': idea_id, 'error': 'no worlds'})
                    
                for world in data['clean']['worlds']:
                    world['id'] = str(uuid.uuid4())
                    world['idea_id'] = idea_id
                    worlds.append(WorldID(**world))
                    
                if len(data['clean']['worlds']) != 3:
                    print('---')
                    print(data['result'])

    return worlds, errors

def write_output(worlds: List[World], output_filename: str):
    with open(output_filename, 'w') as f:
        json.dump([world.model_dump() for world in worlds], f, indent=2)

def main():
    input_filename = sys.argv[1]
    output_filename = 'prepare.json'

    worlds, errors = read_and_process_file(input_filename)
    write_output(worlds, output_filename)
    
    print(f"Total number of output worlds: {len(worlds)}")
    print(f"Prepared data written to {output_filename}")
    
    if len(errors) > 0:
        print("\nRecords with clean_error:")
        for error in errors:
            print(f"Idea ID: {error['idea_id']}, Error: {error['error']}")

if __name__ == "__main__":
    main()
