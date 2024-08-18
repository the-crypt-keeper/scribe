import litellm
import json
import os
import re

API_BASE_URL = "http://100.109.96.89:3333/v1"
API_KEY = os.getenv('OPENAI_API_KEY', "xx-ignored")

def get_output_filename(model, prefix):
    # Extract the model name after the last '/'
    model_name = model.split('/')[-1]
    # Replace any non-alphanumeric characters with underscores
    safe_model_name = re.sub(r'[^a-zA-Z0-9]', '_', model_name)
    return f"{prefix}_{safe_model_name}.json"

def decode_json(response, first_key = True):
    result = response[response.find('{'):response.rfind('}')+1]
    try:
        data = json.loads(result)
        if first_key: data = data.get(list(data.keys())[0])
        return first_key
    except Exception as e:
        print(result)
        print(e)
        return None

def get_llm_response(messages, model, n=1, max_tokens=3072, **params):
    try:
        response = litellm.completion(
            model=model,
            n=n,
            messages=messages,
            api_base=API_BASE_URL,
            api_key=API_KEY,
            max_tokens=max_tokens,
            min_tokens=8,
            **params
        )

        return [x.message.content for x in response.choices]
        
    except Exception as e:
        print(f"Error in LLM call: {e}")
        return []

def get_llm_response_stream(messages, model, max_tokens=3072, **params):
    try:
        response = litellm.completion(
            model=model,
            messages=messages,
            api_base=API_BASE_URL,
            api_key=API_KEY,
            max_tokens=max_tokens,
            min_tokens=8,
            stream=True,
            **params
        )

        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                print(content, end='', flush=True)
        
        print()  # New line after streaming is complete
        
        yield full_response
        
    except Exception as e:
        print(f"Error in LLM call: {e}")
        yield None
