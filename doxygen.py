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
import docs


_items = {}


class Item:
	def __init__(self, protection, kind, name):
		self.protection = protection if protection else 'public'
		self.kind = kind
		self.name = name.split('::')[-1]
		self.qname = name
		self.children = []
		self.docs = None

	def __repr__(self):
		return 'Item({0}, {1}, {2})'.format(self.protection, self.kind, self.name)


class Variable(Item):
	def __init__(self, protection, kind, name):
		Item.__init__(self, protection, kind, name)


class Function(Item):
	def __init__(self, protection, kind, name):
		Item.__init__(self, protection, kind, name)
		self.args = {}


class FunctionPointer(Function):
	def __init__(self, protection, kind, name):
		Function.__init__(self, protection, kind, name)


def signature(item):
	ret = []
	if isinstance(item, Variable) or isinstance(item, Function):
		if item.kind == 'typedef':
			ret.append(cpplex.Keyword(item.kind))
			ret.append(cpplex.WhiteSpace(' '))
		ret.extend(item.vartype)
	else:
		ret.append(cpplex.Keyword(item.kind))
	ret.append(cpplex.WhiteSpace(' '))
	if isinstance(item, FunctionPointer):
		ret.append(cpplex.Operator('('))
		ret.append(cpplex.Operator('*'))
	names = item.qname.split('::')
	for n in range(1, len(names)):
		scope = '::'.join(names[0:n])
		sref = _items[scope]
		ret.append(sref)
		ret.append(cpplex.Operator('::'))
	ret.extend(cpplex.tokenize(item.name))
	if isinstance(item, FunctionPointer):
		ret.append(cpplex.Operator(')'))
	if isinstance(item, Function):
		ret.append(cpplex.Operator('('))
		for i, arg in enumerate(item.args.values()):
			ret.extend(arg.vartype)
			ret.append(cpplex.WhiteSpace(' '))
			ret.append(cpplex.Identifier(arg.name))
			if i != len(item.args) - 1:
				ret.append(cpplex.Operator(','))
				ret.append(cpplex.WhiteSpace(' '))
		ret.append(cpplex.Operator(')'))
	return ret


class ItemRef:
	def __init__(self, ref):
		self.ref = ref
		self.item = None

	def __repr__(self):
		return 'ItemRef({0} => {1})'.format(self.ref, repr(self.item))

	@property
	def html(self):
		return '<a href="{0}.html">{1}</a>'.format(self.ref, self.item.name)


_item_refs = {}
def create_item_ref(ref):
	if ref in _item_refs.keys():
		return _item_refs[ref]
	ret = ItemRef(ref)
	_item_refs[ref] = ret
	return ret


def create_item(ref, protection, kind, name):
	if kind in ['variable', 'typedef']:
		ref.item = Variable(protection, kind, name)
	elif kind == 'function':
		ref.item = Function(protection, kind, name)
	else:
		ref.item = Item(protection, kind, name)
	_items[name] = ref


def is_function_pointer(vartype):
	if len(vartype) < 3:
		return False
	return vartype[-2].value == '(' and vartype[-1].value[-1] == '*'


def _parse_type_node(xml):
	ret = []
	for child in xml.children():
		if child.name == '#text':
			ret.extend(list(cpplex.tokenize(child.node.nodeValue)))
		elif child.name == 'ref':
			xref = create_item_ref(child['@refid'])
			ret.append(xref)
	return ret


def _parse_memberdef_node(xml, parent):
	ref = create_item_ref(xml['@id'])
	name = '::'.join([parent.item.qname, xml['name/text()']])
	if '<' in name and '>' in name: # template specialization
		name = name.split('<')[0]
	create_item(ref, xml['@prot'], xml['@kind'], name)
	parent.item.children.append(ref)
	argnum = 0
	for child in xml:
		if child.name == 'type':
			ref.item.vartype = _parse_type_node(child)
			if is_function_pointer(ref.item.vartype):
				item = ref.item
				ref.item = FunctionPointer(ref.item.protection, ref.item.kind, ref.item.name)
				ref.item.vartype = item.vartype[0:-2]
		elif child.name == 'param':
			argnum = argnum + 1
			pname = child['declname/text()']
			ptype = _parse_type_node(child['type'])
			if not pname:
				pname = '__arg{0}'.format(argnum)
			p = Variable('public', 'parameter', pname)
			p.vartype = ptype
			ref.item.args[pname] = p
		elif child.name == 'argsstring':
			args = _parse_type_node(child)
	if isinstance(ref.item, FunctionPointer) and len(ref.item.args) == 0 and len(args) != 0:
		# doxygen does not parse function pointer arguments into param items,
		# so we need to parse them here ...
		if not args[0].value == ')' or not args[1].value == '(' or not args[-1].value == ')':
			raise Exception('Invalid function pointer construct.')
		args = args[2:]
		param = []
		argnum = 0
		for token in args:
			if token.value == ',' or token.value == ')':
				argnum = argnum + 1
				if isinstance(param[-1], cpplex.Identifier) and len(param) > 1:
					pname = param[-1].value
					param = param[:-1]
				else:
					pname = '__arg{0}'.format(argnum)
				if isinstance(param[-1], cpplex.WhiteSpace):
					param = param[:-1]
				p = Variable('public', 'parameter', pname)
				p.vartype = param
				ref.item.args[pname] = p
				param = []
			elif len(param) == 0 and isinstance(token, cpplex.WhiteSpace):
				pass
			else:
				param.append(token)


def _parse_sectiondef_node(xml, parent):
	for child in xml:
		if child.name == 'memberdef':
			_parse_memberdef_node(child, parent)


def _parse_compounddef_node(xml):
	if xml['@kind'] in ['file', 'dir', 'page']:
		return None
	ref = create_item_ref(xml['@id'])
	for child in xml:
		if child.name == 'compoundname':
			create_item(ref, xml['@prot'], xml['@kind'], child['text()'])
		elif child.name == 'sectiondef':
			_parse_sectiondef_node(child, ref)
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
	def print_etree(e, f=sys.stdout, terminator='\n'):
		f.write('<{0}>'.format(e.tag))
		f.write('{0}'.format(e.text))
		for child in e:
			print_etree(child, f=f, terminator='')
		f.write('</{0}>{1}'.format(e.tag, terminator))


	def generate_html(f, ref):
		f.write('<div><code>')
		for token in signature(ref.item):
			f.write(token.html)
		f.write('</code></div>\n')
		if ref.item.docs:
			f.write('<blockquote class="docs">\n')
			print_etree(ref.item.docs.brief, f)
			for doc in ref.item.docs.detailed:
				print_etree(doc, f)
			f.write('</blockquote>\n')
		if len(ref.item.children) > 0:
			f.write('<blockquote>\n')
			for child in ref.item.children:
				generate_html(f, child)
			f.write('</blockquote>\n')

	items = []
	for filename in sys.argv[1:]:
		if filename.endswith('.xml'):
			item = parse_doxygen(filename)
			if item:
				items.append(item)
	for filename in sys.argv[1:]:
		if filename.endswith('.md'):
			docs.parse(filename, _items)

	rootdir = 'docs/api/html'
	if not os.path.exists(rootdir):
		os.mkdir(rootdir)

	for item in items:
		if not item.item or item.item.protection != 'public':
			continue

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
