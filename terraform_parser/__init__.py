# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from mo_dots import Data
from mo_imports import export

from mo_parsing import whitespaces, Whitespace

from mo_parsing import *
from terraform_parser.functions import *
from terraform_parser.keywords import unary_ops, KNOWN_OPS
from terraform_parser.utils import scrub

expression = Forward()
compound = Forward()


with whitespaces.NO_WHITESPACE:
    CR = Regex(r"\n")
    identifier = Regex(r"\w+")
    quote = Literal('"').suppress()
    code = Literal("${").suppress() + expression + Literal("}").suppress()
    simple_string = Regex(r"(\\\"|\$[^{]|[^\"$])+") / to_string
    string = Group(quote + ZeroOrMore(simple_string | code) + quote) / to_concat
    multiline_string = Regex(r"(\$[^{]|[^$])+") / to_multiline_string
    multiline_string_parser = ZeroOrMore(multiline_string | code).finalize()

    rest = Forward()

    def eod_parser(tokens, _, string):
        eod = Literal(string[tokens.start : tokens.end])
        rest << (SkipTo(eod)("content") / multiline_content) + eod.suppress()

    multiline = (
        Literal("<<").suppress() + SkipTo(CR)("end") / eod_parser + rest
    ) / to_multiline

    path = delimited_list(identifier, ".", combine=True)

comment = Literal("#").suppress() + SkipTo(CR)

white = Whitespace(white="\t ")
white.add_ignore(comment)

multiline_white = Whitespace()
multiline_white.add_ignore(comment)


with white:
    assignment = identifier("name") / to_var + "=" + compound("value")
    property = string("name") / to_name + "=" + compound("value")
    assignments = (
        delimited_list(assignment | property, separator=OneOrMore(CR)) / to_assign
    )


with multiline_white:
    json = Literal("{").suppress() + Optional(assignments) + Literal("}").suppress()

    compound << (
        string | "[" + delimited_list(expression) + "]" | json | multiline | path
    )

    expression << (
        infix_notation(
            compound, [
                        (
                            o,
                            1 if o in unary_ops else (3 if isinstance(o, tuple) else 2),
                            unary_ops.get(o, LEFT_ASSOC),
                            to_json_operator,
                        )
                        for o in KNOWN_OPS
                    ],
        )
        / to_code
    )

    tf_type = (Keyword("data") | Keyword("resource"))
    resource = (tf_type("type") + string("resource") + string("name") + json("params")) / dict
    module = (identifier("type") + string("name") + json("params")) / dict

    terraform = ZeroOrMore(resource | module)

set_parser_names()


def parse(content) -> Data:
    return scrub(terraform.parse(content, parse_all=True))


export("terraform_parser.functions", multiline_string_parser)
