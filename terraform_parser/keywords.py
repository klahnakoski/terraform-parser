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
LPC = Literal("%{").suppress()
LDC = Literal("${").suppress()
COMMA = Literal(",").suppress()

MUL = Literal("*").set_parser_name("mul")
DIV = Literal("/").set_parser_name("div")
MOD = Literal("%").set_parser_name("mod")
POS = Literal("+").set_parser_name("pos")
NEG = Literal("-").set_parser_name("neg")
ADD = Literal("+").set_parser_name("add")
SUB = Literal("-").set_parser_name("sub")
NOT = Literal("!").set_parser_name("not")
AND = Literal("&&").set_parser_name("and")
OR = Literal("||").set_parser_name("or")
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
FOR = Keyword("for").suppress()
IN = Keyword("in")
IF = Keyword("if").suppress()
ELSE = Keyword("else").suppress()


KNOWN_OPS = [
    POS,
    NEG,
    MUL | DIV | MOD,
    ADD | SUB,
    GTE | LTE | LT | GT,
    EQ | NEQ,
    (THEN, COLON),
    NOT,
    AND,
    OR,
]


unary_ops = {
    NOT: RIGHT_ASSOC,
    POS: RIGHT_ASSOC,
    NEG: RIGHT_ASSOC,
}


binary_ops = {
    "*": "mul",
    "/": "div",
    "%": "mod",
    "+": "add",
    "-": "sub",
    "<": "lt",
    "<=": "lte",
    ">": "gt",
    ">=": "gte",
    "=": "eq",
    "==": "eq",
    "!=": "neq",
    "<>": "neq",
    "&&": "and",
    "||": "or",
}

# NUMBERS
real_num = Regex(r"[+-]?(\d+\.\d*|\.\d+)([eE][+-]?\d+)?") / (lambda t: float(t[0]))
int_num = Regex(r"[+-]?\d+") / (lambda t: int(t[0]))

keywords = TRUE | FALSE | NULL | FOR | IN | IF

set_parser_names()
