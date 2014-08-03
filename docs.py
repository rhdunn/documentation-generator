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
		for i, line in enumerate(lines):
			# Convert cldoc headers to attr_list markdown format ...
			if '<cldoc:' in line:
				lines[i] = line.replace('<cldoc:', '').replace('>', ' {: .doc }')
				continue
			# Ignore code blocks ....
			if line.startswith('    ') or line.startswith('\t'):
				continue
			# Fixup cldoc cross-reference links ...
			parts = []
			for j, text in enumerate(self.inline_code.split(line)):
				if j%2 == 0:
					for k, ref in enumerate(self.crossref.split(text)):
						if k%2 == 0:
							parts.append(ref)
						else:
							ref = ref[1:-1]
							parts.append('[](^^{0}){{: .crossref }}'.format(ref))
				else:
					parts.append(text)
			if len(parts) > 1:
				lines[i] = ''.join(parts)
				continue
		return lines

class documentationProcessor(markdown.treeprocessors.Treeprocessor):
	def __init__(self, items):
		self.items = items

	def run(self, root):
		ref = None
		for e in root:
			if e.tag == 'h1':
				if e.attrib.get('class', None) == 'doc':
					try:
						ref = self.items[e.text]
						ref.item.docs = Documentation()
					except KeyError:
						sys.stderr.write('error: item {0} not found\n'.format(e.text))
						ref = None
				else:
					ref = None
			elif ref:
				if ref.item.docs.brief != None:
					ref.item.docs.detailed.append(e)
				else:
					ref.item.docs.brief = e

class Extension(markdown.extensions.Extension):
	def __init__(self, items):
		self.items = items

	def extendMarkdown(self, md, md_globals):
		md.preprocessors.add('cldoc', cldocPreProcessor(), '_end')
		md.treeprocessors.add('docs', documentationProcessor(self.items), '_end')

def parse(filename, items):
	with codecs.open(filename, 'r', encoding='utf-8') as f:
		html = markdown.markdown(f.read(), extensions=['extra', Extension(items)])
