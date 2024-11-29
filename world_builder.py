import json
import fire
import random
from base import Scribe

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

Create a distinct and richly detailed example world using this technique, showcasing the versatility of the {{title}} technique."""

SAMPLER = {
    'temperature': 1.0,
    'min_p': 0.05,
    'repetition_penalty': 1.1,
    'max_tokens': 3072,
    'min_tokens': 10 
}

class WorldBuilder(Scribe):
    def generate_vars(self):        
        method = random.choice(TECHNIQUES)
        random_words = self.get_random_words('basic', 3) + self.get_random_words('advanced', 3)
        vars = { 'random_words': ', '.join(random_words), **method }
        return vars
      
    def prompt_template(self):
        return PROMPT_TEMPLATE

def main(model: str, num_samples: int = 50, num_parallel: int = 1, num_batch: int = 1, tokenizer: str = None):
    wb = WorldBuilder(model)
    if tokenizer: wb.completion_mode(tokenizer)    
    with open(wb.make_output_filename('ideas'), 'a') as outf:  
      for idea in wb.parallel_generator(num_parallel, num_samples, SAMPLER, num_batch):
        outf.write(json.dumps(idea)+'\n')
        outf.flush()

if __name__ == "__main__":
    fire.Fire(main)
