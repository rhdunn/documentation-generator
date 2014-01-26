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
	value = create_item(xml['id'], xml['prot'])
	for child in xml:
		if child.name == 'name':
			value.signature = child.text()
	return value


def _parse_memberdef_node(xml, item):
	member = create_item(xml['id'], xml['prot'])
	vartype = None
	varname = None
	args = None
	for child in xml:
		if child.name == 'type':
			vartype = child.text()
		elif child.name == 'name':
			varname = child.text()
		elif child.name == 'argsstring':
			args = child.text()
		elif child.name == 'enumvalue':
			member.add(_parse_enumvalue_node(child))
	if xml['kind'] in ['enum']:
		member.signature = '%s %s' % (xml['kind'], varname)
	elif args:
		if vartype:
			if xml['kind'] in ['typedef']:
				member.signature = '%s %s %s%s' % (xml['kind'], vartype, varname, args)
			else:
				member.signature = '%s %s%s' % (vartype, varname, args)
		else: # constructor/destructor
			member.signature = '%s%s' % (varname, args)
	elif xml['kind'] in ['typedef']:
		member.signature = '%s %s %s' % (xml['kind'], vartype, varname)
	else:
		member.signature = '%s %s' % (vartype, varname)
	return member


def _parse_sectiondef_node(xml, item):
	for child in xml:
		if child.name == 'memberdef':
			item.add(_parse_memberdef_node(child, item))


def _parse_compounddef_node(xml):
	if xml['kind'] in ['file', 'dir', 'page']:
		return None
	item = create_item(xml['id'], xml['prot'])
	for child in xml:
		if child.name == 'compoundname':
			item.signature = '%s %s' % (xml['kind'], child.text())
		elif child.name == 'sectiondef':
			_parse_sectiondef_node(child, item)
		elif child.name in ['innerclass', 'innernamespace']:
			member = create_item(child['refid'], child['prot'])
			if not member.signature:
				name = child.text().split('::')[-1]
				if member.ref.startswith('class'):
					member.signature = 'class %s' % name
				elif member.ref.startswith('namespace'):
					member.signature = 'namespace %s' % name
				elif member.ref.startswith('struct'):
					member.signature = 'struct %s' % name
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
	def print_item(f, item, level=0):
		if not item:
			return
		f.write('%s%s [%s|%s]\n' % (('... '*level), item.signature, item.scope, item.ref))
		for child in item.items:
			print_item(f, child, level+1)

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
			f.write('<pre>\n')
			print_item(f, item)
			f.write('</pre>\n')
