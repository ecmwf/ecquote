#!/usr/bin/env python3
# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import io
import logging

LOG = logging.getLogger(__name__)


class Reader:
    def __init__(self, file):
        self.file = file
        self._c = None

    def read(self):
        if self._c is not None:
            c = self._c
            self._c = None
            return c
        return self.file.read(1)

    def peek(self):
        if self._c is None:
            self._c = self.file.read(1)
        return self._c


class Parser:
    def __init__(self, stream, comments=True, path=None, text=None):
        self.reader = Reader(stream)
        self.comments = comments
        self.eof = False
        self.line = 0
        self.path = path
        self.text = text

    def __repr__(self):
        if self.text:
            return f"Parser[{self.text}:{self.line+1}]"
        else:
            return f"Parser[{self.path}:{self.line+1}]"

    def read(self):

        if self.eof:
            return ""

        c = self.reader.read()
        if c == "":
            self.eof = True

        return c

    def peek(self, spaces=False):
        while True:

            c = self.reader.peek()

            if self.comments and c == "#":
                while c != "\n" and c != 0:
                    c = self.read()
                    if c == "\n":
                        self.line += 1

                if c == "":
                    return ""

                return self.peek(spaces)

            if spaces or not str.isspace(c):
                return c
            else:
                c = self.read()
                if c == "\n":
                    self.line += 1

    def next(self, spaces=False):

        while True:
            c = self.read()
            if c == "":
                raise ValueError(f"{self}: next() reached eof")

            if c == "\n":
                self.line += 1

            if self.comments and c == "#":
                while c != "\n" and c != "":
                    c = self.read()
                    if c == "\n":
                        self.line += 1

                if c == "":
                    raise ValueError(f"{self}: next() reached eof")

                return self.next(spaces)

            if spaces or not str.isspace(c):
                return c

    def consume(self, s):
        for c in s:
            n = self.next()
            if c != n:
                raise ValueError(f"{self}: consume expecting '{c}', got '{n}'")


class RequestParser(Parser):
    def parse_string(self):
        quote = self.peek()

        if quote not in ("'", '"'):
            raise ValueError(f"{self}: invalid quote")

        self.consume(quote)
        s = ""
        while True:
            c = self.next(True)
            if c == quote:
                break

            s += c
        return s

    def parse_ident(self):
        s = ""
        c = self.peek()
        while str.isalnum(c) or c in (".", ":", "-", "_"):
            s += self.next()
            c = self.peek(True)
        assert s, self
        return s

    def next_token(self):
        if self.peek() in ('"', "'"):
            return self.parse_string()
        return self.parse_ident()

    def parse_list(self):
        result = [self.next_token()]
        while self.peek() == "/":
            self.consume("/")
            result.append(self.next_token())

        return tuple(result)

    def next_request(self, r):
        if self.peek() == "":
            return None, None

        lineno = None
        while True:
            token = self.next_token()
            if lineno is None:
                lineno = self.line + 1
            p = self.peek()

            if p == ",":  # ignore verb
                self.consume(",")
                continue

            assert p == "=", (p, token, self.next_token())
            self.consume("=")
            r[token] = self.parse_list()

            if self.peek() != ",":
                break

            self.consume(",")

        return lineno, r

    def parse_requests(self, inherit):
        r = {}
        while True:
            lineno, r = self.next_request(r)
            if r is None:
                break
            yield lineno, dict(**r)
            if not inherit:
                r = {}


def _parse_requests(stream, inherit=True, path=None, text=None):
    """
    Parse a request file and returns a list of dictionaries
    """
    parser = RequestParser(stream, path=path, text=text)
    for lineno, r in parser.parse_requests(inherit):
        if path:
            r["path"] = (path,)
            r["line"] = (lineno,)
        yield r


def parse_request_file(path, inherit=True):
    """
    Parse a request file and returns a list of dictionaries
    """

    LOG.debug("Parse request file %s", path)
    with open(path) as f:
        for r in _parse_requests(f, inherit, path):
            yield r


def parse_request_string(s, inherit=True):
    yield from _parse_requests(io.StringIO(s), inherit, text=s)


def parse_single_request(s):
    parsed = list(parse_request_string(s))
    assert len(parsed) == 1, parsed
    return parsed[0]


if __name__ == "__main__":
    s = """aoo=b,c=d,
    p=i
    ,e=f,g=h/i
    aoo=b,c=d,
    p=i
    ,e=f,g=h/i
    """
    p = RequestParser(io.StringIO(s))

    print(p.parse_requests())
