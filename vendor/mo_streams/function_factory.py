# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import inspect
from types import FunctionType

from mo_logs import logger, Except
from mo_logs.exceptions import ERROR, get_stacktrace

from mo_streams.type_utils import Typer, LazyTyper, CallableTyper, UnknownTyper

_get = object.__getattribute__
_set = object.__setattr__


class FunctionFactory:
    """
    See mo-streams/docs/function_factory.md
    """

    def __init__(self, builder, type_, desc):
        if not isinstance(type_, Typer):
            logger.error("expecting type, not {{type}}", type=type_)
        _set(self, "build", builder)
        _set(self, "type_", type_)
        _set(self, "_desc", desc)

    def __getattr__(self, item):
        def builder(type_, _schema):
            s = _get(self, "build")(type_, _schema)
            if item in _schema:

                def func(v, a):
                    return a[item]

                return func
            elif isinstance(item, FunctionFactory):
                i = item.build(type_, _schema)
                return lambda v, a: getattr(s(v, a), i(v, a))
            else:
                return lambda v, a: getattr(s(v, a), item)

        return FunctionFactory(
            builder, getattr(_get(self, "type_"), item), f"{self}.{item}"
        )

    def __eq__(self, other):
        func_other = factory(other)

        def builder(type_, _schema):
            s = self.build(type_, _schema)
            o = func_other.build(type_, _schema)

            def func(v, a):
                return s(v, a) == o(v, a)

            return func

        return FunctionFactory(builder, Typer(type_=bool), f"{other} == {self}")

    def __radd__(self, other):
        if isinstance(other, FunctionFactory):
            func_other = other
        else:
            func_other = FunctionFactory(
                lambda v, a: other, Typer(example=other), str(other)
            )

        def builder(type_, _schema):
            s = self.build(type_, _schema)
            o = func_other.build(type_, _schema)

            def func(v, a):
                return o + s(v, a)

            return func

        type_ = Typer(example=other) + _get(self, "type_")
        return FunctionFactory(builder, type_, f"{other} + {self}")

    def __call__(self, *args, **kwargs):
        args = [factory(a) for a in args]
        kwargs = {k: factory(v) for k, v in kwargs.items()}

        def builder(type_, _schema):
            s = self.build(type_, _schema)
            _args = [a.build(type_, _schema) for a in args]
            _kwargs = {k: v.build(type_, _schema) for k, v in kwargs.items()}

            def func(v, a):
                return s(v, a)(
                    *(f(v, a) for f in _args),
                    **{k: f(v, a) for k, f in _kwargs.items()},
                )

            return func

        desc_args = [str(a) for a in args]
        desc_args.extend(f"{k}={v}" for k, v in kwargs.items())
        params = ",".join(desc_args)

        return FunctionFactory(builder, self.type_(), f"{self}({params})")

    def __str__(self):
        return _get(self, "_desc")


def factory(item, self_type=None, return_type=None):
    if isinstance(item, (str, bytes, bool, int, float)):
        # CONSTANT
        def build_constant(type_, _schema):
            return lambda v, a: item

        return FunctionFactory(build_constant, Typer(example=item), f"{item}")
    elif isinstance(item, FunctionFactory):
        return item
    else:
        normalized_func, return_type = wrap_func(item, return_type=return_type)

        def builder3(type_, _schema):
            return normalized_func

        return FunctionFactory(builder3, return_type, f"returning {return_type}")


def build(item):
    if isinstance(item, FunctionFactory):
        return item.build

    def builder(type_, _schema):
        return lambda v, a: item

    return builder


# build list of single arg builtins, that can be used as parse actions
singleArgBuiltins = [
    sum,
    len,
    sorted,
    reversed,
    list,
    tuple,
    set,
    any,
    all,
    min,
    max,
]

singleArgTypes = [
    int,
    float,
    str,
    bool,
    complex,
    dict,
]


def wrap_func(func, return_type=None):
    try:
        func_name = getattr(func, "__name__", getattr(func, "__class__").__name__)
    except Exception:
        func_name = str(func)

    if func in singleArgBuiltins:
        spec = inspect.getfullargspec(func)
    elif func.__class__.__name__ == "staticmethod":
        func = func.__func__
        spec = inspect.getfullargspec(func)
    elif func.__class__.__name__ == "builtin_function_or_method":
        spec = inspect.getfullargspec(func)
    elif func in singleArgTypes:
        spec = inspect.FullArgSpec(["value"], None, None, None, [], None, {})
        return_type = func
    elif isinstance(func, type):
        spec = inspect.getfullargspec(func.__init__)
        new_func = func.__call__
        # USE ONLY FIRST PARAMETER
        num_args = len(spec.args) - 1  # ASSUME self IS FIRST ARG
        if num_args == 0:

            def wrap_init0(val, att):
                return new_func()

            return wrap_init0, Typer(type_=func)
        else:

            def wrap_init1(val, att):
                return new_func(val)

            return wrap_init1, Typer(type_=func)
    elif isinstance(func, FunctionType):
        spec = inspect.getfullargspec(func)
    elif hasattr(func, "__call__"):
        spec = inspect.getfullargspec(func)

    if spec.varargs:
        num_args = 3
    elif spec.args and spec.args[0] in ["cls", "self"]:
        num_args = len(spec.args) - 1
    else:
        num_args = len(spec.args)

    if not return_type:
        return_type = spec.annotations.get("return")
    if return_type:
        return_type = Typer(type_=return_type)
    else:
        cause = Except(
            ERROR,
            "expecting {{function}} to have annotated return type",
            {"function": func_name},
            trace=get_stacktrace(start=3)
        )
        return_type = UnknownTyper(cause)

    if num_args == 0:
        def wrapper0(val, att):
            return func()

        wrapper = wrapper0
    elif num_args == 1:

        def wrapper1(val, att):
            return func(val)

        wrapper = wrapper1
    else:
        return func, return_type

    # copy func name to wrapper for sensible debug output
    wrapper.__name__ = func_name

    return wrapper, return_type


class TopFunctionFactory(FunctionFactory):
    """
    it(x)  RETURNS A FunctionFactory FOR x
    """

    def __call__(self, value):
        if isinstance(value, FunctionFactory):
            logger.error("don't do this")

        def builder(type_, _schema):
            return lambda v, a: value

        if isinstance(value, type):
            return FunctionFactory(builder, CallableTyper(type_=value), f"{value}")

        return FunctionFactory(builder, Typer(type_=type(value)), f"{value}")

    def __str__(self):
        return "it"


def noop(v, a) -> LazyTyper:
    return v


it = factory(noop)
it.__class__ = TopFunctionFactory
