import time
from utils import get_llm_response, get_output_filename
import re
import random
import sys
import json
from jinja2 import Template
import nltk
from nltk.corpus import words, brown
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

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
  }
]

BASIC_WORD_LIST = []
ADVANCED_WORD_LIST = []
def load_dictionaries():
    global BASIC_WORD_LIST
    global ADVANCED_WORD_LIST
    
    nltk.download('brown', quiet=True)
    nltk.download('words', quiet=True)
    
    BASIC_WORD_LIST = words.words('en-basic')
    ADVANCED_WORD_LIST = list(brown.words(categories=['adventure','fiction','humor','science_fiction','romance']))
    
def get_random_words(num_words=6):
    return random.sample(BASIC_WORD_LIST, int(num_words/2)) + random.sample(ADVANCED_WORD_LIST, int(num_words/2))
    
SYSTEM_PROMPT = """Let's do some creative brainstorming with the {{title}} technique. {{summary}}
Use these random words for inspiration: {{random_words}}

Consider the following details for each world:

- Concept: Explain how the technique was applied to produce this World.
- World Name: Give the World a meaningful title.
- Description: Describe the world and its inhabitants.
- Twist: An unexpected detail revealing a hidden depth to this world.

Create 3 example worlds using this technique."""
SYSTEM_TEMPLATE = Template(SYSTEM_PROMPT)

MODEL = sys.argv[1]
NUM_ITERATIONS = 5
NUM_PARALLEL = 4  # Default number of parallel threads
SAMPLER = {
    'temperature': 1.0,
    'min_p': 0.05,
    'repetition_penalty': 1.1,
    'max_tokens': 3072,
    'min_tokens': 10 
}

def generate_prompts():
    prompts = []
    for method in TECHNIQUES:
        for _ in range(NUM_ITERATIONS):
            random_words = get_random_words()
            messages = [{'role': 'user', 'content': SYSTEM_TEMPLATE.render(random_words=', '.join(random_words), **method)}]
            prompts.append((method, random_words, messages))
    return prompts

def process_prompt(args):
    method, random_words, messages = args
    answer = get_llm_response(messages, MODEL, **SAMPLER)
    idea = {'timestamp': time.time(), 'idea': answer, 'method': method['title'], 'model': MODEL, 'random_words': random_words}
    return [idea]

def main():
    output_filename = get_output_filename(MODEL, 'ideas')
    outf = open(output_filename, 'a')

    prompts = generate_prompts()
    total_prompts = len(prompts)

    with ThreadPoolExecutor(max_workers=NUM_PARALLEL) as executor:
        futures = [executor.submit(process_prompt, prompt) for prompt in prompts]
        
        with tqdm(total=total_prompts, desc="Processing prompts", unit="prompt") as pbar:
            for future in as_completed(futures):
                ideas = future.result()
                for idea in ideas:
                    outf.write(json.dumps(idea) + '\n')
                pbar.update(1)

    outf.close()

load_dictionaries()
main()
