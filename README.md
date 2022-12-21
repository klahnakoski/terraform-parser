# terraform-parser

Parse terraform scripts for further processing


## Status

**Dec 2022** - This an experimental parser  

## Problem

An application (or docker image, or lambda) is a black box to infrastructure: Services defined in infrastructure are communicated to the application as a set of environment variables.

We want to defined services independently, in terraform, and then merge many services into a single infrastructure specification.  Specifically, we want to 

* avoiding terraform namespace collision
* merge the vars and other resources 
* merge the application environment variables  

## Solution

The hope is to 

* parse terraform into Json data
* merge data from different terraform to single spec
* allow Python to modify data easily
* write out terraform (in diff-friendly way)

## References

* Look at what is done here - https://github.com/starhawking/python-terrascript

Found some parsers!

* https://github.com/virtuald/pyhcl
* https://pypi.org/project/python-hcl2/




