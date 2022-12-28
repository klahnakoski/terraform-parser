# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import inspect

from mo_imports import expect, export
from mo_logs import logger

from mo_streams._utils import arg_spec

parse, ANNOTATIONS = expect("parse", "ANNOTATIONS")


class Typer:
    """
    Smooth out the lumps of Python type manipulation
    """

    def __init__(self, *, example=None, type_=None, function=None):
        if function:
            # find function return type
            inspect.signature(function)
        elif example:
            self.type_ = type(example)
        elif type_ is LazyTyper:
            self.__class__ = LazyTyper
        else:
            self.type_ = type_

    def __getattr__(self, item):
        try:
            attribute_type = self.type_.__annotations__[item]
            return Typer(type_=attribute_type)
        except:
            pass

        desc = arg_spec(self.type_, item)
        if desc:
            return_type = desc.annotations.get("return")
            if return_type:
                return parse(return_type)
            return_type = ANNOTATIONS.get((self.type_, item))
            if return_type:
                return return_type

            logger.error(
                "expecting {{type}}.{{item}} to have annotated return type",
                type=self.type_.__name__,
                item=item,
            )
        logger.error(
            """expecting {{type}} to have attribute {{item|quote}} declared with a type annotation""",
            type=self.type_.__name__,
            item=item,
        )

    def __add__(self, other):
        if self.type_ is str or other.type_ is str:
            return Typer(type_=str)
        logger.error("not handled")

    def __call__(self, *args, **kwargs):
        spec = inspect.getfullargspec(self.type_)

    def __str__(self):
        return f"Typer(class={self.type_.__name__})"


class CallableTyper(Typer):
    """
    ASSUME THIS WILL BE CALLED, AND THIS IS THE TYPE RETURNED
    """

    def __init__(self, *, type_):
        self.type_ = type_

    def __call__(self, *args, **kwargs):
        return Typer(type_=self.type_)

    def __getattr__(self, item):
        spec = inspect.getmembers(self.type_)
        for k, m in spec:
            if k == item:
                inspect.ismethod(m)

    def __str__(self):
        return f"CallableTyper(return_type={self.type_.__name__})"


class UnknownTyper(Typer):
    """
    MANY TIMES WE DO NOT KNOW THE TYPE, BUT MAYBE WE NEVER NEED IT
    """

    def __init__(self, error):
        Typer.__init__(self)
        self._error: Exception = error

    def __getattr__(self, item):
        def build(type_):
            return getattr(type_, item)

        return UnknownTyper(build)

    def __call__(self, *args, **kwargs):
        def build(type_):
            return type_

        return UnknownTyper(build)

    def __str__(self):
        return "UnknownTyper()"


class LazyTyper(Typer):
    """
    PLACEHOLDER FOR STREAM ELEMENT TYPE, UNKNOWN DURING LAMBDA DEFINITION
    """

    def __init__(self, resolver=None):
        Typer.__init__(self)
        self._resolver: Typer = resolver or (lambda t: t)

    def __getattr__(self, item):
        def build(type_):
            return getattr(type_, item)

        return LazyTyper(build)

    def __call__(self, *args, **kwargs):
        def build(type_):
            return type_

        return LazyTyper(build)

    def __str__(self):
        return "LazyTyper()"


export("mo_streams.type_parser", Typer)
export("mo_streams.byte_stream", Typer)
