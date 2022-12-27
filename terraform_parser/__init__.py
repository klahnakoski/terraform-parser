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
code = Forward()

with whitespaces.NO_WHITESPACE:
    CR = Regex(r"\n")
    identifier = Regex(r"[\w](\[\d+\]|[-\w])*")
    name = ~keywords + identifier
    quote = Literal('"').suppress()
    string_segment = Regex(r"(\\\"|\$[^{]|[^\"$])+") / to_string
    compound_string = (
        Group(quote + ZeroOrMore(string_segment | code) + quote) / to_concat
    )
    multiline_string = Regex(r"(\$[^{]|[^$])+") / to_literal
    multiline_string_parser = ZeroOrMore(multiline_string | code).finalize()

    rest = Forward()

    def eod_parser(tokens, _, string):
        eod = Literal(string[tokens.start : tokens.end])
        rest << (SkipTo(eod)("content") / multiline_content) + eod.suppress()

    multiline = (
        Literal("<<").suppress()
        + Optional("-").suppress()
        + SkipTo(CR)("end") / eod_parser
        + rest
    ) / to_multiline

    path = Combine(
        name
        + Optional(
            ~ELLIPSIS + "." + delimited_list(identifier | "*", ".", combine=True)
        )
    )

    comment = (
        Literal("#").suppress() + SkipTo(CR)
        | "/*" + SkipTo("*/", include=True)
        | Literal("//").suppress() + SkipTo(CR)
    )

single_line_white = Whitespace(white="\t ")
single_line_white.add_ignore(comment)

multiline_white = Whitespace()
multiline_white.add_ignore(comment)

object = Forward()

with single_line_white:
    assignment = identifier + Group(ASSIGN + expression)
    property = compound_string + Group(ASSIGN + expression)
    sub_resource = (
        (keyword("provisioner") | keyword("backend")) + compound_string + object
    )

    assignments = delimited_list(
        Group(sub_resource | assignment | property) / to_inner_object,
        separator=OneOrMore(CR | COMMA),
    )
    splat_accessor = LB + "*" + RB
    dynamic_accessor = LB + expression + RB
    simple_accessor = Literal(".").suppress() + identifier / to_literal

with multiline_white:

    object << LC + Optional(Group(assignments)) + RC
    code << Literal("${").suppress() + expression + Literal("}").suppress()
    function_call = (
        name("op") + LP + delimited_list(expression("params")) + Optional(COMMA) + RP
    ) / to_json_call

    for_object = (
        LC
        + FOR
        + (
            (
                Group(identifier / (lambda t: {"name": t[0], "value": "index"}))
                + Optional(
                    COMMA
                    + Group(identifier / (lambda t: {"name": t[0], "value": "value"}))
                )
            )("select")
            + IN
            + compound("from")
        )("from")
        + COLON
        + expression("groupby")
        + "=>"
        + (expression("value"))("select")
        + Optional(IF + expression("where"))
        + RC
    )("object")
    for_tuple = (
        LB
        + FOR
        + (
            (
                Group(identifier / (lambda t: {"name": t[0], "value": "index"}))
                + Optional(
                    COMMA
                    + Group(identifier / (lambda t: {"name": t[0], "value": "value"}))
                )
            )("select")
            + IN
            + compound("from")
        )("from")
        + COLON
        + Group(expression("value"))("select")
        + Optional(IF + expression("where"))
        + RB
    )

    compound << (
        NULL
        | TRUE
        | FALSE
        | compound_string
        | for_object
        | for_tuple
        | LP + expression + RP
        | LB + delimited_list(expression) + Optional(COMMA) + RB
        | object
        | multiline
        | function_call
        | real_num
        | int_num
        | path
    )

    expression << (
        infix_notation(
            compound,
            [
                (splat_accessor, 1, LEFT_ASSOC, to_splat),
                (dynamic_accessor, 1, LEFT_ASSOC, to_offset),
                (simple_accessor, 1, LEFT_ASSOC, to_offset),
                (ELLIPSIS, 1, LEFT_ASSOC, to_list),
            ]
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
        Keyword("resource").suppress() + compound_string + compound_string + object
    )
    data = Keyword("data") + compound_string + compound_string + object
    module = Keyword("module").suppress() + compound_string + object
    # module = (identifier("type") + string("name") + json("params")) / dict
    variable = Keyword("variable") / "var" + compound_string + object
    output = Keyword("output") + compound_string + object
    local = Keyword("locals") / "local" + object
    provider = Keyword("provider") + compound_string + object
    terraform = keyword("terraform") + object
    everything = ZeroOrMore(
        (terraform | resource | data | module | variable | output | local | provider)
        / to_inner_object
    )

set_parser_names()


def parse(content) -> Data:
    return scrub(everything.parse(content, parse_all=True))


export("terraform_parser.functions", multiline_string_parser)

# https://github.com/hashicorp/hcl/blob/main/hclsyntax/spec.md
