import os
import re
import sys
import json
import toml
import yaml
import itertools
from typing import List, Set, Dict, Any, Iterator


def get_lines(fpath: str) -> List[str]:
    if not os.path.isfile(fpath):
        print(f"Error: The file '{fpath}' was not found.")
        return []
    try:
        with open(fpath, 'r') as file:
            return [line.strip() for line in file.readlines()]
    except IOError:
        print(f"Error: An error occurred while reading the file '{fpath}'.")
    return []

def get_basedir() -> str:
    return os.path.split(os.path.abspath(sys.modules['permitcheck'].__file__))[0]

def check_subclass(subclass: type, cls: type) -> bool:
    return False if subclass is cls else issubclass(subclass, cls)

def get_pwd() -> str:
    return os.getcwd()

def flatten_set(data: Dict[str, List[str]]) -> Set[str]:
    return set(itertools.chain(*data.values()))

def get_matching_keys(substring: str, keys: List[str]) -> List[str]:
    return [key for key in keys if re.search(substring, key)]

def read_json(fpath: str) -> Dict[str, Any]:
    if not os.path.isfile(fpath):
        return {}
    with open(fpath, 'r') as f:
        return json.load(f)

def write_json(fpath: str, data: Dict[str, Any]) -> None:
    with open(fpath, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=True)

def read_toml(fpath: str) -> Dict[str, Any]:
    if not os.path.isfile(fpath):
        return {}
    with open(fpath, 'r') as f:
        return toml.load(f)
    
def read_yaml(fpath: str) -> Dict[str, Any]:
    if not os.path.isfile(fpath):
        return {}
    with open(fpath, 'r') as f:
        return yaml.safe_load(f)

def exit(code: int = 0) -> None:
    sys.exit(code)
