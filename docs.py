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

class documentationProcessor(markdown.treeprocessors.Treeprocessor):
	def __init__(self, items):
		self.items = items

	def run(self, root):
		ref = None
		for e in root:
			if e.tag == 'h1':
				if e.attrib.get('class', None) == 'doc':
					try:
						ref = self.items[e.text][0]
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
