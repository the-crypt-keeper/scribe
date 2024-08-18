import litellm
import json
import os

API_BASE_URL = "http://100.109.96.89:3333/v1"
API_KEY = os.getenv('OPENAI_API_KEY', "xx-ignored")

def decode_json(response):
    result = response[response.find('{'):response.rfind('}')+1]
    try:
        data = json.loads(result)
        events = data.get(list(data.keys())[0])
        return events
    except Exception as e:
        print(result)
        print(e)
        return []

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
            stream=False,
            **params
        )

        return [x.message.content for x in response.choices]
        
    except Exception as e:
        print(f"Error in LLM call: {e}")
        return []

def get_llm_response_stream(messages, model, n=1, max_tokens=3072, **params):
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
        
        yield [full_response]
        
    except Exception as e:
        print(f"Error in LLM call: {e}")
        yield []
