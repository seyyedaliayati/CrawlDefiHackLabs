import os
import json
import openai

import time

from extract import num_tokens_from_string

file_path = "./dataset_gpt3.json"
openai.api_key = os.getenv("OPENAI_API_KEY") or "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"

prompt_template = """
The following is a Solidity test case written in Foundry that exposes an attack titled "{attack_title}".
In one paragraph explain how it exposes this specific vulnerability?
{testcase}
"""

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
    for item in data:
        if item['attack_explain'] is not None:
            continue
        prompt = prompt_template.format(
            attack_title=item['attack_title'],
            testcase=item['testcase']
        )
        num_tokens = num_tokens_from_string(prompt)
        if num_tokens > 4096:
            print("Too long prompt, skip")
            continue
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt},
            ]
        )
        res = completion.choices[0].message['content']
        print(f"response generated: {len(res)}")
        item['attack_explain'] = res
        time.sleep(5)
        with open('dataset_gpt4.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        


# print(completion.choices[0].message)
