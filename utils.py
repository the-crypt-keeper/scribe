import litellm
import json
import os

API_BASE_URL = "http://100.109.96.89:3333/v1"
API_KEY = os.getenv('OPENAI_API_KEY', "xx-ignored")

def get_llm_response(messages, model, n=1, max_tokens=3072, decode_json=False, **params):
    try:
        response = litellm.completion(
            model=model,
            n=n,
            messages=messages,
            api_base=API_BASE_URL,
            api_key=API_KEY,
            max_tokens=max_tokens,
            min_tokens=8,
            stream=False,
            **params
        )

        full_response = [x.message.content for x in response.choices]
        
        if decode_json:
            full_response = full_response[0]
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
        
        return events
        
    except Exception as e:
        print(f"Error in LLM call: {e}")
        return []

def get_llm_response_stream(messages, model, n=1, max_tokens=3072, decode_json=False, **params):
    try:
        response = litellm.completion(
            model=model,
            n=n,
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
            events = [full_response]
        
        yield events
        
    except Exception as e:
        print(f"Error in LLM call: {e}")
        yield []
