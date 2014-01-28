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


class Identifier(Token):
	def __init__(self, value):
		Token.__init__(self, value)


class Keyword(Token):
	def __init__(self, value):
		Token.__init__(self, value)


class Operator(Token):
	def __init__(self, value):
		Token.__init__(self, value)


class Literal(Token):
	def __init__(self, value):
		Token.__init__(self, value)


class IntegerLiteral(Literal):
	def __init__(self, value):
		Literal.__init__(self, value)


class OctalLiteral(IntegerLiteral):
	def __init__(self, value):
		IntegerLiteral.__init__(self, value)


class DecimalLiteral(IntegerLiteral):
	def __init__(self, value):
		IntegerLiteral.__init__(self, value)


class HexadecimalLiteral(IntegerLiteral):
	def __init__(self, value):
		IntegerLiteral.__init__(self, value)


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
	(re.compile('\\s+'), WhiteSpace),
	(re.compile('(%s)\\b' % '|'.join(_keywords)), Keyword), # 2.11 [lex.key]
	(re.compile('[a-zA-Z_][a-zA-Z0-9_]*'), Identifier), # 2.10 [lex.name]
	(re.compile('0x[0-9a-fA-F]+%s?' % _integer_suffix), HexadecimalLiteral), # 2.13.1 [lex.icon]
	(re.compile('0[0-7]*%s?'        % _integer_suffix), OctalLiteral), # 2.13.1 [lex.icon]
	(re.compile('[0-9]+%s?'         % _integer_suffix), DecimalLiteral), # 2.13.1 [lex.icon]
	# 2.12 [lex.operators]
	(re.compile('{|}'), Operator),
	(re.compile('\\[|\\]'), Operator),
	(re.compile('\\(|\\)'), Operator),
	(re.compile('<%|%>'), Operator),
	(re.compile('<:|:>'), Operator),
	(re.compile('<<=|<=|<<|<'), Operator),
	(re.compile('>>=|>=|>>|>'), Operator),
	(re.compile('##|#'), Operator),
	(re.compile('%:%:|%:'), Operator),
	(re.compile('::|:'), Operator),
	(re.compile('->\\*|->'), Operator),
	(re.compile('\\+=|\\+\\+|\\+'), Operator),
	(re.compile('-=|--|-'), Operator),
	(re.compile('\\.\\.\\.|\\.\\*|\\.'), Operator),
	(re.compile(';'), Operator),
	(re.compile('\\?'), Operator),
	(re.compile('\\*=|\\*'), Operator),
	(re.compile('/=|/'), Operator),
	(re.compile('%=|%'), Operator),
	(re.compile('\\^=|\\^'), Operator),
	(re.compile('&=|&&|&'), Operator),
	(re.compile('\\|=|\\|\\||\\|'), Operator),
	(re.compile('~'), Operator),
	(re.compile('!=|!'), Operator),
	(re.compile(','), Operator),
	(re.compile('==|='), Operator),
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
	tokenizer_testcases = []
	for whitespace in [' ', '\t', '\r', '\n', '    ', ' \t\r\n']:
		tokenizer_testcases.append((whitespace, [WhiteSpace(whitespace)]))
	# 2.10 [lex.name]
	identifiers = [
		'lowercase', 'UPPERCASE', 'MixedCase',
		'_abc', 'ab_cd', '__T',
		'_123', 'a123', 'A123',
		'a', 'A', '_',
	]
	for ident in identifiers:
		tokenizer_testcases.append((ident, [Identifier(ident)]))
	# 2.11 [lex.key]
	for keyword in _keywords:
		tokenizer_testcases.append((keyword, [Keyword(keyword)]))
	# 2.12 [lex.operators]
	operators = [
		'{',  '}',  '[',  ']',  '#',  '##',   '(', ')',
		'<:', ':>', '<%', '%>', '%:', '%:%:', ';', ':', '...',
		'?',  '::', '.',  '.*',
		'+',  '-',  '*',  '/',  '%',  '^',   '&',   '|',   '~',
		'!',  '=',  '<',  '>',  '+=', '-=',  '*=',  '/=',  '%=',
		'^=', '&=', '|=', '<<', '>>', '>>=', '<<=', '==',  '!=',
		'<=', '>=', '&&', '||', '++', '--',  ',',   '->*', '->',
	]
	for op in operators:
		tokenizer_testcases.append((op, [Operator(op)]))
	# 2.13.1 [lex.icon]
	integer_suffix = ['',
		'u',  'ul',  'uL',  'ull', 'uLL', 'U', 'Ul', 'UL', 'Ull', 'ULL',
		'l',  'lu',  'lU',  'L',   'Lu',  'LU',
		'll', 'llu', 'llU', 'LL',  'LLu', 'LLU',
	]
	for value in ['0', '01234567']:
		for suffix in integer_suffix:
			tokenizer_testcases.append((value + suffix, [OctalLiteral(value + suffix)]))
	for value in ['1', '23']:
		for suffix in integer_suffix:
			tokenizer_testcases.append((value + suffix, [DecimalLiteral(value + suffix)]))
	for value in ['0x1', '0x123abc', '0xABC123']:
		for suffix in integer_suffix:
			tokenizer_testcases.append((value + suffix, [HexadecimalLiteral(value + suffix)]))

	passed = 0
	failed = 0
	for text, result in tokenizer_testcases:
		try:
			got = repr(list(tokenizer(text)))
		except:
			got = None
		expected = repr(result)
		if expected == got:
			passed = passed + 1
		else:
			print('test %s failed -- expected %s, got %s' % (repr(text), expected, got))
			failed = failed + 1
	print('passed : %d' % passed)
	print('failed : %d' % failed)
	print('total  : %d' % (passed + failed))
