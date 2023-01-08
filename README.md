# terraform-parser

[![PyPI Latest Release](https://img.shields.io/pypi/v/terraform-parser.svg)](https://pypi.org/project/terraform-parser/)
[![Build Status](https://app.travis-ci.com/klahnakoski/terraform-parser.svg?branch=master)](https://travis-ci.com/github/klahnakoski/terraform-parser)
 [![Coverage Status](https://coveralls.io/repos/github/klahnakoski/terraform-parser/badge.svg?branch=dev)](https://coveralls.io/github/klahnakoski/terraform-parser?branch=dev)
[![Downloads](https://pepy.tech/badge/terraform-parser/month)](https://pepy.tech/project/terraform-parser)


Parse Terraform scripts into JSON


## Status

**Dec 2022** - This an experimental parser that can parse HCL2

## Problem

I am uncertain if configuration/template language, such as Terraform, should include scripting.  It is beneficial to have a simple configuration, albeit redundant, for VCS tracking and simple diff for merge reviews.  

I would advocate a high level langauge (HLL), like Python, be used to produce the Terraform configuration with both HLL and Terraform be included in the repository. HLL is familiar, and the Terraform changes are easy to review.

Using an HLL for Terraform generation removes the need for the [quirky template expressions](https://github.com/hashicorp/hcl/blob/main/hclsyntax/spec.md#template-expressions), complex expressions, and modules. 

The hope is to 

* parse terraform into Json data
* merge data from different terraform to single spec
* allow Python to modify data easily
* write out terraform (in diff-friendly way)


## References

* Look at what is done here - https://github.com/starhawking/python-terrascript
* Existing parser for [HCL1](https://github.com/virtuald/pyhcl)
* Existing parser for [HCL2](https://pypi.org/project/python-hcl2/)
* Unicode Identifiers - [UAX31](http://unicode.org/reports/tr31/)
* [Terraform Spec](https://github.com/hashicorp/hcl/blob/main/hclsyntax/spec.md)
* [Diagram terraform](https://diagrams.mingrammer.com/docs/getting-started/installation
* [Graphviz](https://www.graphviz.org/)



