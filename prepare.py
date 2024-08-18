import json
import sys
import uuid
from typing import List
from pydantic import BaseModel, Field

class World(BaseModel):
    id: str = Field(description='Unique identifier for the world')
    world_name: str = Field(description='The World Name')
    concept: str = Field(description='The way in which the concept was applied to create this world')
    description: str = Field(description='Description of the world')
    twist: str = Field(description='Unique Twist that makes this world interesting')
    idea_id: int = Field(description='ID of the original idea')

class PreparedData(BaseModel):
    worlds: List[World]

def read_and_process_file(input_filename: str) -> PreparedData:
    worlds = []

    with open(input_filename, 'r') as f:
        for idea_id, line in enumerate(f, start=1):
            data = json.loads(line)

            if 'clean' in data and 'worlds' in data['clean']:
                for world in data['clean']['worlds']:
                    world['id'] = str(uuid.uuid4())
                    world['idea_id'] = idea_id
                    worlds.append(World(**world))

    return PreparedData(worlds=worlds)

def write_output(prepared_data: PreparedData, output_filename: str):
    with open(output_filename, 'w') as f:
        json.dump(prepared_data.model_dump()['worlds'], f, indent=2)

def main():
    input_filename = sys.argv[1]
    output_filename = 'prepare.json'

    prepared_data = read_and_process_file(input_filename)
    write_output(prepared_data, output_filename)
    print(f"Prepared data written to {output_filename}")

if __name__ == "__main__":
    main()
