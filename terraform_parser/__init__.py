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

from mo_parsing import *
from mo_parsing import whitespaces, Whitespace
from terraform_parser.functions import *
from terraform_parser.keywords import *
from terraform_parser.utils import scrub, keyword

expression = Forward()
compound = Forward()

with whitespaces.NO_WHITESPACE:
    CR = Regex(r"\n")
    identifier = Regex(r"\w+")
    quote = Literal('"').suppress()
    code = Literal("${").suppress() + expression + Literal("}").suppress()
    string_segment = Regex(r"(\\\"|\$[^{]|[^\"$])+") / to_string
    compound_string = (
        Group(quote + ZeroOrMore(string_segment | code) + quote) / to_concat
    )
    multiline_string = Regex(r"(\$[^{]|[^$])+") / to_multiline_string
    multiline_string_parser = ZeroOrMore(multiline_string | code).finalize()

    rest = Forward()

    def eod_parser(tokens, _, string):
        eod = Literal(string[tokens.start : tokens.end])
        rest << (SkipTo(eod)("content") / multiline_content) + eod.suppress()

    multiline = (
        Literal("<<").suppress() + SkipTo(CR)("end") / eod_parser + rest
    ) / to_multiline

    path = delimited_list(identifier|"*", ".", combine=True)

comment = Literal("#").suppress() + SkipTo(CR)

white = Whitespace(white="\t ")
white.add_ignore(comment)

multiline_white = Whitespace()
multiline_white.add_ignore(comment)

json = Forward()

with white:
    assignment = identifier + Group(ASSIGN + compound | json)

    property = compound_string + Group(ASSIGN + compound | json)
    provisioner = Keyword("provisioner") + compound_string + json

    assignments = delimited_list(
        Group(provisioner | assignment | property)/to_inner_object, separator=OneOrMore(CR)
    )
    dynamic_accessor = LB + expression + RB

with multiline_white:
    json << LC + Optional(Group(assignments)) + RC
    compound << (
        compound_string
        | LB + delimited_list(expression | Empty()) + RB
        | json
        | multiline
        | (identifier("op") + LP + delimited_list(expression("params")) + RP)
        / to_json_call
        | path
    )

    expression << (
        infix_notation(
            compound,
            [(dynamic_accessor, 1, LEFT_ASSOC, to_offset)]
            + [
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

    resource = (
        Keyword("resource").suppress() + compound_string + compound_string + json("params")
    ) / to_inner_object
    data = (
        Keyword("data") + compound_string + compound_string + json
    ) / to_inner_object
    module = (Keyword("module").suppress() + compound_string + json) / to_inner_object

    # module = (identifier("type") + string("name") + json("params")) / dict
    variable = (
        Keyword("variable") / "var" + compound_string + json("params")
    ) / to_inner_object
    local = (Keyword("locals") / "local" + json("params")) / to_inner_object

    terraform = ZeroOrMore(resource | data | module | variable | local)

set_parser_names()


def parse(content) -> Data:
    return scrub(terraform.parse(content, parse_all=True))


export("terraform_parser.functions", multiline_string_parser)
