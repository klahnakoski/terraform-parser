# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from mo_dots import is_null, Data, from_data
from mo_future import text, number_types, binary_type

from mo_parsing import *
from mo_parsing.utils import listwrap


class Call(object):
    __slots__ = ["op", "args", "kwargs"]

    def __init__(self, op, args, kwargs):
        self.op = op
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return f"{self.op}({self.args}, {self.kwargs})"


SQL_NULL = Call("null", [], {})
null_locations = []


def simple_op(op, args, kwargs):
    if args is None:
        kwargs[op] = {}
    else:
        kwargs[op] = args
    return kwargs


def normal_op(op, args, kwargs):
    output = Data(op=op)
    args = listwrap(args)
    if args and (not isinstance(args[0], dict) or args[0]):
        output.args = args
    if kwargs:
        output.kwargs = kwargs
    return from_data(output)


scrub_op = simple_op


def scrub(result):
    if result is SQL_NULL:
        return SQL_NULL
    elif result == None:
        return None
    elif isinstance(result, text):
        return result
    elif isinstance(result, binary_type):
        return result.decode("utf8")
    elif isinstance(result, number_types):
        return result
    elif isinstance(result, Call):
        kwargs = scrub(result.kwargs)
        args = scrub(result.args)
        if args is SQL_NULL:
            null_locations.append((kwargs, result.op))
        return scrub_op(result.op, args, kwargs)
    elif isinstance(result, dict) and not result:
        return result
    elif isinstance(result, list):
        output = [rr for r in result for rr in [scrub(r)]]

        if not output:
            return None
        elif len(output) == 1:
            return output[0]
        else:
            for i, v in enumerate(output):
                if v is SQL_NULL:
                    null_locations.append((output, i))
            return output
    else:
        # ATTEMPT A DICT INTERPRETATION
        try:
            kv_pairs = list(result.items())
        except Exception as c:
            print(c)
        output = {k: vv for k, v in kv_pairs for vv in [scrub(v)] if not is_null(vv)}
        if isinstance(result, dict) or output:
            for k, v in output.items():
                if v is SQL_NULL:
                    null_locations.append((output, k))
            return output
        return scrub(list(result))


def keyword(keywords):
    return And([
        Keyword(k, caseless=True) for k in keywords.split(" ")
    ]).set_parser_name(keywords) / (lambda: keywords.replace(" ", "_"))
