import os
import yaml
import json


def safe_mkdir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def load_json(fn):
    with open(fn) as fh:
        return json.load(fh)


def write_json(content, fn):
    with open(fn, 'w') as fh:
        return json.dump(content, fh, indent=2, sort_keys=True)


def load_yaml(fn):
    with open(fn) as fh:
        return yaml.safe_load(fh)



