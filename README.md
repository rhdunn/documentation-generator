# Documentation Generator

- [Usage](#usage)
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

4.  Signatures for the items being documented are normalized, avoiding
    mismatches due to spacing or namespace scope issues.

5.  Better error/warning reporting for undocumented and mismatched items and
    parameters.

6.  Better tooling, e.g. generating template documentation for the code.

## Usage

First, run `doxygen` to generate the xml files:

    doxygen ${PATH_TO_DOXYGEN_CONFIG_FILE}

Then run `doxygen.py` on the generated xml files and the markdown documentation:

    ${PATH_TO_DOCUMENTATION_GENERATOR}/doxygen.py docs/api/xml/*.xml docs/api/src/*.md

Then browse the generated html files:

    firefox docs/api/html

## Bugs

Report bugs to the
[documentation-generator issues](https://github.com/rhdunn/documentation-generator/issues)
page on GitHub.

## License Information

Documentation Generator is released under the GPL version 3 or later license.
