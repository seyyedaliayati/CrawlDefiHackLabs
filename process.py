import json
import requests

from bs4 import BeautifulSoup

file_path = "./data.json"
out_path = "./to_train.txt"

prompt = """
Create a new test case that demonstrates the following vulnerability in a smart contract:

Vulnerability Description:
{link}
{desc}
Contract Interface:
{interface}
"""

completion = """
PoC Test Case:
{testcase}
PoC Explanation:
{explain}
"""

template = """
{question}

{answer}
"""


with open(file_path, 'r') as fp:
    data = json.load(fp)

    for item in data:
        urls = ""
        interfaces = ""
        for link in item['reference_links']:
            url = link['link']
            if '/tx/' in url:
                continue
            urls += url + "\n"
        q = prompt.format(
            link=urls,
            interface=f"fetch from {id}",
            desc="",
        )
        for poc in item['data']:
            c = completion.format(
                testcase=poc['testcase'],
                explain=""
            )
            row = template.format(
                question=q,
                answer=c
            )
            with open(out_path, 'a') as f:
                f.write(row.strip())
                f.write("\n==========================\n")
