from datasets import Dataset, Image
import json

with open('prepare.json') as f:
    data = json.load(f)

worlds = data['worlds']
ideas = data['ideas']
idea_map = { x['idea_id']: x for x in ideas }
   
def clean_model(model):
    return model.split('/')[-1] if '/' in model else model

def add_image(world):
    new_world = {}
    
    new_world['image'] = 'static/'+world['id']+'.jpg'
    
    for k,v in world.items():
        if k in ['idea_id']: continue
        new_world[k] = v
    
    idea = idea_map[world['idea_id']]
    new_world['size'] = 'big'
    new_world['model'] = clean_model(idea['model'])
    new_world['technique'] = idea['vars']['title']
    new_world['random_words'] = idea['vars']['random_words']
        
    return new_world

world_merged = list(map(add_image, worlds))

dataset = Dataset.from_list(world_merged).cast_column("image", Image())
print(dataset)

dataset.push_to_hub('mike-ravkine/AlteredWorlds')
