import requests
import re
import mwparserfromhell
import litellm
import json

SYSTEM_PROMPT = """The user will provide a timeline of historic events. Convert it to a JSON list where each entry has the following schema:

{
  'year_range': [start_year, end_year],
  'title': <event title>,
  'summary': <brief summary of event>,
  'significance': LOCAL | REGIONAL | GLOBAL,
  'historic_importance': MINOR | MAJOR | CRITICAL
}"""

API_BASE_URL = "http://100.109.96.89:3333/"
MODEL = "hermes-3-llama-3.1-405b-fp8"

def get_llm_response(text):
    try:
        response = litellm.completion(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            api_base=API_BASE_URL
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error in LLM call: {e}")
        return []

def get_mediawiki_content(url):
    # Convert URL to API URL
    api_url = url.replace('/wiki/', '/w/index.php?title=') + '&action=raw'
    response = requests.get(api_url)
    return response.text

def split_into_sections(content):
    section_pattern = r'^(={2,6})\s*(.+?)\s*\1'
    sections = []
    lines = content.split('\n')
    current_section = {'title': 'Introduction', 'text': '', 'start_line': 0, 'end_line': 0}
    
    for i, line in enumerate(lines):
        match = re.match(section_pattern, line)
        if match:
            # End the previous section
            current_section['end_line'] = i - 1
            sections.append(current_section)
            
            # Start a new section
            current_section = {
                'title': match.group(2),
                'text': '',
                'start_line': i,
                'end_line': 0
            }
        else:
            current_section['text'] += line + '\n'
    
    # Add the last section
    current_section['end_line'] = len(lines) - 1
    sections.append(current_section)
    
    for section in sections:
        section['plain'] = mwparserfromhell.parse(section['text']).strip_code()
    
    return sections

def filter_sections_with_years(sections):
    year_pattern = r'\b\d{4}'
    return [section for section in sections if re.search(year_pattern, section['title'])]

# List of Wikipedia URLs
wikipedia_urls = [
    "https://en.wikipedia.org/wiki/15th_century",
    "https://en.wikipedia.org/wiki/16th_century",
    "https://en.wikipedia.org/wiki/Timeline_of_the_17th_century"
]

for url in wikipedia_urls:
    print(f"Processing: {url}")
    
    # Download MediaWiki content
    mediawiki_content = get_mediawiki_content(url)
    sections = split_into_sections(mediawiki_content)
    sections_with_years = filter_sections_with_years(sections)
    
    print(f"Found {len(sections_with_years)} sections containing years:")
    for i, section in enumerate(sections_with_years, 1):
        print(f"\nSection {i}:")
        print(section['plain'][:200] + "..." if len(section['plain']) > 200 else section['plain'])
        
        # Make LiteLLM completions call
        section['timeline'] = get_llm_response(section['plain'])
        print(f"Timeline entries: {len(section['timeline'])}")
    
    print("\n" + "="*50 + "\n")
