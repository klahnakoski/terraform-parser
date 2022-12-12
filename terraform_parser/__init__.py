from mo_parsing import (
    Literal,
    SkipTo,
    Whitespace,
    Forward,
    delimited_list,
    Regex,
    infix_notation,
    set_parser_names,
    whitespaces, RIGHT_ASSOC, OneOrMore, ZeroOrMore, Group, Combine,
)

expression = Forward()
compound = Forward()

def multiline_content(tokens, _, string):
    content = string[tokens.start:tokens.end]
    return content


with whitespaces.NO_WHITESPACE:
    CR = Regex(r"\n")
    identifier = Regex(r"\w+")
    quote = Literal('"')
    string_var = Literal("${").suppress() + expression + Literal("}").suppress()
    string = Group(quote + ZeroOrMore(Regex(r"(\\\"|\$[^{]|[^\"$])+") | string_var) + quote)

    rest = Forward()

    def make_parser(tokens, _, string):
        eod = Literal(string[tokens.start:tokens.end])
        rest << (SkipTo(eod)("content") / multiline_content) + eod.suppress()


    multiline = (
            Literal("<<")
            + SkipTo(CR)("end") / make_parser
            + rest
    )

    path = Combine(delimited_list(identifier, "."))

comment = Literal("#") + SkipTo(CR)

white = Whitespace(white="\t ")
white.add_ignore(comment)

multiline_white = Whitespace()
multiline_white.add_ignore(comment)


def if_else(tokens):
    when, _, then, _, els_ = list(tokens)
    return {"when": when, "then": then, "else": els_}


with white:
    assignment = identifier("name") + "=" + compound("value")
    property = string("name") + "=" + compound("value")
    assignments = delimited_list(assignment | property, separator=OneOrMore(CR))


with multiline_white:
    json = "{" + assignments + "}"

    compound << (string | "[" + delimited_list(expression) + "]" | json | multiline | path)

    expression << (
        infix_notation(
            compound,
            [
                ((Literal("?"), Literal(":")), 3, RIGHT_ASSOC, if_else),
            ]
        )("value").set_parser_name("expression")
    )

    resource = (
            identifier("type")
            + string("name")
            + "{"
            + assignments
            + "}"
    )

set_parser_names()


def parse(content):
    return resource.parse(content)
