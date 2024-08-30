import json
import sys
import hashlib
from typing import List, Dict
from cleaner import World
from pydantic import Field

class WorldID(World):
    id: str = Field(description='Unique identifier for the world')
    idea_id: str = Field(description='ID of the original idea')

def read_and_process_files(input_filenames: List[str]) -> tuple[List[WorldID], List[Dict], List[Dict], Dict[str, int]]:
    worlds = []
    errors = []
    ideas = []
    worlds_per_file = {}    

    for input_filename in input_filenames:
        file_world_count = 0
        with open(input_filename, 'r') as f:
            for line in f:
                data = json.loads(line)
                data['idea_id'] = hashlib.md5(data['result'].encode()).hexdigest()
                ideas.append(data)

                if 'clean_error' in data:
                    errors.append({'idea_id': data['idea_id'], 'error': data['clean_error'], 'filename': input_filename})
                elif 'clean' in data:
                    clean_len = len(str(data['clean']))
                    result_len = len(data['result'])
                    ratio = clean_len/result_len
                    
                    if ratio < 0.7:
                        print('---')
                        print(data['result'])
                        print(data['clean'])
                        
                        errors.append({'idea_id': data['idea_id'], 'error': f'low clean ratio {ratio:.2f}', 'filename': input_filename})
                        
                    if isinstance(data['clean'], list):
                        data['clean'] = { 'worlds': data['clean'] }
                    
                    if 'worlds' not in data['clean']:
                        errors.append({'idea_id': data['idea_id'], 'error': 'no worlds', 'filename': input_filename})
                    else:                        
                        for world in data['clean']['worlds']:
                            world['idea_id'] = data['idea_id']
                            for k,v in world.items():
                                if isinstance(v, dict): world[k] = '\n'.join([f'{sk}: {sv}' for sk,sv in v.items()])
                            world_key = world['world_name'] + ' ' + world['description']
                            world['id'] = hashlib.md5(world_key.encode()).hexdigest()
                            try:
                                worlds.append(WorldID(**world))
                            except Exception as e:
                                errors.append({'idea_id': data['idea_id'], 'error': 'schema error: '+str(e), 'filename': input_filename})
                            file_world_count += 1
        
        worlds_per_file[input_filename] = file_world_count

    return worlds, errors, ideas, worlds_per_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python prepare.py <input_file1> [<input_file2> ...]")
        sys.exit(1)

    input_filenames = sys.argv[1:]
    output_filename = 'prepare.json'

    worlds, errors, ideas, worlds_per_file = read_and_process_files(input_filenames)
    with open(output_filename, 'w') as f:
        json.dump({ 'worlds': [world.model_dump() for world in worlds], 'ideas': ideas }, f, indent=2)
   
    print(f"Total number of input files: {len(input_filenames)}")
    print(f"Total number of output worlds: {len(worlds)}")
    print(f"Prepared data written to {output_filename}")
    
    print("\nWorlds per input file:")
    for filename, count in worlds_per_file.items():
        print(f"{filename}: {count} worlds")
    
    if len(errors) > 0:
        print("\nRecords with clean_error:")
        for error in errors:
            print(f"Idea ID: {error['idea_id']}, Filename: {error['filename']} Error: {error['error']}")

if __name__ == "__main__":
    main()
