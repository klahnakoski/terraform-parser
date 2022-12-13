import json

from mo_dots import is_many

from mo_parsing import ParseResults


def first(values):
    if isinstance(values, ParseResults):
        return values[0]
    else:
        return values

def to_string(tokens):
    value = json.loads(f'"{tokens[0]}"')
    return {"literal": value}

def to_multiline(tokens):
    return dict(tokens)


def to_var(tokens):
    return tokens[0]

def to_code(tokens):
    return tokens


def multiline_content(tokens, _, string):
    content = string[tokens.start:tokens.end]
    return content

def if_else(tokens):
    when, _, then, _, els_ = list(tokens)
    return {"when": when, "then": then, "else": els_}


def to_name(tokens):
    return tokens[0]['literal']


def to_assign(tokens):
    return dict(zip([first(t) for t in tokens['name']], [first(t) for t in tokens['value']]))