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
import cpplex


class Item:
	def __init__(self, protection, kind, name):
		self.protection = protection
		self.kind = kind
		self.name = name

	def __repr__(self):
		return 'Item({0}, {1}, {2})'.format(self.protection, self.kind, self.name)


class ItemRef:
	def __init__(self, ref):
		self.ref = ref
		self.item = None

	def __repr__(self):
		return 'ItemRef({0} => {1})'.format(self.ref, repr(self.item))


_item_refs = {}
def create_item_ref(ref):
	if ref in _item_refs.keys():
		return _item_refs[ref]
	ret = ItemRef(ref)
	_item_refs[ref] = ret
	return ret


def _parse_compounddef_node(xml):
	if xml['@kind'] in ['file', 'dir', 'page']:
		return None
	ref = create_item_ref(xml['@id'])
	for child in xml:
		if child.name == 'compoundname':
			ref.item = Item(xml['@prot'], xml['@kind'], child['text()'])
	return ref


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

	def generate_html(f, ref):
		if not ref.item or ref.item.protection != 'public':
			return
		f.write('<div><code>{0}</code></div>'.format(repr(item)))
		f.write('<hr>\n')

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
