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

from mo_parsing import ParseResults, Forward, Group, is_number, Keyword, quote
from terraform_parser.keywords import binary_ops
from terraform_parser.utils import SQL_NULL, Call, And

multiline_string_parser = expect("multiline_string_parser")


def first(values):
    if isinstance(values, ParseResults):
        return values[0]
    else:
        return values


def keyword(keywords):
    return And([
        Keyword(k, caseless=True) for k in keywords.split(" ")
    ]).set_parser_name(keywords) / (lambda: keywords.replace(" ", "_"))


def to_string(tokens):
    value = json.loads(f'"{tokens[0].replace("$${", "${").replace("%%{", "%{")}"')
    return {"literal": value}


def to_concat(tokens):
    items = list(tokens)
    if not items:
        return {"literal": ""}
    if len(items) == 1 and (not isinstance(items[0], dict) or "from" not in items[0]):
        return tokens
    return {"concat": items}


def to_multiline_string(tokens):
    value = tokens[0].replace("$${", "${").replace("%%{", "%{")
    return {"literal": value}


def to_multiline(tokens):
    return list(multiline_string_parser.parse(tokens["content"]))


def multiline_content(tokens, _, string):
    content = string[tokens.start : tokens.end]
    return content


def to_inner_object(tokens):
    items = list(tokens)
    prev = items[-1]
    for v in reversed(items[:-1]):
        while isinstance(v, ParseResults):
            v = v[0]
        if isinstance(v, dict):
            if "literal" in v:
                v = v["literal"]
            else:
                raise NotImplementedError("do not know what to do here")
        prev = {v: prev}
    return prev


def to_splat(tokens):
    expr, _ = tokens.tokens
    return Call("from", [expr], {})


def to_offset(tokens):
    expr, offset = tokens.tokens

    if isinstance(expr, ParseResults) and isinstance(expr[0], Call):
        call = expr[0]
        if call.op == "from":
            select = call.kwargs.setdefault("select", {})
            value = select.get("value")
            if not value:
                select["value"] = offset[0]["literal"]
            else:
                select["value"] = value + "." + offset[0]["literal"]
            return call
    return Call("get", [expr, *offset], {})


def to_list(tokens):
    expr, _ = list(tokens)
    return Call("list", [expr], {})


def to_json_call(tokens):
    # ARRANGE INTO {op: params} FORMAT
    op = tokens["op"].lower()
    op = binary_ops.get(op, op)
    params = tokens["params"]
    if isinstance(params, (dict, str, int, Call)):
        args = [params]
    else:
        args = list(params)

    kwargs = {k: v for k, v in tokens.items() if k not in ("op", "params", "kwargs")}
    more_kwargs = tokens["kwargs"]
    if more_kwargs:
        for kv in list(more_kwargs):
            kwargs.update(kv)

    return ParseResults(
        tokens.type,
        tokens.start,
        tokens.end,
        [Call(op, args, kwargs)],
        tokens.failures,
    )


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

    if op in {"add", "mul", "and", "or"}:
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
