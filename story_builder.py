import time
from utils import get_llama_completion, get_llm_response, get_output_filename, build_tokenizer
import re
import random
import json
from jinja2 import Template
import nltk
from nltk.corpus import words, brown
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import fire

TITLE = "The Range Beyond"

OUTLINE = """#### Chapter 1: The Last Marker

In the year 2550, the world is a parched husk. Water, once taken for granted, is now a precious commodity. The capital city of Fallen Arbor, nestled near what remains of Lake Superior, is a hub of opulence where water is meticulously rationed among the elite. To the south lies Ironhaven, a settlement teetering on the edge of prosperity and struggle. Beyond the city’s reach, the barren lands of the Range stretch out, an unforgiving expanse of desolation and danger.

Grizwald Chambers, a stoic and weathered ex-special forces officer, is deep in the heart of Ironhaven. His office is cluttered with dusty relics and half-finished investigations. He’s approached by Audrie Holmes, a strikingly beautiful woman with a desperate plea. Her brother, Ethan Holmes, a brilliant scientist, vanished while on a mission to the last marker—a forbidden boundary leading into the perilous Range. She offers Grizwald a hefty sum to find him.

#### Chapter 2: Into the Forbidden

Griz and Audrie begin their perilous journey toward the final marker, a grim landmark that represents the edge of civilization. Their travel is initially uneventful until they encounter a ragtag band of criminals. The skirmish is tense but relatively minor, with Grizwald’s experience and quick thinking ensuring their escape. They dodge a grim fate, using the environment to their advantage. Their pursuers are left tied up, submerged in barrels of water, or buried under debris.

After passing the final marker, the landscape transforms. The dry expanse of the Range stretches out before them. They forge ahead, hoping to find clues about Ethan. Their journey is grueling, with every mile revealing new hazards. It is in this forbidding terrain that they encounter the Dusty Nomads, led by the seasoned Wren King. Wren, having heard tales of Ethan, joins them, revealing that Ethan was heading towards the mountains of Colorado, rumored to harbor an oasis.

#### Chapter 3: Bonds Forged in the Dust

The journey through the Range is fraught with danger. The group is soon ambushed by a ruthless band of scavengers. The battle is brutal and chaotic. Grizwald’s exceptional marksmanship and Wren’s surprising skill with blades turn the tide in their favor. Wren, wounded, reveals his skill with a knife, a talent that surprises even his closest allies. They salvage some valuable equipment from the bandits, including a Remington revolver and ammo.

As the group makes camp, they share stories around the fire. Grizwald speaks of his past in the military and the loss of his young son during the water wars. Audrie shares memories of her brother Ethan, her childhood with him, and her struggles against being underestimated due to her looks. Wren, the ever-silent leader, listens, revealing little of his past, but his actions speak of his deep care for his people.

#### Chapter 4: The Oasis Revealed

The final approach to the oasis is treacherous. The party encounters soldiers from Dripstone Haven, the city to the south. The oasis is heavily guarded, and a fierce confrontation ensues. Wren is gravely wounded in the fight. The oasis itself is a lush paradise amidst the arid wasteland, a stark contrast to the world outside. The battle is intense, and they manage to defeat the soldiers, but not without cost. Grizwald executes the lone survivor to extract crucial information about Ethan, confirming that he was taken prisoner and headed back towards Dripstone Haven.

#### Chapter 5: An Unexpected Revelation

Elder Shaun, who has been a silent, non-combatant guide, is sent back to the Duster camp for aid while the others make camp by the oasis. In their moment of respite, romance blossoms between Griz and Audrie, their shared experiences forging a deeper connection. As Elder Shaun returns with reinforcements—a skilled fighter with a bowstaff and another with a bow—their journey is poised to continue.

The story ends with the group waiting for the rescue party amidst the serenity of the oasis. The first kiss between Griz and Audrie marks the beginning of something new as they face the uncertain future together. The expedition's continuation is left open-ended, hinting at further adventures and discoveries.

#### Epilogue: The Road Ahead

The journey from Fallen Arbor to Dripstone Haven has been long and fraught with peril, spanning approximately four months. With the oasis discovered and Ethan’s fate now a matter of high importance, the story is far from over. The world is a harsh place, but amidst the desolation, hope flickers in the form of new alliances and burgeoning love. As the dust settles, new chapters await in the unforgiving Range and beyond.
"""

SYSTEM_PROMPT = """Let's engage in a creative writing session, we will be working on a project titled "{{ title }}".

Use this outline of the story, setting, characters and key plot events to answer all user queries and inform your writing:

{{ outline }}

Paint a vivid picture of the world's environment, including its geography, climate, and unique features.  Characters should interact in interesting ways.
"""

SYSTEM_TEMPLATE = Template(SYSTEM_PROMPT)

TASKS = {
    'scene_beats': "Let's work on Chapter {{ chapter_number }}: {{ chapter_name }}. Start with breaking the chapter into scenes. Then for each scene, let's write a list of scene beats followed by a scene summary."
}

SAMPLER = {
    'temperature': 1.0,
    'min_p': 0.05,
    'repetition_penalty': 1.1,
    'max_tokens': 3072,
    'min_tokens': 10 
}

def generate_prompts(num_samples, tokenizer=None):
    # prompts = []
    # for _ in range(num_samples):
    #     method = random.choice(TECHNIQUES)
    #     vars = { 'random_words': ', '.join(get_random_words()), **method }
    #     text = SYSTEM_TEMPLATE.render(**vars)            
    #     messages = [{'role': 'user', 'content': text}]
    #     if tokenizer:
    #       vars['tokenizer'] = tokenizer.name_or_path
    #       messages = [{"role": "user", "content": tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, bos_token='')}]            
    #     prompts.append((messages, vars))
    # return prompts
    
    BEATS_PARAMS = [
        { 'chapter_number': 1, 'chapter_name': 'The Last Marker' },
        { 'chapter_number': 2, 'chapter_name': 'Into the Forbidden' },
        { 'chapter_number': 3, 'chapter_name': 'Bonds Forged in the Dust' },
        { 'chapter_number': 4, 'chapter_name': 'The Oasis Revealed' },
        { 'chapter_number': 5, 'chapter_name': 'An Unexpected Revelation' }
    ]
    prompts = []
    TASK_TEMPLATE = Template(TASKS['scene_beats'])
    for task_params in BEATS_PARAMS:
        task_text = TASK_TEMPLATE.render(**task_params)
        messages = [{'role': 'system', 'content': SYSTEM_TEMPLATE.render(title=TITLE, outline=OUTLINE)}, {'role': 'user', 'content': task_text}]    
        if tokenizer:
            vars['tokenizer'] = tokenizer.name_or_path
            messages = [{"role": "user", "content": tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, bos_token='')}]            
        prompts.append((messages, task_params))
        
    return prompts

def process_prompt(args):
    model, messages, vars = args
    if 'llama/' in model:
      answer = get_llama_completion(messages, model, **SAMPLER)
    else:
      answer = get_llm_response(messages, model, **SAMPLER)
    idea = {'timestamp': time.time(), 'model': model, 'result': answer, 'vars': vars}
    return [idea]

def main(model: str, num_samples: int = 50, num_parallel: int = 1, tokenizer: str = None):
    """
    Generate creative world ideas using AI.

    Args:
        model (str): The AI model to use for generation.
        num_iterations (int): Number of iterations per technique. Default is 5.
        num_parallel (int): Number of parallel threads to use. Default is 4.
        tokenizer (str): Optional. The name of the HuggingFace tokenizer to use for pre-processing.
    """
    tokenizer_instance = build_tokenizer(tokenizer)
    output_filename = get_output_filename(model, 'story')
    outf = open(output_filename, 'a')

    prompts = generate_prompts(num_samples, tokenizer_instance)
    total_prompts = len(prompts)
    
    if '/' not in model:
      model = 'openai/'+model if tokenizer is None else 'text-completion-openai/'+model

    with ThreadPoolExecutor(max_workers=num_parallel) as executor:
        futures = [executor.submit(process_prompt, (model, messages, vars)) for messages, vars in prompts]
        
        with tqdm(total=total_prompts, desc="Processing prompts", unit="prompt") as pbar:
            for future in as_completed(futures):
                ideas = future.result()
                for idea in ideas:
                    outf.write(json.dumps(idea) + '\n')
                    outf.flush()
                pbar.update(1)

    outf.close()

if __name__ == "__main__":
    fire.Fire(main)
