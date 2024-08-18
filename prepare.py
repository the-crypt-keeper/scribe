import json
import sys
from typing import List, Dict
from pydantic import BaseModel, Field

class World(BaseModel):
    world_name: str = Field(description='The World Name')
    concept: str = Field(description='The way in which the concept was applied to create this world')
    description: str = Field(description='Description of the world')
    twist: str = Field(description='Unique Twist that makes this world interesting')
    line_id: int = Field(description='Line ID from the input file')

class PreparedData(BaseModel):
    input_data: List[Dict]
    worlds: List[World]

def read_and_process_file(input_filename: str) -> PreparedData:
    input_data = []
    worlds = []

    with open(input_filename, 'r') as f:
        for line_id, line in enumerate(f, start=1):
            data = json.loads(line)
            data['line_id'] = line_id
            input_data.append(data)

            if 'clean' in data and 'worlds' in data['clean']:
                for world in data['clean']['worlds']:
                    world['line_id'] = line_id
                    worlds.append(World(**world))

    return PreparedData(input_data=input_data, worlds=worlds)

def write_output(prepared_data: PreparedData, output_filename: str):
    with open(output_filename, 'w') as f:
        json.dump(prepared_data.model_dump(), f, indent=2)

def main():
    input_filename = sys.argv[1]
    output_filename = 'prepare.json'

    prepared_data = read_and_process_file(input_filename)
    write_output(prepared_data, output_filename)
    print(f"Prepared data written to {output_filename}")

if __name__ == "__main__":
    main()
