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
	def __init__(self, value, kind):
		self.value = value
		self.kind  = kind

	def __repr__(self):
		if self.kind:
			return '%s(%s|%s)' % (self.__class__.__name__, repr(self.value), self.kind)
		return '%s(%s)' % (self.__class__.__name__, repr(self.value))


class WhiteSpace(Token):
	def __init__(self, value, kind=None):
		Token.__init__(self, value, kind)


class Identifier(Token):
	def __init__(self, value, kind=None):
		Token.__init__(self, value, kind)


class Keyword(Token):
	def __init__(self, value, kind=None):
		Token.__init__(self, value, kind)


class Operator(Token):
	def __init__(self, value, kind=None):
		Token.__init__(self, value, kind)


class Literal(Token):
	def __init__(self, value, kind):
		Token.__init__(self, value, kind)


_keywords = [ # 2.11 [lex.key]
	'alignas',		# C++11
	'alignof',		# C++11
	'and',			# operator
	'and_eq',		# operator
	'asm',
	'auto',
	'bitand',		# operator
	'bitor',		# operator
	'bool',
	'break',
	'case',
	'catch',
	'char',
	'char16_t',		# C++11
	'char32_t',		# C++11
	'class',
	'compl',		# operator
	'const',
	'constexpr',		# C++11
	'const_cast',
	'continue',
	'decltype',		# C++11
	'default',
	'delete',		# operator
	'do',
	'double',
	'dynamic_cast',
	'else',
	'enum',
	'explicit',
	'export',
	'extern',
	'false',
	'float',
	'for',
	'friend',
	'goto',
	'if',
	'inline',
	'int',
	'long',
	'mutable',
	'namespace',
	'new',			# operator
	'noexcept',		# C++11
	'not',			# operator
	'not_eq',		# operator
	'nullptr',		# C++11
	'operator',
	'or',			# operator
	'or_eq',		# operator
	'private',
	'protected',
	'public',
	'register',
	'reinterpret_cast',
	'return',
	'short',
	'signed',
	'sizeof',
	'static',
	'static_assert',	# C++11
	'static_cast',
	'struct',
	'switch',
	'template',
	'this',
	'thread_local',		# C++11
	'throw',
	'true',
	'try',
	'typedef',
	'typeid',
	'typename',
	'union',
	'unsigned',
	'virtual',
	'void',
	'volatile',
	'wchar_t',
	'while',
	'xor',			# operator
	'xor_eq',		# operator
]
_integer_suffix = '([uU](ll|LL|l|L)?|(ll|LL|l|L)[uU]?)' # 2.13.1 [lex.icon]
_tokens = [
	(re.compile('\\s+'), WhiteSpace, None),
	(re.compile('L?\'[^\']*\''), Literal, 'character'), # 2.13.2 [lex.ccon]
	(re.compile('L?"[^"]*"'), Literal, 'string'), # 2.13.4 [lex.string]
	(re.compile('(%s)\\b' % '|'.join(_keywords)), Keyword, None), # 2.11 [lex.key]
	(re.compile('[a-zA-Z_][a-zA-Z0-9_]*'), Identifier, None), # 2.10 [lex.name]
	(re.compile('[0-9]+\\.([0-9]+)?(e[\\+-]?[0-9]+)?[fFlL]?'), Literal, 'float'), # 2.13.3 [lex.fcon]
	(re.compile('[0-9]+e[\\+-]?[0-9]+[fFlL]?'), Literal, 'float'), # 2.13.3 [lex.fcon]
	(re.compile('0x[0-9a-fA-F]+%s?' % _integer_suffix), Literal, 'hexadecimal'), # 2.13.1 [lex.icon]
	(re.compile('0[0-7]*%s?'        % _integer_suffix), Literal, 'octal'), # 2.13.1 [lex.icon]
	(re.compile('[0-9]+%s?'         % _integer_suffix), Literal, 'decimal'), # 2.13.1 [lex.icon]
	(re.compile('\?\?[=/\'\(\)!<>\-]'), Operator, None), # 2.3 [lex.trigraph]
	# 2.12 [lex.operators]
	(re.compile('{|}'), Operator, None),
	(re.compile('\\[|\\]'), Operator, None),
	(re.compile('\\(|\\)'), Operator, None),
	(re.compile('<%|%>'), Operator, None),
	(re.compile('<:|:>'), Operator, None),
	(re.compile('<<=|<=|<<|<'), Operator, None),
	(re.compile('>>=|>=|>>|>'), Operator, None),
	(re.compile('##|#'), Operator, None),
	(re.compile('%:%:|%:'), Operator, None),
	(re.compile('::|:'), Operator, None),
	(re.compile('->\\*|->'), Operator, None),
	(re.compile('\\+=|\\+\\+|\\+'), Operator, None),
	(re.compile('-=|--|-'), Operator, None),
	(re.compile('\\.\\.\\.|\\.\\*|\\.'), Operator, None),
	(re.compile(';'), Operator, None),
	(re.compile('\\?'), Operator, None),
	(re.compile('\\*=|\\*'), Operator, None),
	(re.compile('/=|/'), Operator, None),
	(re.compile('%=|%'), Operator, None),
	(re.compile('\\^=|\\^'), Operator, None),
	(re.compile('&=|&&|&'), Operator, None),
	(re.compile('\\|=|\\|\\||\\|'), Operator, None),
	(re.compile('~'), Operator, None),
	(re.compile('!=|!'), Operator, None),
	(re.compile(','), Operator, None),
	(re.compile('==|='), Operator, None),
]


def match_token(text, pos):
	for matcher, token, kind in _tokens:
		m = matcher.match(text, pos)
		if m:
			return token(m.group(0), kind), m.end()
	return None, None


def tokenize(text):
	pos = 0
	while pos < len(text):
		token, end = match_token(text, pos)
		if not token:
			raise Exception('Invalid C++ token : %s' % text[pos:])
		pos = end
		yield token
