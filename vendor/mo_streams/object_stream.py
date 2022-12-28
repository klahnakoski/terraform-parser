# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from typing import Any, Iterator, Dict, Tuple
from zipfile import ZIP_STORED

from mo_future import zip_longest, first
from mo_imports import expect, export
from mo_json import JxType, JX_INTEGER
from mo_logs import logger

from mo_files import File
from mo_streams import ByteStream
from mo_streams._utils import (
    Reader,
    Writer,
    chunk_bytes,
    Stream,
)
from mo_streams.byte_stream import DEBUG
from mo_streams.files import File_usingStream
from mo_streams.function_factory import factory
from mo_streams.type_utils import Typer, LazyTyper

stream = expect("stream")

ERROR = {}
WARNING = {}
NONE = {}


class ObjectStream(Stream):
    """
    A STREAM OF OBJECTS
    """

    def __init__(self, values, datatype, schema):
        if not isinstance(datatype, Typer) or isinstance(datatype, LazyTyper):
            logger.error(
                "expecting datatype to be Typer not {{type}}",
                type=datatype.__class__.__name__,
            )
        self._iter: Iterator[Tuple[Any, Dict[str, Any]]] = values
        self.type_: Typer = datatype
        self._schema = schema

    def __getattr__(self, item):
        type_ = getattr(self.type_, item)

        def read():
            for v, a in self._iter:
                try:
                    yield getattr(v, item), a
                except (StopIteration, GeneratorExit):
                    raise
                except Exception as cause:
                    DEBUG and logger.warn(
                        "can not get attribute {{item|quote}}", cause=cause
                    )
                    yield None, a

        return ObjectStream(read(), type_, self._schema)

    def __call__(self, *args, **kwargs):
        type_ = self.type_(*args, **kwargs)

        if type_.type_ == bytes:

            def read_bytes():
                for m, a in self._iter:
                    try:
                        yield m(*args, **kwargs)
                    except (StopIteration, GeneratorExit):
                        raise
                    except Exception:
                        yield None

            return ByteStream(Reader(read_bytes()))

        def read():
            for m, a in self._iter:
                try:
                    yield m(*args, **kwargs), a
                except (StopIteration, GeneratorExit):
                    raise
                except Exception:
                    yield None, a

        return ObjectStream(read(), type_, self._schema)

    def map(self, accessor):
        if isinstance(accessor, str):
            type_ = getattr(self.type_, accessor)
            return ObjectStream(
                ((getattr(v, accessor), a) for v, a in self._iter), type_, self._schema
            )
        fact = factory(accessor, self.type_)
        do_accessor = fact.build(self.type_, self._schema)

        def read():
            for v, a in self._iter:
                try:
                    yield do_accessor(v, a), a
                except (StopIteration, GeneratorExit):
                    raise
                except Exception as cause:
                    yield None, a

        if isinstance(fact.type_, LazyTyper):
            type_ = fact.type_._resolver(self.type_)
        else:
            type_ = fact.type_

        return ObjectStream(read(), type_, self._schema)

    def filter(self, predicate):
        fact = factory(predicate, return_type=bool)
        filteror = fact.build(self.type_, self._schema)

        def read():
            for v, a in self._iter:
                try:
                    if filteror(v, a):
                        yield v, a
                except (StopIteration, GeneratorExit):
                    raise
                except Exception as cause:
                    pass

        return ObjectStream(read(), self.type_, self._schema)


    def attach(self, **kwargs):
        facts = {k: factory(v) for k, v in kwargs.items()}

        more_schema = JxType()  # NOT AT REAL TYPE, WE ADD PYTHON TYPES ON THE LEAVES
        for k, f in facts.items():
            setattr(more_schema, k, f.type_)

        mapper = {k: f.build(f.type_, self._schema) for k, f in facts.items()}

        def read():
            for v, a in self._iter:
                yield v, {**a, **{k: m(v, a) for k, m in mapper.items()}}

        return ObjectStream(read(), self.type_, self._schema | more_schema)

    def exists(self):
        def read():
            for v, a in self._iter:
                if v != None:
                    yield v, a

        return ObjectStream(read(), self.type_, self._schema)

    def enumerate(self):
        def read():
            for i, (v, a) in enumerate(self._iter):
                yield v, {**a, "index": i}

        return ObjectStream(read(), self.type_, self._schema | JxType(index=JX_INTEGER))

    def flatten(self):
        def read():
            for v, a in self._iter:
                for vv, aa in stream(v)._iter:
                    yield vv, {**a, **aa}

        return ObjectStream(read(), self.type_, self._schema)

    def reverse(self):
        def read():
            yield from reversed(list(self._iter))

        return ObjectStream(read(), self.type_, schema=self._schema)

    def sort(self, *, key=None, reverse=0):
        if key:
            key = lambda t: key(t[0])

        def read():
            yield from sorted(self._iter, key=key, reverse=reverse)

        return ObjectStream(read(), self.type_, self._schema)

    def distinct(self):
        def read():
            acc = set()
            for v, a in self._iter:
                if v in acc:
                    continue
                acc.add(v)
                yield v, a

        return ObjectStream(read(), self.type_, self._schema)

    def append(self, value):
        def read():
            yield from self._iter
            yield value, {}

        return ObjectStream(read(), self.type_, self._schema)

    def extend(self, values):
        suffix = stream(values)

        def read():
            yield from self._iter
            yield from suffix._iter

        return ObjectStream(read(), self.type_, self._schema | suffix._schema)

    def zip(self, *others):
        streams = [stream(o) for o in others]

        def read():
            yield from zip_longest(self._iter, *(s._iter for s in streams))

        return TupleStream(
            read(),
            self._example,
            self.type_,
            sum((s._schema for s in streams), JxType()),
        )

    def limit(self, count):
        def read():
            try:
                for i in range(count):
                    yield next(self._iter)
            except StopIteration:
                pass

        return ObjectStream(read(), self.type_, self._schema)

    def materialize(self):
        return ObjectStream(list(self._iter), self.type_, self._schema)

    def to_list(self):
        return list(v for v, _ in self._iter)

    def count(self):
        return sum(1 for _ in self._iter)

    def to_dict(self, key=None):
        """
        CONVERT STREAM TO dict
        :param key: CHOOSE WHICH ANNOTATION IS THE KEY
        """
        if key is None:
            candidates = self._schema.__dict__.keys()
            if len(candidates) != 1:
                logger.error(
                    "expecting attachment to have just one property, not {{num}}",
                    num=len(candidates),
                )
            key = first(candidates)

        return {a[key]: v for v, a in self._iter}

    def to_zip(
        self, compression=ZIP_STORED, allowZip64=True, compresslevel=None,
    ):
        from zipfile import ZipFile, ZipInfo

        type_ = self.type_.type_
        if type_ is File:
            pass
        elif type_ is File_usingStream:
            pass
        else:
            raise NotImplementedError("expecting stream of Files")

        def read():
            mode = "w"
            writer = Writer()
            with ZipFile(
                writer,
                mode=mode,
                compression=compression,
                allowZip64=allowZip64,
                compresslevel=compresslevel,
            ) as archive:
                for file, _ in self._iter:
                    info = ZipInfo(file.rel_path)
                    with archive.open(info, mode=mode) as target:
                        for chunk in chunk_bytes(file.bytes()):
                            target.write(chunk)
                            yield writer.read()

            yield writer.read()
            writer.close()

        return ByteStream(Reader(read()))


export("mo_streams.byte_stream", ObjectStream)
