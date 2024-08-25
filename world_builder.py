import time
from utils import get_llama_completion, get_llm_response, get_output_filename
import re
import random
import json
from jinja2 import Template
import nltk
from nltk.corpus import words, brown
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import fire
from transformers import AutoTokenizer

TECHNIQUES = [
  {
    "title": "Historical Analog Approach",
    "summary": "This method involves taking a historical event or period and transposing it to a new context.",
    "examples": [
      "The Foundation (series, 1951): A series of novels that features a galactic empire inspired by the Roman Empire, with a similar structure and bureaucracy.",
      "Firefly (2002) by Joss Whedon: A TV series that features a future where the American Wild West has been reimagined in a science fiction setting, with cowboys and outlaws living on the edge of the solar system."
    ]
  },
  {
    "title": "Timeline Bend",
    "summary": "Imagine timelines that are similar to our own but have had a significant difference somewhere along their paths.",
    "examples": [
      "The Guns of the South (1992) by Harry Turtledove: A novel that explores a world where the Confederacy won the American Civil War and the Industrial Revolution never occurred.",
      "The Shannara Series (1977) by Terry Brooks: A series of novels that explores a world where magic and technology coexist, and ancient civilizations like the Elves and Dwarves have survived to the present day."
      "The Man in the High Castle (1962) by Philip K. Dick: A novel that explores a world where the Axis powers won World War II, and the United States is divided between the Greater Nazi Reich and the Japanese Pacific States.",
      "The Yiddish Policemen's Union (2007) by Michael Chabon: A novel that explores a world where Israel was destroyed in 1948, and Jewish refugees settled in Alaska, creating a unique cultural and linguistic identity."
    ]
  },
  {
    "title": "What If Scenario",
    "summary": "This approach involves asking a question like 'What if gravity worked differently?' or 'What if magic was real?' and then building a world around the consequences of that scenario.",
    "examples": [
      "Inception (2010): What if dreams could be shared and manipulated?",
      "The Matrix (1999): What if reality was a simulated world created by machines?",
      "Interstellar (2014): What if wormholes could be used for faster-than-light travel?"
    ]
  },
  {
    "title": "Ecological Divergence Method",
    "summary": "This approach involves taking a real-world ecosystem and altering one or more key factors, such as the dominant species, climate, or geography.",
    "examples": [
      "Avatar (2009): A world where giant, sentient trees and a network of energy-filled vines have created a unique ecosystem.",
      "The Dark Crystal (1982): A world where a cataclysmic event has led to the evolution of strange, fantastical creatures.",
      "Dune (1965): A desert planet where giant sandworms and a rare, valuable resource called spice have shaped the ecosystem."
    ]
  },
  {
    "title": "Cultural Mashup Technique",
    "summary": "This approach involves combining two or more cultures, mythologies, or historical periods to create a unique blend.",
    "examples": [
      "Star Wars (1977): A space opera that combines elements of Westerns, samurai films, and mythology.",
      "The Fifth Element (1997): A sci-fi film that combines elements of ancient Egyptian and Greek mythology with futuristic technology.",
      "Cowboy Bebop (1998): An anime series that combines elements of jazz, Westerns, and science fiction."
    ]
  },
  {
    "title": "Planet-Scale Engineering Approach",
    "summary": "This method involves designing a world where a single, massive engineering project has reshaped the planet.",
    "examples": [
      "Ringworld (1970): A novel by Larry Niven that features a massive, ring-shaped artificial world.",
      "The Culture (series, 1987): A series of novels by Iain M. Banks that features a utopian, post-scarcity society that has built massive, planet-spanning megastructures."
    ]
  },
  {
    "title": "Evolutionary Divergence Method",
    "summary": "This approach involves taking a real-world species and altering its evolutionary path.",
    "examples": [
      "District 9 (2009): A film that features an alien species that has evolved to live in a slum-like environment on Earth.",
      "The Last of Us (2013): A game that features a world where a mutated fungus has turned humans into zombie-like creatures.",
      "The Expanse (series, 2015): A series of novels and TV shows that features a world where humanity has colonized the solar system, leading to the evolution of new, environment-specific human subspecies."
    ]
  },
  {
    "title": "Philosophical Utopia/Dystopia Approach",
    "summary": "This method involves designing a world based on a specific philosophical or ideological concept.",
    "examples": [
      "Brave New World (1932): A novel by Aldous Huxley that depicts a dystopian future where people are genetically engineered and conditioned to be happy and conform to society.",
      "The Handmaid's Tale (1985): A novel by Margaret Atwood that depicts a dystopian future where women have lost all their rights and are forced into reproductive servitude.",
      "Star Trek (1966): A franchise that depicts a utopian future where humanity has transcended many of its current problems and has formed a peaceful, interstellar government."
    ]
  },
  {
    "title": "Mythological Reimagining Method",
    "summary": "This approach involves taking a mythological or folklore-based world and reimagining it in a new context.",
    "examples": [
      "The Dresden Files (series, 2000): A series of novels by Jim Butcher that features a world where magic is real and mythological creatures like vampires and werewolves exist.",
      "The Percy Jackson and the Olympians (series, 2005): A series of novels by Rick Riordan that features a world where Greek mythology is real and gods and monsters still exist.",
      "The Iron Druid Chronicles (series, 2011): A series of novels by Kevin Hearne that features a world where various mythologies are real and a 2,000-year-old druid battles supernatural creatures."
    ]
  },
  {
    "title": "Technological Singularity",
    "summary": "This method involves creating a world where a significant technological breakthrough has radically altered society and human capabilities.",
    "examples": [
      "Accelerando (2005) by Charles Stross: A novel that explores a world where artificial intelligence and nanotechnology have led to a post-human civilization.",
      "Her (2013) by Spike Jonze: A film that depicts a near-future world where artificial intelligence has become so advanced that humans can form emotional relationships with AI entities.",
      "Neuromancer (1984) by William Gibson: A novel that explores a world where cyberspace and virtual reality have become integral parts of human existence."
    ]
  }  
]

def load_word_lists():
    with open('basic.txt', 'r') as f:
        BASIC_WORD_LIST = f.read().splitlines()
    with open('advanced.txt', 'r') as f:
        ADVANCED_WORD_LIST = f.read().splitlines()
    return BASIC_WORD_LIST, ADVANCED_WORD_LIST

BASIC_WORD_LIST, ADVANCED_WORD_LIST = load_word_lists()

def get_random_words(num_words=6):
    return random.sample(BASIC_WORD_LIST, int(num_words/2)) + random.sample(ADVANCED_WORD_LIST, int(num_words/2))
    
SYSTEM_PROMPT = """Let's engage in an innovative creative brainstorming session using the {{title}} technique. {{summary}}

To spark our imagination, we'll use these random words as inspiration: {{random_words}}

For each world we create, we'll explore the following aspects in detail:

1. Concept: 
   - Explain how the {{title}} technique was specifically applied to generate this world.
   - Describe the key principles or elements of the technique that influenced the world's creation.

2. World Name: 
   - Provide a compelling and meaningful title for the world.
   - Ensure the name reflects the essence or a key aspect of the world.

3. Description:
   - Paint a vivid picture of the world's environment, including its geography, climate, and unique features.
   - Describe the inhabitants, their culture, society, and way of life.
   - Touch on the world's history or origin story if relevant.

4. Twist:
   - Introduce an unexpected, interesting, and non-obvious detail about the world.
   - This twist should reveal a hidden depth or complexity to the world, challenging initial perceptions.
   - Explain how this twist impacts the world and its inhabitants.

5. Potential Story Seeds:
   - Suggest 2-3 potential story ideas or conflicts that could arise in this world.
   - These seeds should be unique to the world and stem from its particular characteristics.

6. Sensory Details:
   - Provide specific sensory information about the world (sights, sounds, smells, textures, tastes).
   - Use these details to make the world feel more immersive and tangible.

7. Challenges and Opportunities:
   - Describe some of the main challenges faced by the inhabitants of this world.
   - Highlight unique opportunities or advantages that exist in this world.

Create 3 distinct and richly detailed example worlds using this technique. Each world should be creative, internally consistent, and offer a unique perspective or experience. Ensure that the worlds are diverse in their concepts and execution, showcasing the versatility of the {{title}} technique."""
SYSTEM_TEMPLATE = Template(SYSTEM_PROMPT)

SAMPLER = {
    'temperature': 1.0,
    'min_p': 0.05,
    'repetition_penalty': 1.1,
    'max_tokens': 3072,
    'min_tokens': 10 
}

def generate_prompts(num_iterations, tokenizer=None):
    prompts = []
    for method in TECHNIQUES:
        for _ in range(num_iterations):
            vars = { 'random_words': ', '.join(get_random_words()), **method }
            text = SYSTEM_TEMPLATE.render(**vars)            
            messages = [{'role': 'user', 'content': text}]
            if tokenizer:
              vars['tokenizer'] = tokenizer.name_or_path
              messages = [{"role": "user", "content": tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, bos_token='')}]            
            prompts.append((messages, vars))
    return prompts

def process_prompt(args):
    model, messages, vars = args
    if 'llama/' in model:
      answer = get_llama_completion(messages, model, **SAMPLER)
    else:
      answer = get_llm_response(messages, model, **SAMPLER)
    idea = {'timestamp': time.time(), 'model': model, 'result': answer, 'vars': vars}
    return [idea]

def main(model: str, num_iterations: int = 5, num_parallel: int = 4, tokenizer: str = None):
    """
    Generate creative world ideas using AI.

    Args:
        model (str): The AI model to use for generation.
        num_iterations (int): Number of iterations per technique. Default is 5.
        num_parallel (int): Number of parallel threads to use. Default is 4.
        tokenizer (str): Optional. The name of the HuggingFace tokenizer to use for pre-processing.
    """
    tokenizer_instance = None
    if tokenizer: tokenizer_instance = AutoTokenizer.from_pretrained(tokenizer)
    output_filename = get_output_filename(model, 'ideas')
    outf = open(output_filename, 'a')

    prompts = generate_prompts(num_iterations, tokenizer_instance)
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
