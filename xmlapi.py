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

from xml.dom import minidom


class NodeSelector:
	def __init__(self, name):
		self.typename = 'node'
		self.name = name

	def __repr__(self):
		return 'Node(%s)' % self.name

	def select(self, item):
		for node in item.children():
			if node.name == self.name:
				yield node


class AttributeSelector:
	def __init__(self, name):
		self.typename = 'attribute'
		self.name = name

	def __repr__(self):
		return 'Attr(%s)' % self.name

	def select(self, item):
		if item.node.attributes:
			ret = item.node.attributes.get(self.name, None)
			if ret:
				yield ret.value


class TextSelector:
	def __init__(self):
		self.typename = 'text()'

	def __repr__(self):
		return 'text()'

	def select(self, item):
		yield ''.join(self._text(item.node))

	def _text(self, node):
		ret = []
		for child in node.childNodes:
			if child.nodeType == child.TEXT_NODE:
				ret.append(child.nodeValue)
			elif child.nodeType == child.ELEMENT_NODE:
				ret.extend(self._text(child))
		return ret


class EqualsSelector:
	def __init__(self, selector, value):
		self.typename = 'equals'
		self.selector = selector
		self.value = value

	def __repr__(self):
		return 'Equals(%s,%s)' % (self.selector, self.value)

	def select(self, item):
		for value in self.selector.select(item):
			if value == self.value:
				yield value


class IfSelector:
	def __init__(self, node, selector):
		self.typename = 'when'
		self.node = node
		self.selector = selector

	def __repr__(self):
		return '%s.If(%s)' % (self.node, self.selector)

	def select(self, item):
		for node in self.node.select(item):
			for value in self.selector.select(node):
				yield node


class ChildSelector:
	def __init__(self, node, selector):
		self.typename = 'child'
		self.node = node
		self.selector = selector

	def __repr__(self):
		return '%s.Select(%s)' % (self.node, self.selector)

	def select(self, item):
		for node in self.node.select(item):
			for match in self.selector.select(node):
				yield match


_tokens = [
	(re.compile(r'text\(\)'), 'text()'),
	(re.compile(r'[a-zA-Z0-9\_]+'), 'name'),
	(re.compile(r'"[^"]*"'), 'string'),
	(re.compile(r'\['), '['),
	(re.compile(r'\]'), ']'),
	(re.compile(r'@'), '@'),
	(re.compile(r'='), '='),
	(re.compile(r'/'), '/'),
]


def match_token(text, pos):
	for matcher, token in _tokens:
		m = matcher.match(text, pos)
		if m:
			return token, m.group(0), m.end()
	return None, None, None


def tokenizer(selector):
	pos = 0
	while pos < len(selector):
		token, value, end = match_token(selector, pos)
		if not token:
			raise Exception('Invalid selector token : %s' % selector[pos:])
		pos = end
		yield token, value


def parse_selector(selector):
	stack = []
	for token, value in tokenizer(selector):
		if token == 'name':
			try:
				top, _ = stack[-1]
			except IndexError:
				top = None
			if top == '@':
				stack = stack[:-1]
				stack.append(('selector', AttributeSelector(value)))
			else:
				stack.append(('selector', NodeSelector(value)))
		elif token == 'string':
			a, _ = stack[-1]
			_, b = stack[-2]
			if a == '=' and b.typename == 'attribute':
				stack = stack[:-2]
				stack.append(('selector', EqualsSelector(b, value[1:-1])))
			else:
				raise Exception('XPath: invalid syntax for - %s' % selector)
		elif token == ']':
			_, a = stack[-1]
			b, _ = stack[-2]
			_, c = stack[-3]
			if b != '[':
				raise Exception('XPath: invalid syntax for - %s' % selector)
			stack = stack[:-3]
			stack.append(('selector', IfSelector(c, a)))
		elif token == 'text()':
			stack.append(('selector', TextSelector()))
		else:
			stack.append((token, value))
	while len(stack) > 1:
		_, a = stack[-1]
		b, _ = stack[-2]
		_, c = stack[-3]
		if b != '/':
			raise Exception('XPath: invalid syntax for - %s' % selector)
		stack = stack[:-3]
		stack.append(('selector', ChildSelector(c, a)))
	return stack[0][1]


class XmlNode:
	def __init__(self, node):
		self.node = node
		self.name = node.nodeName

	def __iter__(self):
		for child in self.node.childNodes:
			if child.nodeType == child.ELEMENT_NODE:
				yield XmlNode(child)

	def __getitem__(self, xpath):
		for item in self.select(xpath):
			return item
		return None

	def children(self):
		for child in self.node.childNodes:
			yield XmlNode(child)

	def select(self, xpath):
		return parse_selector(xpath).select(self)


class XmlDocument(XmlNode):
	def __init__(self, filename):
		XmlNode.__init__(self, minidom.parse(filename).documentElement)
