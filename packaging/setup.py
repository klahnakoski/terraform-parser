# encoding: utf-8
# THIS FILE IS AUTOGENERATED!
from __future__ import unicode_literals
from setuptools import setup
setup(
    author='Kyle Lahnakoski',
    author_email='kyle@lahnakoski.com',
    classifiers=["Development Status :: 2 - Pre-Alpha","Topic :: Software Development :: Libraries","Topic :: Software Development :: Libraries :: Python Modules","License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)","Programming Language :: Python :: 3.7","Programming Language :: Python :: 3.8","Programming Language :: Python :: 3.9","Programming Language :: Python :: 3.10"],
    description='Terraform Parser - Parse Terraform to JSON',
    extras_require={"tests":["mo-testing","mo-files","mo-streams"]},
    include_package_data=True,
    install_requires=["diagrams","mo-dots==9.356.23062","mo-imports==7.341.23006","mo-parsing==8.356.23062","mo-streams==1.358.23070"],
    license='MPL 2.0',
    long_description='# terraform-parser\n\n[![PyPI Latest Release](https://img.shields.io/pypi/v/terraform-parser.svg)](https://pypi.org/project/terraform-parser/)\n[![Build Status](https://app.travis-ci.com/klahnakoski/terraform-parser.svg?branch=master)](https://travis-ci.com/github/klahnakoski/terraform-parser)\n [![Coverage Status](https://coveralls.io/repos/github/klahnakoski/terraform-parser/badge.svg?branch=dev)](https://coveralls.io/github/klahnakoski/terraform-parser?branch=dev)\n[![Downloads](https://pepy.tech/badge/terraform-parser/month)](https://pepy.tech/project/terraform-parser)\n\n\nParse Terraform scripts into JSON\n\n\n## Status\n\n**Dec 2022** - This an experimental parser that can parse HCL2\n\n## Problem\n\nI am uncertain if configuration/template language, such as Terraform, should include scripting.  It is beneficial to have a simple configuration, albeit redundant, for VCS tracking and simple diff for merge reviews.  \n\nI would advocate a high level langauge (HLL), like Python, be used to produce the Terraform configuration with both HLL and Terraform be included in the repository. HLL is familiar, and the Terraform changes are easy to review.\n\nUsing an HLL for Terraform generation removes the need for the [quirky template expressions](https://github.com/hashicorp/hcl/blob/main/hclsyntax/spec.md#template-expressions), complex expressions, and modules. \n\nThe hope is to \n\n* parse terraform into Json data\n* merge data from different terraform to single spec\n* allow Python to modify data easily\n* write out terraform (in diff-friendly way)\n\n\n## References\n\n* Look at what is done here - https://github.com/starhawking/python-terrascript\n* Existing parser for [HCL1](https://github.com/virtuald/pyhcl)\n* Existing parser for [HCL2](https://pypi.org/project/python-hcl2/)\n* Unicode Identifiers - [UAX31](http://unicode.org/reports/tr31/)\n* [Terraform Spec](https://github.com/hashicorp/hcl/blob/main/hclsyntax/spec.md)\n* [Diagram terraform](https://diagrams.mingrammer.com/docs/getting-started/installation\n* [Graphviz](https://www.graphviz.org/)\n\n\n\n',
    long_description_content_type='text/markdown',
    name='terraform-parser',
    packages=["terraform_parser"],
    url='https://github.com/klahnakoski/terraform-parser',
    version='0.358.23070',
    zip_safe=False
)