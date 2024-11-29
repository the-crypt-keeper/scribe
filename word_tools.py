import nltk
from nltk.corpus import words, brown

def create_dictionaries():
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
