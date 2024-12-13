import random
from language_tools import get_random_words
from base import SQLiteScribe
from steps import *

IDEAS_TEMPLATE = """You are tasked with brainstorming a list of programming challenge tasks suitable for senior-level developers. These challenges should be complex, requiring advanced knowledge and skills in various areas of computer science and software engineering.

Guidelines for generating challenge ideas:
- Focus on tasks that require deep understanding of algorithms, data structures, and system design
- Include challenges that test problem-solving skills, optimization abilities, and architectural thinking
- Vary the difficulty level, but ensure all challenges are appropriate for senior developers
- Cover a wide range of topics in computer science and software engineering

Your output should be a numbered list of exactly 3 challenge tasks. Each task should have:
1. A concise title
2. A brief description (1-2 sentences)
3. Key concepts or skills tested

Examples of challenge categories and specific tasks:
1. Advanced Algorithms: Implement a parallel merge sort algorithm
2. Distributed Systems: Design a distributed cache with consistency guarantees
3. Language Design: Create a basic interpreter for a custom programming language
4. Machine Learning: Implement a neural network from scratch without using ML libraries
5. Operating Systems: Write a simple scheduler for a multi-threaded operating system

First, use a <scratchpad></scratchpad> field to free-form brainstorm ideas before designing the challenges, using the following random words as entropy: {{random_words}}. Consider various areas of computer science and software engineering that would challenge a senior developer. Explore a diverse range of concepts.

Then, provide your final response in JSON format:

```json
{
    "challenge_0": {            
            "title": "<first challenge title>",
            "description": "<first challenge description>",
            "concepts": "<concepts covered by the first challenge>",
    },
    "challenge_1": {
            "title": "<second challenge title>",
            "description": "<first challenge description>",
            "concepts": "<concepts covered by the second challenge>",
    },
    "challenge_2": {
            "title": "<third challenge title>",
            "description": "<third challenge description>",
            "concepts": "<concepts covered by the third challenge>",
    }
}
```"""

class StepIdeaGeneration(GenerateStep):    
    def run(self, id, input):
        random_words = get_random_words('basic', 3) + get_random_words('advanced', 7)
        return { 'random_words': ', '.join(random_words), 'NUM_CHALLENGES': 5 }, {}

GENERATE_TASK = """You will be given a JSON object containing information about three programming challenges.

Your task is to think step-by-step to analyze these challenges, select the most appropriate one to be represented as a single function, design that function, and create test cases for it. Follow these steps:

1. Consider the following brainstorm ideas for programming challenges:

{{challenge_0}}

{{challenge_1}}

{{challenge_2}}

2. Analyze the three challenges and select the one that is most appropriate to be represented as a single function that takes only simple data types (int, str, float, list, dict) as inputs and outputs. Consider the complexity of the challenge (prefer higher complexity) and how well it can be encapsulated in a single function.

3. For the selected challenge, design (but do not implement) the function that best represents its core concepts while adhereing to the restrictions above. Describe the function's operations, inputs, and outputs in detail. Ensure that the function only uses simple data types for its inputs and outputs.

4. Generate 7-10 test cases for this function. Include both typical use cases and potential error conditions. Each test case should specify the input(s) and the expected output or behavior.

5. Present your final result in a YAML block, formatted as follows:

```yaml
ChallengeName:
    Signature: "function_name(param1, param2, ...)"
    Input: "Description of input parameters"
    Output: "Description of the function's output"
    Description: "A DETAILED description of the function's purpose and expected methods of operation"
    Checks:
        test_case_1:
            assert: function_call(args)
            eq: expected_output
        test_case_2:
            assert: function_call(args)
            eq: expected_output
        # ... (include all 7-10 test cases)
```

Ensure that your YAML block includes all necessary information about the function and all 7-10 test cases. Use appropriate indentation and formatting for the YAML structure.

Remember to think step-by-step, starting from step 1!"""

PIPELINE = [
  StepIdeaGeneration(step='Scenario', outkey='vars'),
  StepExpandTemplate(step='IdeaPrompt', inkey='vars', outkey='idea_prompt', template=IDEAS_TEMPLATE),
  StepLLMCompletion(step='GenIdea', inkey='idea_prompt', outkey='idea'),
  StepJSONParser(step='Parse', inkey='idea', outkey='challenges'),
  StepExpandTemplate(step='TaskPrompt', inkey='challenges', outkey='task_prompt', template=GENERATE_TASK),
  StepLLMCompletion(step='GenTask', inkey='task_prompt', outkey='task'),
  StepJSONExport(step='Export', inkey='task')
]

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="World Builder")
    parser.add_argument("--watch", action="store_true", help="Watch mode")
    parser.add_argument("--project", type=str, required=True, help="Project name")
    parser.add_argument("--step", action="append", nargs="+", help="Steps to run")
    args = parser.parse_args()

    if not args.step: raise Exception("At least one --step is required.")

    try:
      scr = SQLiteScribe(args.project)
      scr.init_pipeline(args.step, PIPELINE)       
      scr.run_all_steps()
    finally:
      scr.shutdown()
