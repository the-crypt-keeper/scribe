import sys
import random
from base import *

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

PROMPT_TEMPLATE = """Let's engage in an innovative creative brainstorming session using the {{title}} technique. {{summary}}

To spark our imagination, we'll use these random words as inspiration: {{random_words}}

IMPORTANT: DO NOT DIRECTLY MENTION THESE RANDOM WORDS IN YOUR OUTPUT.

We will create the world by exploring the following aspects in detail:

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

4. Sensory Details:
   - Provide specific sensory information about the world (sights, sounds, smells, textures, tastes).
   - Use these details to make the world feel more immersive and tangible.

5. Challenges and Opportunities:
   - Describe some of the main challenges faced by the inhabitants of this world.
   - Highlight unique opportunities or advantages that exist in this world.
      
6. Twist:
   - Introduce an unexpected, interesting, and non-obvious detail about the world.
   - This twist should reveal a hidden depth or complexity to the world, challenging initial perceptions.
   - Explain how this twist impacts the world and its inhabitants.

7. Potential Story Seeds:
   - Suggest 2-3 potential story ideas or conflicts that could arise in this world.
   - These seeds should be unique to the world and stem from its particular characteristics.

Create a distinct and richly detailed example world using this technique, showcasing the versatility of the {{title}} technique."""

class StepWorldGeneration(GenerateStep):    
    def run(self, id, input):
        from language_tools import get_random_words      
        method = random.choice(TECHNIQUES)
        random_words = get_random_words('basic', 3) + get_random_words('advanced', 3)
        return { 'random_words': ', '.join(random_words), **method }, {}

EXTRACTION_PROMPT = """The text provided by the user describes an world and is always organized into 7 sections: 

- Concept
- World Name
- Description
- Sensory Details
- Challenges and Opportunities
- Twist
- Story Seeds

FULLY AND COMPLETELY map the user input into a JSON object with the following schema:

{
    "concept": "<Concept including key principles or elements>",
    "world_name": "<The World Name>",
    "description": "<Description>",
    "sensory": "<Sensory Details>",
    "challenges_opportunities": "<Difficulties or opportunities faced by inhabitants of this world>",
    "twist": "<Twist>",
    "story_seeds": ["<A story idea that could arise in this world>","<another story idea...>"]
}

INSTRUCTIONS:
* All fields are required.
* Preserve sub-headings.
* Escape quotes, convert any newlines into \n and otherwise ensure the output JSON is valid.
* Make sure ALL text between relevant headings is captured.
"""

from pydantic import BaseModel, Field
from typing import List

class World(BaseModel):
    world_name: str = Field(description='The World Name')
    concept: str = Field(description='The way in which the concept was applied to create this world')
    description: str = Field(description = 'Description of the world')
    twist: str = Field(description = 'Unique Twist that makes this world interesting')
    story_seeds: List[str] = Field(description = 'Story ideas or conflicts that could arise in this world')
    sensory: str = Field(description='Specific sensory information about the world')
    challenges_opportunities: str = Field(description='Difficulties or opportunities faced by inhabitants of this world')

PIPELINE = [
  StepWorldGeneration(step='WorldGenScenario', outkey='vars'),
  StepExpandTemplate(step='WorldGenPrompt', inkey='vars', outkey='world_prompt', template=PROMPT_TEMPLATE),
  StepLLMCompletion(step='WorldGenComplete', inkey='world_prompt', outkey='idea'),
  StepLLMExtraction(step='WorldExtractPrompt', inkey='idea', outkey='world', prompt=EXTRACTION_PROMPT, schema_json=World.model_json_schema()),
  # WorldImagePrompt(step='WorldVisualizePrompt', input='world', output='img_prompt'),
  # Txt2ImgCompletion(step='WorldGenerateImage', input='img_prompt', output='image')
]
    
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="World Builder")
    parser.add_argument("--watch", action="store_true", help="Watch mode")
    parser.add_argument("--project", type=str, required=True, help="Project name")
    parser.add_argument("--step", action="append", nargs="+", help="Steps to run")

    args = parser.parse_args()

    step_dict = {x.step: x for x in PIPELINE}

    if args.step:
        for step_group in args.step:
            for step_arg in step_group:
                escaped_step_arg = step_arg.replace('//','%%')
                step_name, *parts = escaped_step_arg.split('/')
                parts = [p.replace('%%','/') for p in parts]
                
                if step_name not in step_dict:
                    raise Exception(f'Step {step_name} was not found, should be one of: {", ".join(step_dict.keys())}')
                
                print(f"CONFIG STEP: {step_name}")
                step_dict[step_name].enabled = True

                for arg in parts:
                    k, v = arg.split('=')
                    print(f"CONFIG ARG: {step_name}.{k} = {v}")
                    step_dict[step_name].params[k] = v
    
    # Init core
    scr = SQLiteScribe(args.project)
    for step in PIPELINE: scr.add_step(step)

    # Run all steps
    try:
      scr.run_all_steps()
    except Exception as e:
      scr.shutdown()
