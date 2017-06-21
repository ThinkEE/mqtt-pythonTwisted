################################################################################
# MIT License
#
# Copyright (c) 2017 Jean-Charles Fosse & Johann Bigler
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
################################################################################

class IdGenerator(object):
    """
    ID generator for WAMP request IDs.
    WAMP request IDs are sequential per WAMP session, starting at 1 and
    wrapping around at 2**53 (both value are inclusive [1, 2**53]).
    The upper bound **2**53** is chosen since it is the maximum integer that can be
    represented as a IEEE double such that all smaller integers are representable as well.
    Hence, IDs can be safely used with languages that use IEEE double as their
    main (or only) number type (JavaScript, Lua, etc).
    See https://github.com/wamp-proto/wamp-proto/blob/master/spec/basic.md#ids
    """

    def __init__(self):
        self._next = 0  # starts at 1; next() pre-increments

    def next(self):
        """
        Returns next ID.
        :returns: The next ID.
        :rtype: int
        """
        self._next += 1
        if self._next > 65536:
            self._next = 1
        return self._next

    # generator protocol
    def __next__(self):
        return self.next()
