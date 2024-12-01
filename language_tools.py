import os
import random

def create_dictionaries():
    import nltk
    from nltk.corpus import words, brown
        
    nltk.download('brown', quiet=True)
    nltk.download('words', quiet=True)
    
    basic_words = words.words('en-basic')
    advanced_words = list(set(brown.words(categories=['adventure','fiction','humor','science_fiction','romance'])))
    
    with open('basic.txt', 'w') as f:
        for word in sorted(basic_words):
            f.write(f"{word}\n")
    
    with open('advanced.txt', 'w') as f:
        for word in sorted(advanced_words):
            if not (word[0].isdigit() or word[0].isalpha()): continue
            f.write(f"{word}\n")

word_lists = {}
if not os.path.isfile('basic.txt'): create_dictionaries()
  
with open('basic.txt', 'r') as f:
    word_lists['basic'] = f.read().splitlines()
            
with open('advanced.txt', 'r') as f:
    word_lists['advanced'] = f.read().splitlines()
            
def get_random_words(list_name, num_words):
    return random.sample(word_lists[list_name], num_words)