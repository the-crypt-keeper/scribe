from transformers import AutoTokenizer

class InternalTokenizer:    
    def __init__(self, name, fn):
        self.fn = fn
        self.name_or_path = name
        
    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, bos_token=''):
        system = [x['content'] for x in messages if x['role'] == 'system']
        user = [x['content'] for x in messages if x['role'] == 'user']
        assistant = [x['content'] for x in messages if x['role'] == 'assistant']
        
        system = "You are a helpful assistant." if len(system) == 0 else system[0]
        user = user[0]
        assistant = "" if len(assistant) == 0 else assistant[0]
        
        return self.fn(system, user, assistant)

tokenizer_internal = {
    'internal:vicuna': InternalTokenizer('vicuna', lambda system, user, assistant:
f"""SYSTEM: {system}

USER: {user}

ASSISTANT:{assistant}"""),

    'internal:alpaca': InternalTokenizer('alpaca', lambda system, user, assistant:
f"""### Instruction:
{system}

### Input:
{user}

### Response:{assistant}""")
}

def build_tokenizer(tokenizer_name):
    if tokenizer_name is None:
        return None
    elif tokenizer_name in tokenizer_internal:
        return tokenizer_internal[tokenizer_name]
    else: 
        return AutoTokenizer.from_pretrained(tokenizer_name, trust_remote_code=True)