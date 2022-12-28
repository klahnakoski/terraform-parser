# terraform-parser

[![PyPI Latest Release](https://img.shields.io/pypi/v/terraform-parser.svg)](https://pypi.org/project/terraform-parser/)
[![Build Status](https://app.travis-ci.com/klahnakoski/terraform-parser.svg?branch=master)](https://travis-ci.com/github/klahnakoski/terraform-parser)
 [![Coverage Status](https://coveralls.io/repos/github/klahnakoski/terraform-parser/badge.svg?branch=dev)](https://coveralls.io/github/klahnakoski/terraform-parser?branch=dev)
[![Downloads](https://pepy.tech/badge/terraform-parser/month)](https://pepy.tech/project/terraform-parser)


Parse Terraform scripts into JSON


## Status

**Dec 2022** - This an experimental parser that can parse HCL2

## Problem

Terraform scripting can be complex; 


An application (or docker image, or lambda) is a black box to infrastructure: Services defined in infrastructure are communicated to the application as a set of environment variables.

We want to define services independently, in terraform, and then merge many services into a single infrastructure specification.  Specifically, we want to 

* avoiding terraform namespace collision
* merge the vars and other resources 
* merge the application environment variables  

## Solution

Most of the solution is to use terraform modules.  The remaining problem is 

The hope is to 

* parse terraform into Json data
* merge data from different terraform to single spec
* allow Python to modify data easily
* write out terraform (in diff-friendly way)

## References

* Look at what is done here - https://github.com/starhawking/python-terrascript
* Parser for [HCL1](https://github.com/virtuald/pyhcl)
* parser for [HCL2](https://pypi.org/project/python-hcl2/)
* Unicode Identifiers - [UAX31](http://unicode.org/reports/tr31/)
* [Terraform Spec](https://github.com/hashicorp/hcl/blob/main/hclsyntax/spec.md)



