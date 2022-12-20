# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_streams._utils import Stream


class EmptyStream(Stream):
    def __getattr__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def to_dict(self):
        return {}

    def to_list(self):
        return []

    def to_bytes(self):
        return b""

    def to_str(self):
        return ""
