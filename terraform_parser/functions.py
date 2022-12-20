# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

import json

from mo_imports import expect

from mo_parsing import ParseResults, Forward, Group, is_number
from terraform_parser.keywords import binary_ops
from terraform_parser.utils import SQL_NULL, Call

multiline_string_parser = expect("multiline_string_parser")


def first(values):
    if isinstance(values, ParseResults):
        return values[0]
    else:
        return values


def to_string(tokens):
    value = json.loads(f'"{tokens[0]}"')
    return {"literal": value}


def to_multiline_string(tokens):
    return {"literal": tokens[0]}


def to_multiline(tokens):
    return {"concat": multiline_string_parser.parse(tokens['content'])}


def to_var(tokens):
    return tokens[0]


def to_code(tokens):
    return tokens


def multiline_content(tokens, _, string):
    content = string[tokens.start : tokens.end]
    return content


def if_else(tokens):
    when, _, then, _, els_ = list(tokens)
    return {"when": when, "then": then, "else": els_}


def to_name(tokens):
    return tokens[0]["literal"]


def to_assign(tokens):
    return dict(zip(
        [first(t) for t in tokens["name"]], [first(t) for t in tokens["value"]]
    ))


def to_json_operator(tokens):
    # ARRANGE INTO {op: params} FORMAT
    length = len(tokens.tokens)
    if length == 2:
        if tokens.tokens[1].type.parser_name == "cast":
            return Call("cast", list(tokens), {})
        # UNARY OPERATOR
        op = tokens.tokens[0].type.parser_name
        if is_number(tokens[1]):
            if op == "neg":
                return -tokens[1]
            elif op == "pos":
                return tokens[1]
        return Call(op, [tokens[1]], {})
    elif length == 5:
        # TRINARY OPERATOR
        return Call(
            tokens.tokens[1].type.parser_name, [tokens[0], tokens[2], tokens[4]], {}
        )

    op = tokens[1]
    if not isinstance(op, str):
        op = op.type.parser_name
    op = binary_ops.get(op, op)
    if op == "eq":
        if tokens[2] is SQL_NULL:
            return Call("missing", tokens[0], {})
        elif tokens[0] is SQL_NULL:
            return Call("missing", tokens[2], {})
    elif op == "neq":
        if tokens[2] is SQL_NULL:
            return Call("exists", tokens[0], {})
        elif tokens[0] is SQL_NULL:
            return Call("exists", tokens[2], {})
    elif op == "eq!":
        if tokens[2] is SQL_NULL:
            return Call("missing", tokens[0], {})
        elif tokens[0] is SQL_NULL:
            return Call("missing", tokens[2], {})
    elif op == "ne!":
        if tokens[2] is SQL_NULL:
            return Call("exists", tokens[0], {})
        elif tokens[0] is SQL_NULL:
            return Call("exists", tokens[2], {})
    elif op == "is":
        if tokens[2] is SQL_NULL:
            return Call("missing", tokens[0], {})
        else:
            return Call("exists", tokens[0], {})
    elif op == "is_not":
        if tokens[2] is SQL_NULL:
            return Call("exists", tokens[0], {})
        else:
            return Call("missing", tokens[0], {})

    operands = [tokens[0], tokens[2]]
    binary_op = Call(op, operands, {})

    if op in {"add", "mul", "and", "or", "concat", "binary_and", "binary_or"}:
        # ASSOCIATIVE OPERATORS
        acc = []
        for operand in operands:
            while isinstance(operand, ParseResults) and isinstance(operand.type, Group):
                # PARENTHESES CAUSE EXTRA GROUP LAYERS
                operand = operand[0]
                if isinstance(operand, ParseResults) and isinstance(
                    operand.type, Forward
                ):
                    operand = operand[0]

            if isinstance(operand, Call) and operand.op == op:
                acc.extend(operand.args)
            elif isinstance(operand, list):
                acc.append(operand)
            elif isinstance(operand, dict) and operand.get(op):
                acc.extend(operand.get(op))
            else:
                acc.append(operand)
        binary_op = Call(op, acc, {})
    return binary_op

