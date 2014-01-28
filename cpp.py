#!/usr/bin/python

# Copyright (C) 2014 Reece H. Dunn
#
# This file is part of documentation-generator.
#
# documentation-generator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# documentation-generator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with documentation-generator.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import re


class Token:
	def __init__(self, value):
		self.value = value

	def __repr__(self):
		return '%s(%s)' % (self.__class__.__name__, repr(self.value))


class WhiteSpace(Token):
	def __init__(self, value):
		Token.__init__(self, value)


_tokens = [
	(re.compile(r'\s+'), WhiteSpace),
]


def match_token(text, pos):
	for matcher, token in _tokens:
		m = matcher.match(text, pos)
		if m:
			return token(m.group(0)), m.end()
	return None, None


def tokenizer(text):
	pos = 0
	while pos < len(text):
		token, end = match_token(text, pos)
		if not token:
			raise Exception('Invalid C++ token : %s' % text[pos:])
		pos = end
		yield token


if __name__ == '__main__':
	tokenizer_testcases = [
		# whitespace ############################################
		(' ', [WhiteSpace(' ')]),
		('\t', [WhiteSpace('\t')]),
		('\r', [WhiteSpace('\r')]),
		('\n', [WhiteSpace('\n')]),
		('    ', [WhiteSpace('    ')]),
		(' \t\r\n', [WhiteSpace(' \t\r\n')]),
	]

	passed = 0
	failed = 0
	for text, result in tokenizer_testcases:
		got = repr(list(tokenizer(text)))
		expected = repr(result)
		if expected == got:
			passed = passed + 1
		else:
			print('test %s failed -- expected %s, got %s' % (repr(text), expected, got))
			failed = failed + 1
	print('passed : %d' % passed)
	print('failed : %d' % failed)
	print('total  : %d' % (passed + failed))
