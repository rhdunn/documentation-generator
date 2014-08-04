# Documentation Generator

- [Usage](#usage)
- [Markdown Support](#markdown-support)
  - [cldoc-flavoured Markdown](#cldoc-flavoured-markdown)
  - [Docdown](#docdown)
    - [Type Documentation](#type-documentation)
    - [Parameter and Return Type Documentation](#parameter-and-return-type-documentation)
    - [Cross References](#cross-references)
- [Bugs](#bugs)
- [License Information](#license-information)

----------

The documentation generator project is designed to support documenting C++
projects (including C++11 projects) using markdown.

It uses doxygen to parse the C++ code (processing the XML files that doxygen
generates), but reads the documentation from markdown files. The rationale for
this is:

1.  It is easier to write documentation in markdown format.

2.  The markdown documentation can be viewed standalone from the generated
    documentation.

3.  Doxygen bugs in building the documentation (either HTML or XML) are avoided.

4.  Better error/warning reporting for undocumented and mismatched items and
    parameters.

5.  Better tooling, e.g. generating template documentation for the code.

## Usage

First, run `doxygen` to generate the xml files:

    doxygen ${PATH_TO_DOXYGEN_CONFIG_FILE}

Then run `doxygen.py` on the generated xml files and the markdown documentation:

    ${PATH_TO_DOCUMENTATION_GENERATOR}/doxygen.py docs/api/xml/*.xml docs/api/src/*.md

Then browse the generated html files:

    firefox docs/api/html

## Markdown Support

The documentation-generator tools support
[standard markdown](http://daringfireball.net/projects/markdown/syntax), along
with the following extensions:

1.  [Markdown inside HTML blocks](https://pythonhosted.org/Markdown/extensions/extra.html#markdown-inside-html-blocks)
2.  [Abbreviations](https://pythonhosted.org/Markdown/extensions/abbreviations.html#syntax)
3.  [Attribute Lists](https://pythonhosted.org/Markdown/extensions/attr_list.html#syntax)
4.  [Definition Lists](https://pythonhosted.org/Markdown/extensions/definition_lists.html#syntax)
5.  [Fenced Code Blocks](https://pythonhosted.org/Markdown/extensions/fenced_code_blocks.html#syntax)
6.  [Footnotes](https://pythonhosted.org/Markdown/extensions/footnotes.html#syntax)
7.  [Tables](https://pythonhosted.org/Markdown/extensions/tables.html#syntax)
8.  [Smart Strong](https://pythonhosted.org/Markdown/extensions/smart_strong.html#summary)

The support for this markdown processing is provided by the
[Python Markdown](https://pythonhosted.org/Markdown/) processor.

### cldoc-flavoured Markdown

The documentation-generator tools support using
[cldoc](https://github.com/jessevdk/cldoc)-flavoured markdown. That is,
documentation of the form:

	#<cldoc:fully_qualified_name>

	Brief documentation
	@param1 Parameter 1 documentation
	@param2 Parameter 2 documentation

	This is the detailed documentation

	@return The return value documentation

In addition to this, it also supports the cldoc cross-references of the form:
`<name>`.

The support differs from cldoc in several ways:

1.  the cross-references have to be fully qualified;

2.  additional markdown headers can appear in the markdown file, but these will
    not be picked up as part of the documentation;

3.  detailed documentation can appear after a `@return` statement.

### Docdown

Docdown is a custom markdown format used by the documentation-generator tools
to support writing API documentation. This is similar to cldoc-flavoured
markdown, but is intended to work nicely with existing markdown processors like
kramdown.

#### Type Documentation

To document a type, you need to specify the fully-qualified name of that type
as a markdown section header with a `doc` class, i.e.:

	# fully-qualified-name {: .doc }

	Brief documentation

	Detailed documentation

### Parameter and Return Type Documentation

To document parameters and return types of functions and methods, you need to
use a definition list with the entry being `@parameter_name` for parameters or
`@return` for the return type. For example:

	@param1
	: Parameter 1 documentation

	@param2
	: Parameter 2 documentation

	@return
	: The return type documentation

These can occur anywhere in the detailed documentation section of a
[Type Documentation](#type-documentation) block.

### Cross References

A cross-reference is a markdown link with a href section of the form
`^^fully-qualified-name`. If the link text is empty, the type name is used,
otherwise the specified text is used. For example:

	[](^^test::a)
	[thing](^^other_thing)

## Bugs

Report bugs to the
[documentation-generator issues](https://github.com/rhdunn/documentation-generator/issues)
page on GitHub.

## License Information

Documentation Generator is released under the GPL version 3 or later license.
