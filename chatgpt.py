import os
import json
import openai
import re
import time
import json

from crawl import num_tokens_from_string
from openai.error import InvalidRequestError, RateLimitError

file_path = "./data_gpt5.json"
output_path = "./data_gpt6.json"
assert file_path != output_path
wait_time = 10
model = 'gpt-4-0613'
openai.api_key = os.getenv("OPENAI_API_KEY") or "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"

prompt_template = """
You are an expert in security testcases written in Solidity with Foundry framework. Consider the following PoC testcase:
Target: {target}
Attack Title: {attack_title}
PoC Testcase written in Foundry:
```
{testcase}
```

Your task is to extract the address of the vulnerable smart contract, category of the attack strategy, a description of the exposed vulnerability, and the target/vulnerable function in a JSON format with the following keys:
address, attack_strategy, vuln_desc, target_function

If you are not sure, fill the values with null.
I do not need any extra text, the output must be only the specified json and nothing more.
"""


def find_between_backticks(text):
    pattern = r"```(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches

def get_completion(prompt) -> str:
    completion = openai.ChatCompletion.create(
        model=model,
        temperature=0.4,
        messages=[
            {"role": "user", "content": prompt},
        ]
    )
    return completion.choices[0].message['content']

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
    for i, item in enumerate(data):
        if item['attack_strategy'] is not None:
            continue
        print(f"Processing {i} of {len(data)}...")
        target = item['target']
        attack_title = item['attack_title']
        for d in item['data']:
            testcase = d['testcase']
            prompt = prompt_template.format(target=target, attack_title=attack_title, testcase=testcase)
            try:
                completion = get_completion(prompt)
            except InvalidRequestError as e:
                print("\nError: ", e)
                print()
                time.sleep(10)
                continue
            except RateLimitError as e:
                print("\nError: ", e)
                print()
                time.sleep(10)
                continue
            try:
                completion = json.loads(completion)
            except:
                codes = find_between_backticks(completion)
                if len(codes) != 1:
                    print("Error: more than one or zero code block found")
                    print(completion)
                    print(codes)
                    exit(1)
                completion = codes[0]
                completion = json.loads(completion)
            print(completion)
            
            item.update(completion)

            with open(output_path, 'w') as f:
                json.dump(data, f, indent=4)
            time.sleep(10)
            print("====================================")
