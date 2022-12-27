# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
# SIMPLE OPERATORS
from mo_parsing import Literal, RIGHT_ASSOC, Regex, Optional, LEFT_ASSOC, Keyword
from terraform_parser.utils import keyword, SQL_NULL, set_parser_names

NULL = keyword("null") / SQL_NULL
TRUE = keyword("true") / True
FALSE = keyword("false") / False
LP, RP = Literal("(").suppress(), Literal(")").suppress()
LB, RB = Literal("[").suppress(), Literal("]").suppress()
LC, RC = Literal("{").suppress(), Literal("}").suppress()
COMMA = Literal(",").suppress()

CONCAT = Literal("||").set_parser_name("concat")
MUL = Literal("*").set_parser_name("mul")
DIV = Literal("/").set_parser_name("div")
MOD = Literal("%").set_parser_name("mod")
POS = Literal("+").set_parser_name("pos")
NEG = Literal("-").set_parser_name("neg")
ADD = Literal("+").set_parser_name("add")
SUB = Literal("-").set_parser_name("sub")
BINARY_NOT = Literal("~").set_parser_name("binary_not")
BINARY_AND = Literal("&").set_parser_name("binary_and")
BINARY_OR = Literal("|").set_parser_name("binary_or")
GTE = Literal(">=").set_parser_name("gte")
LTE = Literal("<=").set_parser_name("lte")
LT = Literal("<").set_parser_name("lt")
GT = Literal(">").set_parser_name("gt")
EQ = Literal("==").set_parser_name("neq")
NEQ = (Literal("!=") | Literal("<>")).set_parser_name("neq")
THEN = Literal("?").set_parser_name("if_then_else")
COLON = Literal(":")
ASSIGN = Optional(Literal("=")).suppress()
ELLIPSIS = Literal("...")
FOR = Keyword("for")
IN = Keyword("in")
IF = Keyword("if")


KNOWN_OPS = [
    CONCAT,
    POS,
    NEG,
    MUL | DIV | MOD,
    ADD | SUB,
    BINARY_NOT,
    BINARY_AND,
    BINARY_OR,
    GTE | LTE | LT | GT,
    EQ | NEQ,
    (THEN, COLON)
]


unary_ops = {
    POS: RIGHT_ASSOC,
    NEG: RIGHT_ASSOC,
    BINARY_NOT: RIGHT_ASSOC,
}


binary_ops = {
    "||": "concat",
    "*": "mul",
    "/": "div",
    "%": "mod",
    "+": "add",
    "-": "sub",
    "&": "binary_and",
    "|": "binary_or",
    "<": "lt",
    "<=": "lte",
    ">": "gt",
    ">=": "gte",
    "=": "eq",
    "==": "eq",
    "!=": "neq",
    "<>": "neq",
}

# NUMBERS
real_num = Regex(r"[+-]?(\d+\.\d*|\.\d+)([eE][+-]?\d+)?") / (lambda t: float(t[0]))
int_num = Regex(r"[+-]?\d+") / (lambda t: int(t[0]))

keywords = TRUE | FALSE | NULL | FOR | IN | IF

set_parser_names()