from string import whitespace

from mo_parsing import Literal, AnyChar, SkipTo, Whitespace, Forward, Many, delimited_list, Regex, infix_notation

expression = Forward()

with whitespace.NONE:
    quote = Literal("\"")
    string_var = "${"+expression+"}"
    string = quote + Many(Literal("\\\"") | ~quote + AnyChar() | string_var) + quote

    rest = Forward()
    eod = SkipTo("\n", include=True)("end")
    multiline = Literal("<<") + eod / (lambda t: rest << SkipTo(eod)) + rest("content") / string.parse

comment = Literal("#")+SkipTo("\n", include=True)

white = Whitespace()
white.add_ignore(comment)


identifier = Regex("\w+")

with white:


    assignment = identifier +"="+ expression
    resource = identifier("type") + string("name") +"{" +delimited_list(assignment)


    compound = string

    expression << (
        infix_notation(
            compound,
            [

                (Literal("?"), Literal(":")),
            ]
        )("value").set_parser_name("expression")
    )

# module "aws_reverse_proxy" {
#   # Available inputs: https://github.com/futurice/terraform-utils/tree/master/aws_reverse_proxy#inputs
#   # Check for updates: https://github.com/futurice/terraform-utils/compare/v11.0...master
#   source = "git::ssh://git@github.com/futurice/terraform-utils.git//aws_reverse_proxy?ref=v11.0"
#
#   origin_url             = "http://example.com/"           # note that this is just a dummy value to satisfy CloudFront, it won't ever be used with the override_* variables in place
#   site_domain            = "${var.redirect_domain}"
#   name_prefix            = "${var.name_prefix}"
#   comment_prefix         = "${var.comment_prefix}"
#   cloudfront_price_class = "${var.cloudfront_price_class}"
#   viewer_https_only      = "${var.viewer_https_only}"
#   lambda_logging_enabled = "${var.lambda_logging_enabled}"
#   tags                   = "${var.tags}"
#
#   add_response_headers = {
#     "Strict-Transport-Security" = "${var.redirect_with_hsts ? "max-age=31557600; preload" : ""}"
#     "Location"                  = "${var.redirect_url}"
#   }
#
#   override_response_status             = "${var.redirect_permanently ? "301" : "302"}"
#   override_response_status_description = "${var.redirect_permanently ? "Moved Permanently" : "Found"}"
#
#   override_response_body = <<EOF
#   <!doctype html>
#   <html lang="en">
#   <head>
#     <meta charset="utf-8">
#     <title>Redirecting</title>
#   </head>
#   <body>
#     <pre>Redirecting to: <a href="${var.redirect_url}">${var.redirect_url}</a></pre>
#   </body>
#   EOF
# }

def parse(content):
