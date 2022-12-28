# encoding: utf-8
# THIS FILE IS AUTOGENERATED!
from __future__ import unicode_literals
from setuptools import setup
setup(
    author='Kyle Lahnakoski',
    author_email='kyle@lahnakoski.com',
    classifiers=["Development Status :: 2 - Pre-Alpha","Topic :: Software Development :: Libraries","Topic :: Software Development :: Libraries :: Python Modules","License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)","Programming Language :: Python :: 3.7","Programming Language :: Python :: 3.8","Programming Language :: Python :: 3.9"],
    description='Terraform Parser - Parse Terraform to JSON',
    extras_require={"tests":["mo-testing"]},
    include_package_data=True,
    install_requires=["mo-dots==9.300.22349","mo-imports==7.298.22349","mo-parsing==8.309.22362"],
    license='MPL 2.0',
    long_description='# terraform-parser\n\nParse Terraform scripts into JSON\n\n## Status\n\n**Dec 2022** - This an experimental parser that can parse the\n\n## Problem\n\nAn application (or docker image, or lambda) is a black box to infrastructure: Services defined in infrastructure are communicated to the application as a set of environment variables.\n\nWe want to define services independently, in terraform, and then merge many services into a single infrastructure specification.  Specifically, we want to \n\n* avoiding terraform namespace collision\n* merge the vars and other resources \n* merge the application environment variables  \n\n## Solution\n\nThe hope is to \n\n* parse terraform into Json data\n* merge data from different terraform to single spec\n* allow Python to modify data easily\n* write out terraform (in diff-friendly way)\n\n## References\n\n* Look at what is done here - https://github.com/starhawking/python-terrascript\n* Parser for [HCL1](https://github.com/virtuald/pyhcl)\n* parser for [HCL2](https://pypi.org/project/python-hcl2/)\n* Unicode Identifiers - [UAX31](http://unicode.org/reports/tr31/)\n* [Terraform Spec](https://github.com/hashicorp/hcl/blob/main/hclsyntax/spec.md)\n\n\n\n',
    long_description_content_type='text/markdown',
    name='terraform-parser',
    packages=["terraform_parser"],
    url='https://github.com/klahnakoski/terraform-parser',
    version='9.309.22362',
    zip_safe=False
)