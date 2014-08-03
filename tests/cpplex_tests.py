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

sys.path.append(os.path.join(sys.path[0], '..'))

import cpplex

passed = 0
failed = 0

def run(text, result):
	global passed
	global failed
	try:
		got = repr(list(cpplex.tokenize(text)))
	except Exception as e:
		got = repr(e)
	expected = repr(result)
	if expected == got:
		passed = passed + 1
	else:
		print('%s test %s failed -- expected %s, got %s' % (parser.__name__, repr(text), expected, got))
		failed = failed + 1

def summary():
	print('passed : %d' % passed)
	print('failed : %d' % failed)
	print('total  : %d' % (passed + failed))

for whitespace in [' ', '\t', '\r', '\n', '    ', ' \t\r\n']:
	run(whitespace, [cpplex.WhiteSpace(whitespace, None)])

# 2.3 [lex.trigraph]
operators = [
	'??=', '??/', '??\'', '??(', '??)', '??!', '??<', '??>', '??-',
]
for op in operators:
	run(op, [cpplex.Operator(op, None)])

# 2.10 [lex.name]
identifiers = [
	'lowercase', 'UPPERCASE', 'MixedCase',
	'_abc', 'ab_cd', '__T',
	'_123', 'a123', 'A123',
	'a', 'A', '_',
]
for ident in identifiers:
	run(ident, [cpplex.Identifier(ident, None)])

# 2.11 [lex.key]
for keyword in cpplex._keywords:
	run(keyword, [cpplex.Keyword(keyword, None)])

# 2.12 [lex.operators]
operators = [
	'{',  '}',  '[',  ']',  '#',  '##', '(', ')', '...',
	';',  ':',  '?',  '::', '.',  '.*',
	'+',  '-',  '*',  '/',  '%',  '^',   '&',   '|',   '~',
	'!',  '=',  '<',  '>',  '+=', '-=',  '*=',  '/=',  '%=',
	'^=', '&=', '|=', '<<', '>>', '>>=', '<<=', '==',  '!=',
	'<=', '>=', '&&', '||', '++', '--',  ',',   '->*', '->',
	# alternative tokens
	'<:', ':>', '<%', '%>', '%:', '%:%:',
]
for op in operators:
	run(op, [cpplex.Operator(op, None)])

# 2.13.1 [lex.icon]
integer_suffix = ['',
	'u',  'ul',  'uL',  'ull', 'uLL', 'U', 'Ul', 'UL', 'Ull', 'ULL',
	'l',  'lu',  'lU',  'L',   'Lu',  'LU',
	'll', 'llu', 'llU', 'LL',  'LLu', 'LLU',
]
for value in ['0', '01234567']:
	for suffix in integer_suffix:
		run(value + suffix, [cpplex.Literal(value + suffix, 'octal')])
for value in ['1', '23']:
	for suffix in integer_suffix:
		run(value + suffix, [cpplex.Literal(value + suffix, 'decimal')])
for value in ['0x1', '0x123abc', '0xABC123']:
	for suffix in integer_suffix:
		run(value + suffix, [cpplex.Literal(value + suffix, 'hexadecimal')])

# 2.13.2 [lex.ccon]
characters = ["'a'", "'\\0'", "L'a'", "L'\\0'"]
for c in characters:
	run(c, [cpplex.Literal(c, 'character')])

# 2.13.3 [lex.fcon]
float_suffix = ['', 'f', 'F', 'l', 'L']
fcon = [
	'1.2',     '12.23',     '2.',
	'1.2e99',  '12.23e47',  '2.e33',  '6e5',
	'1.2e+99', '12.23e+47', '2.e+33', '6e+5',
	'1.2e-99', '12.23e-47', '2.e-33', '6e-5',
]
for f in fcon:
	for suffix in float_suffix:
		run(f + suffix, [cpplex.Literal(f + suffix, 'float')])

# 2.13.4 [lex.string]
strings = ['""', '"abc"', 'L""', 'L"abc"']
for s in strings:
	run(s, [cpplex.Literal(s, 'string')])

summary()
