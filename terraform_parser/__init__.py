from mo_parsing import (
    Literal,
    SkipTo,
    Whitespace,
    Forward,
    delimited_list,
    Regex,
    infix_notation,
    set_parser_names,
    whitespaces, RIGHT_ASSOC, OneOrMore, ZeroOrMore, Group, )
from terraform_parser.functions import to_string, multiline_content, to_code, if_else, to_assign, to_name, to_multiline, \
    to_var

expression = Forward()
compound = Forward()


with whitespaces.NO_WHITESPACE:
    CR = Regex(r"\n")
    identifier = Regex(r"\w+")
    quote = Literal('"').suppress()
    code = Literal("${").suppress() + expression + Literal("}").suppress()
    simple_string = Regex(r"(\\\"|\$[^{]|[^\"$])+") / to_string
    string = Group(quote + ZeroOrMore(simple_string | code) + quote)

    rest = Forward()

    def eod_parser(tokens, _, string):
        eod = Literal(string[tokens.start:tokens.end])
        rest << (SkipTo(eod)("content") / multiline_content) + eod.suppress()


    multiline = (
            Literal("<<").suppress()
            + SkipTo(CR)("end") / eod_parser
            + rest
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
    assignments = delimited_list(assignment | property, separator=OneOrMore(CR)) / to_assign


with multiline_white:
    json = Literal("{").suppress() + assignments + Literal("}").suppress()

    compound << (string | "[" + delimited_list(expression) + "]" | json | multiline | path)

    expression << (
        infix_notation(
            compound,
            [
                ((Literal("?"), Literal(":")), 3, RIGHT_ASSOC, if_else),
            ]
        ) / to_code
    )

    resource = (
            identifier("type")
            + string("name")
            + json("params")
    ) / dict

set_parser_names()


def parse(content):
    return resource.parse(content)
