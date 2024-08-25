import nltk
from nltk.corpus import words, brown

def load_dictionaries():
    nltk.download('brown', quiet=True)
    nltk.download('words', quiet=True)
    
    basic_words = words.words('en-basic')
    advanced_words = list(brown.words(categories=['adventure','fiction','humor','science_fiction','romance']))
    
    with open('basic.txt', 'w') as f:
        for word in basic_words:
            f.write(f"{word}\n")
    
    with open('advanced.txt', 'w') as f:
        for word in advanced_words:
            f.write(f"{word}\n")

if __name__ == "__main__":
    load_dictionaries()
    print("Word lists have been written to 'basic.txt' and 'advanced.txt'.")
