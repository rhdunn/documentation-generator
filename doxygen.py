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

import xmlapi
import cpp


class Item:
	def __init__(self, ref, scope):
		self.ref = ref
		if scope:
			self.scope = scope
		else:
			self.scope = 'public'
		self.signature = None
		self.items = []

	def add(self, item):
		self.items.append(item)


_items = {}
def create_item(ref, scope):
	if ref in _items.keys():
		return _items[ref]
	ret = Item(ref, scope)
	_items[ref] = ret
	return ret


def _parse_enumvalue_node(xml):
	value = create_item(xml['@id'], xml['@prot'])
	for child in xml:
		if child.name == 'name':
			value.signature = cpp.parse(child['text()'])
	return value


def _parse_memberdef_node(xml, item):
	member = create_item(xml['@id'], xml['@prot'])
	vartype = None
	varname = None
	args = None
	for child in xml:
		if child.name == 'type':
			vartype = child['text()']
		elif child.name == 'name':
			varname = child['text()']
		elif child.name == 'argsstring':
			args = child['text()']
		elif child.name == 'enumvalue':
			member.add(_parse_enumvalue_node(child))
	if xml['@kind'] in ['enum']:
		member.signature = cpp.parse('%s %s' % (xml['@kind'], varname))
	elif args:
		if vartype:
			if xml['@kind'] in ['@typedef']:
				member.signature = cpp.parse('%s %s %s%s' % (xml['@kind'], vartype, varname, args))
			else:
				member.signature = cpp.parse('%s %s%s' % (vartype, varname, args))
		else: # constructor/destructor
			member.signature = cpp.parse('%s%s' % (varname, args))
	elif xml['@kind'] in ['typedef']:
		member.signature = cpp.parse('%s %s %s' % (xml['@kind'], vartype, varname))
	else:
		member.signature = cpp.parse('%s %s' % (vartype, varname))
	return member


def _parse_sectiondef_node(xml, item):
	for child in xml:
		if child.name == 'memberdef':
			item.add(_parse_memberdef_node(child, item))


def _parse_compounddef_node(xml):
	if xml['@kind'] in ['file', 'dir', 'page']:
		return None
	item = create_item(xml['@id'], xml['@prot'])
	for child in xml:
		if child.name == 'compoundname':
			item.signature = cpp.parse('%s %s' % (xml['@kind'], child['text()']))
		elif child.name == 'sectiondef':
			_parse_sectiondef_node(child, item)
		elif child.name in ['innerclass', 'innernamespace']:
			member = create_item(child['@refid'], child['@prot'])
			if not member.signature:
				name = child['text()'].split('::')[-1]
				if member.ref.startswith('class'):
					member.signature = cpp.parse('class %s' % name)
				elif member.ref.startswith('namespace'):
					member.signature = cpp.parse('namespace %s' % name)
				elif member.ref.startswith('struct'):
					member.signature = cpp.parse('struct %s' % name)
				else:
					raise Exception('Unknown innerclass/innernamespace referenced kind.')
			item.add(member)
	return item


def parse_doxygen(filename):
	xml = xmlapi.XmlDocument(filename)
	item = None
	for child in xml:
		if child.name == 'compounddef':
			if item:
				raise Exception('Multiple compounddef nodes found.')
			item = _parse_compounddef_node(child)
	return item


if __name__ == '__main__':
	def generate_html_cpp_tokens(f, tokens):
		for token in tokens:
			name = token.__class__.__name__
			if name == 'WhiteSpace':
				f.write(token.value)
			elif name == 'Identifier':
				f.write('<span class="identifier">%s</span>' % token.value)
			elif name == 'Keyword':
				f.write('<span class="keyword">%s</span>' % token.value)
			elif name == 'Operator':
				f.write('<span class="operator">%s</span>' % token.value)
			elif name == 'Literal':
				f.write('<span class="literal">%s</span>' % token.value)

	def generate_html(f, item):
		if not item or item.scope != 'public':
			return
		f.write('<div><code>')
		generate_html_cpp_tokens(f, item.signature)
		f.write('</code></div>\n')
		f.write('<blockquote>\n')
		for child in item.items:
			generate_html(f, child)
		f.write('</blockquote>\n')

	items = []
	for filename in sys.argv[1:]:
		item = parse_doxygen(filename)
		if item:
			items.append(item)

	rootdir = 'docs/api/html'
	if not os.path.exists(rootdir):
		os.mkdir(rootdir)

	for item in items:
		with open(os.path.join(rootdir, '%s.html' % item.ref), 'w') as f:
			f.write('<!DOCTYPE html>\n')
			f.write('<style type="text/css">\n')
			f.write('    blockquote { margin-top: 0; margin-bottom: 0; }\n')
			f.write('    .identifier { font-weight: normal; color: maroon; }\n')
			f.write('    .keyword    { font-weight: bold;   color: green; }\n')
			f.write('    .operator   { font-weight: normal; color: black; }\n')
			f.write('    .literal    { font-weight: normal; color: magenta; }\n')
			f.write('</style>\n')
			generate_html(f, item)
