import random
import re
import json
import string
import os
import nltk

from hashlib import sha256
from solidity_parser import parser
import tiktoken


root_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(root_dir, 'DeFiHackLabs')
file_path = os.path.join(root_dir, 'README.md')
cache = dict()
encoding = tiktoken.encoding_for_model('gpt-4')
split = False

def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    num_tokens = len(encoding.encode(string))
    return num_tokens

def remove_code_blocks(content: str) -> str:
    pattern = re.compile(r'(```.*?\n(.*?)\n```)', re.DOTALL)
    content = re.sub(pattern, '', content)

    assert '```' not in content, content

    return content

def clean_text(content: str) -> str:
    pattern = re.compile(r'Testing')
    content = re.sub(pattern, '', content)

    pattern = re.compile(r'(\n+)')
    content = re.sub(pattern, '\n', content)

    assert 'Testing' not in content, content
    assert '\n\n' not in content, content

    return content.strip()

def clean_solidity(file_content: str) -> str:
    code = file_content
    # Remove non-ASCII characters
    code = ''.join(char for char in code if char in string.printable)

    # Remove large single-line comments
    code = re.sub(r'\/\/[^\n]{100,}', '', code)

    # Remove multi-line comments
    code = re.sub(r'\/\*(.*?)\*\/', '', code, flags=re.DOTALL)

    # Remove leading and trailing whitespaces
    code = code.strip()

    # Remove empty lines
    code = re.sub(r'\n\s+\n', '\n\n', code)

    # Remove empty lines 2
    code = re.sub(r'\n\s*\n', '\n', code)

    # Remove excess consecutive whitespaces
    # code = re.sub(r'\s{2,}', ' ', code)

    # Remove unnecessary spaces before and after parentheses
    code = re.sub(r'\(\s*', '(', code)
    code = re.sub(r'\s*\)', ')', code)

    return code

def extract_code_snippet(file_path, loc):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Subtract 1 from start and end line because list indexing starts from 0
    start_line = loc['start']['line'] - 1
    # we don't subtract 1 here because list slicing is exclusive at the end
    end_line = loc['end']['line']
    snippet = lines[start_line:end_line]
    snippet = ''.join(snippet)
    return snippet, num_tokens_from_string(snippet)

def get_imports(node):
    imports = []
    if node['type'] == 'ImportDirective':
        imports.append(node['path'])
    return imports

def get_interface(node, file_path: str):
    if node['type'] == 'ContractDefinition' and node['kind'] == 'interface':
        code_snippet, token_count = extract_code_snippet(file_path, node['loc'])
        return {'name': node['name'], 'content': code_snippet, 'token_count': token_count}

# Define a function to traverse the tree and print the names of used user-defined types and function calls
def get_variable_types(node):
    types = []
    # If the node is a contract
    if node['type'] == 'ContractDefinition' and node['kind'] == 'contract' and node['subNodes']:
        for sub_node in node['subNodes']:
            if sub_node['type'] == 'StateVariableDeclaration':
                for var_dec in sub_node['variables']:
                    # If the variable type is a user-defined type
                    if var_dec['typeName']['type'] == 'UserDefinedTypeName':
                        types.append(var_dec['typeName']['namePath'])
    return types

def get_variables(node, file_path: str):
    # If the node is a contract
    if node['type'] == 'ContractDefinition' and node['kind'] == 'contract' and node['subNodes']:
        for sub_node in node['subNodes']:
            if sub_node['type'] == 'StateVariableDeclaration':
                for var_dec in sub_node['variables']:
                    # If the variable type is a user-defined type
                    if var_dec['typeName']['type'] == 'UserDefinedTypeName':
                        var_type = var_dec['typeName']['namePath']
                        var_name = var_dec['name']
                        if var_dec['expression']:
                            if var_dec['expression']['expression']:
                                print(extract_code_snippet(file_path, var_dec['expression']['expression']['loc']))
                    if var_dec['typeName']['type'] == 'ElementaryTypeName':
                        if var_dec['typeName']['name'] == 'address':
                            var_name = var_dec['name']
                            addr = var_dec['expression']['number']
                            yield 'address', var_name, addr

def extract_interfaces(file_path: str, get_types=True) -> list:
    if file_path.startswith("src/test/"):
        file_path = os.path.join(root_dir, file_path)

    if file_path in cache:
        ast = cache[file_path]
    else:
        ast = parser.parse_file(file_path, loc=True)
        cache[file_path] = ast
    all_interfaces = []
    imports = []
    types = []

    # 1. Get all user-defined types
    if get_types:
        for node in ast['children']:
            types += get_variable_types(node)

    # 2. Get inner interfaces + imports
    for node in ast['children']:
        imports += get_imports(node)
        interface = get_interface(node, file_path)
        if interface:
            interface['imported'] = not get_types
            all_interfaces.append(interface)
    # 3. Get imported interfaces
    for import_path in imports:
        p2 = os.path.join(os.path.dirname(file_path), import_path)
        if os.path.exists(p2):
            all_interfaces += extract_interfaces(p2, get_types=False)

    if types:
        types = list(set(types))
        for interface in all_interfaces.copy():
            if interface['name'] not in types:
                all_interfaces.remove(interface)

    return all_interfaces

def extract_vulnerable_contract_info(file_path: str, title: str, interface_names: list) -> str:
    if file_path.startswith("src/test"):
        file_path = os.path.join(root_dir, file_path)
    if file_path in cache:
        ast = cache[file_path]
    else:
        ast = parser.parse_file(file_path, loc=True)
        cache[file_path] = ast
    variables_with_values = {}
    for node in ast['children']:
        res = get_variables(node, file_path)
        # for i in res:
        #     print(i)
        # print()
    # print(variables_with_values)
    return variables_with_values

def fetch_data(content: str) -> str:
    pattern = re.compile(r'^### (\d{8})\s*(.*)', re.MULTILINE)
    dates = re.findall(pattern, content)
    if len(dates) == 0:
        print(content)
        exit()
    date, title = dates[0]
    parts = title.split(' - ')
    if len(parts) == 1:
        tokens = parts[0]
        attack = None
    elif len(parts) >= 2:
        attack = parts[-1]
        tokens = " - ".join(parts[:-1])
    else:
        print(content)
        print(parts)
        raise Exception('Invalid title')
    if tokens.startswith("- "):
        tokens = tokens[2:]

    # lost
    pattern = re.compile(r'^#.* Lost: (.*)', re.MULTILINE)
    losts = re.findall(pattern, content)
    lost = None
    if len(losts) == 0:
        assert 'Lost:' not in content, content
    elif len(losts) > 1:
        lost = losts[0]

    # contract path
    pattern = re.compile(r'^\[.*?\]\((.*?)\)', re.MULTILINE)
    pathes = re.findall(pattern, content)
    assert len(pathes) > 0, content

    # reference links
    pattern = re.compile(r'(^https:\/\/.*\s*$)', re.MULTILINE)
    links = re.findall(pattern, content)

    # extract data
    data = []
    for i, p in enumerate(pathes):
        data_item = {}

        if p.startswith('/'):
            p = p[1:]
        # if not p.endswith('ARA_exp.sol'):
        #     continue
        data_item['contract_path'] = p

        f = open(os.path.join(root_dir, p), 'r', encoding='utf-8')

        testcase = f.read()  # Test case are in Solidity

        interfaces = []
        interfaces = extract_interfaces(file_path=p)
        interface_names = [i['name'] for i in interfaces]
        extract_vulnerable_contract_info(file_path=p, title=tokens.strip(), interface_names=interface_names)
        testcase = clean_solidity(testcase)
        data_item['testcase'] = testcase
        token_count = num_tokens_from_string(testcase)
        data_item['token_count'] = token_count
        data_item['interfaces'] = interfaces

        data.append(data_item)

    assert len(data) == len(pathes) >= 0, pathes

    info = {
        'id': sha256(content.encode()).hexdigest()[:10],
        'content': content.strip(),
        'date': date.strip(),
        'target': tokens.strip(),
        'attack_title': attack.strip().title() if attack else None,
        'attack_strategy': None,
        'address': None,
        'vuln_desc': None,
        'target_function': None,
        'lost_value': lost.strip() if lost else None,
        'github_path': "https://github.com/SunWeb3Sec/DeFiHackLabs/",
        'reference_links': [{'link': link.strip(), 'content': None} for link in links if '/tx/' not in link],  # Skipping transaction links
        'data': data,
    }
    return info

if __name__ == '__main__':
    with open(file_path, 'r') as f:
        file_content = f.read()
        hacks = file_content.split('---')
        print(f"No. of hacks: {len(hacks)}")
        data = []
        for hack in hacks:
            hack = remove_code_blocks(hack)
            hack = clean_text(hack)
            data.append(fetch_data(hack))
        assert len(data) == len(hacks), "len(data) != len(hacks)"

    # Shuffle the data
    random.shuffle(data)
    
    with open('./data.json', 'w') as f:
        json.dump(data, f, indent=4)
    
    if split:
        # Split the data into training and evaluation datasets
        split_index = int(0.9 * len(data))
        train_data = data[:split_index]
        print(len(train_data))
        eval_data = data[split_index:]
        print(len(eval_data))

        with open('./train_data.json', 'w') as f:
            json.dump(train_data, f, indent=4)
        with open('./eval_data.json', 'w') as f:
            json.dump(eval_data, f, indent=4)
