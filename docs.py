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
import re
import sys
import codecs
import markdown

class Documentation:
	def __init__(self):
		self.brief = None
		self.detailed = []

class cldocPreProcessor(markdown.preprocessors.Preprocessor):
	inline_code = re.compile(r'(`[^`]*`)')
	crossref = re.compile(r'(<[^>]*>)')

	def run(self, lines):
		ret = []
		for line in lines:
			# Convert cldoc headers to docdown type documentation format ...
			if '<cldoc:' in line:
				ret.append(line.replace('<cldoc:', '').replace('>', ' {: .doc }'))
				continue
			# Ignore code blocks ....
			if line.startswith('    ') or line.startswith('\t'):
				ret.append(line)
				continue
			# Convert cldoc cross-reference links to docdown format ...
			parts = []
			for i, text in enumerate(self.inline_code.split(line)):
				if i%2 == 0:
					for j, ref in enumerate(self.crossref.split(text)):
						if j%2 == 0:
							parts.append(ref)
						else:
							ref = ref[1:-1]
							parts.append('[](^^{0})'.format(ref))
				else:
					parts.append(text)
			if len(parts) > 1:
				line = ''.join(parts)
			# Convert cldoc parameter/return type documentation to docdown format ...
			if line.startswith('@') and ' ' in line:
				ret.append('')
				words = line.split()
				ret.append(words[0])
				ret.append(': {0}'.format(' '.join(words[1:])))
				continue
			# Anything else ...
			ret.append(line)
		return ret


def equivalent(list1, list2):
	if len(list1) != len(list2):
		return False
	for i in range(0, len(list1)):
		if list1[i] != list2[i]:
			return False
	return True


class documentationProcessor(markdown.treeprocessors.Treeprocessor):
	def __init__(self, items):
		self.items = items
		self.clear()

	def clear(self):
		self.refs = None
		self.doc = None
		self.param_doc = {}

	def process_documentation(self):
		matching = []
		if len(self.refs) == 1:
			matching.append(self.refs[0].item)
		else:
			docargs = sorted([x for x in self.param_doc.keys() if x != 'return'])
			matching = []
			for ref in self.refs:
				args = sorted(ref.item.args.keys())
				if equivalent(docargs, args):
					matching.append(ref.item)

		if len(matching) == 0:
			docargs = sorted([x for x in self.param_doc.keys() if x != 'return'])
			sys.stderr.write('error: no matching {0} type found for the given parameters: {1}\n'.format(self.refs[0].item.qname, ', '.join(docargs)))
		for i, item in enumerate(matching):
			if i == 1:
				sys.stdout.write('info: multiple matching {0} type found for the given parameters: {1}\n'.format(self.refs[0].item.qname, ', '.join(docargs)))
			item.docs = self.doc
			for argname, doc in self.param_doc.items():
				if argname == 'return':
					item.retdoc = doc
					continue
				try:
					item.args[argname].docs = doc
				except KeyError:
					sys.stdout.write('error: parameter {0} does not exist on {1}\n'.format(argname, item.qname))

	def run(self, root):
		for e in root:
			if e.tag == 'h1':
				if e.attrib.get('class', None) == 'doc':
					if self.refs:
						self.process_documentation()
					try:
						self.refs = self.items[e.text]
						self.doc = Documentation()
						self.param_doc = {}
					except KeyError:
						sys.stderr.write('error: item {0} not found\n'.format(e.text))
						self.clear()
				else:
					self.clear()
			elif e.tag == 'dl':
				argname = None
				argdoc = None
				remove = []
				for defn in e:
					if defn.tag == 'dt':
						if defn.text.startswith('@'):
							argname = defn.text.replace('@', '')
							argdoc = Documentation()
							remove.append(defn)
					elif argname != None:
						# The dd node is the container of the documentation ...
						defn.tag = 'p'
						argdoc.brief = defn
						self.param_doc[argname] = argdoc
						remove.append(defn)
						argname = None
						argdoc = None
				for item in remove:
					e.remove(item)
			elif self.doc:
				if self.doc.brief != None:
					self.doc.detailed.append(e)
				else:
					self.doc.brief = e

class Extension(markdown.extensions.Extension):
	def __init__(self, items):
		self.items = items

	def extendMarkdown(self, md, md_globals):
		md.preprocessors.add('cldoc', cldocPreProcessor(), '_end')
		md.treeprocessors.add('docs', documentationProcessor(self.items), '_end')

def parse(filename, items):
	with codecs.open(filename, 'r', encoding='utf-8') as f:
		html = markdown.markdown(f.read(), extensions=['extra', Extension(items)])
