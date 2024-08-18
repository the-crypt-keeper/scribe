import time
import litellm
import json
import os
import re
from urllib.parse import urlparse
from jinja2 import Template

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

SYSTEM_PROMPT = """Let's do some creative brainstorming with the {{title}} technique. {{summary}}
Return a markdown list of 3 example worlds created with this technique.
Provide the following details for each world:

- Concept: Explain how the technique was applied to produce this idea
- World Name: What is this world called
- Description: Describe the world and it's inhabitants.
- Twist: A deeper, hidden meaning or creative twist underlying this world.
"""
SYSTEM_TEMPLATE = Template(SYSTEM_PROMPT)

API_BASE_URL = "http://100.109.96.89:3333/v1"
API_KEY = os.getenv('OPENAI_API_KEY', "xx-ignored")
MODEL = "openai/Hermes-2-Theta-Llama-3-70B"
RESPONSE_FORMAT = None #{"type": "json_object"}

def get_output_filename(model):
    # Extract the model name after the last '/'
    model_name = model.split('/')[-1]
    # Replace any non-alphanumeric characters with underscores
    safe_model_name = re.sub(r'[^a-zA-Z0-9]', '_', model_name)
    return f"ideas_{safe_model_name}.json"

def get_llm_response(messages, n = 1, stream = True, decode_json = False):
    try:
        response = litellm.completion(
            model=MODEL,
            n=n,
            messages=messages,
            api_base=API_BASE_URL,
            api_key=API_KEY,
            max_tokens=4095,
            response_format=RESPONSE_FORMAT,
            stream=stream
        )

        full_response = ""
        if stream:
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    print(content, end='', flush=True)
        else:
            full_response = [x.message.content for x in response.choices]
            
        if decode_json:
            result = full_response[full_response.find('{'):full_response.rfind('}')+1]
            events = []
            try:
                data = json.loads(result)
                events = data.get(list(data.keys())[0])
            except Exception as e:
                print(result)
                print(e)
        else:
            events = full_response
            
        print()  # New line after streaming is complete
        yield events
        
    except Exception as e:
        print(f"Error in LLM call: {e}")
        yield []

for method in TECHNIQUES:
    messages = [{'role': 'user', 'content': SYSTEM_TEMPLATE.render(**method)}]
    print('>>>',method['title'])
    ideas = []
    output_filename = get_output_filename(MODEL)
    outf = open(output_filename, 'a')
    for completion in get_llm_response(messages, n=5, stream=False):
        for answer in completion:
            idea = {'timestamp': time.time(), 'idea': answer, 'method': method['title'], 'model': MODEL}
            ideas.append(idea)
            outf.write(json.dumps(idea)+'\n')
    print('--')
