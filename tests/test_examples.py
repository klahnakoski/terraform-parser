from mo_dots import Data
from mo_logs import logger
from mo_parsing.debug import Debugger
from mo_testing.fuzzytestcase import FuzzyTestCase

from mo_files import File
from mo_streams import it, stream, ERROR
from terraform_parser import parse


class TestExamples(FuzzyTestCase):

    # https://github.com/futurice/terraform-examples/tree/master/aws/aws_reverse_proxy

    def test_main(self):
        content = File("tests/examples/aws/aws_domain_redirect/main.tf").read()
        result = parse(content)
        expected = {
            "name": {"literal": "aws_reverse_proxy"},
            "params": {
                "add_response_headers": {
                    "Location": "var.redirect_url",
                    "Strict-Transport-Security": {
                        "then": {"literal": "max-age=31557600; preload"},
                        "when": "var.redirect_with_hsts",
                    },
                },
                "cloudfront_price_class": "var.cloudfront_price_class",
                "comment_prefix": "var.comment_prefix",
                "lambda_logging_enabled": "var.lambda_logging_enabled",
                "name_prefix": "var.name_prefix",
                "origin_url": {"literal": "http://example.com/"},
                "override_response_body": {"concat": [
                    {
                        "literal": (
                            '\n  <!doctype html>\n  <html lang="en">\n  <head>\n   '
                            ' <meta charset="utf-8">\n    <title>Redirecting</title>\n '
                            ' </head>\n  <body>\n    <pre>Redirecting to: <a href="'
                        )
                    },
                    "var.redirect_url",
                    {"literal": '">'},
                    "var.redirect_url",
                    {"literal": "</a></pre>\n  </body>\n  "},
                ]},
                "override_response_status": {
                    "else": {"literal": "302"},
                    "then": {"literal": "301"},
                    "when": "var.redirect_permanently",
                },
                "override_response_status_description": {
                    "else": {"literal": "Found"},
                    "then": {"literal": "Moved Permanently"},
                    "when": "var.redirect_permanently",
                },
                "site_domain": "var.redirect_domain",
                "source": {
                    "literal": "git::ssh://git@github.com/futurice/terraform-utils.git//aws_reverse_proxy?ref=v11.0"
                },
                "tags": "var.tags",
                "viewer_https_only": "var.viewer_https_only",
            },
            "type": "module",
        }
        self.assertEqual(result, expected)

    def test_data(self):
        content = File("tests/examples/aws/aws_ec2_ebs_docker_host/data.tf").read()
        with Debugger():
            result = parse(content)
        expected = [
            {
                "name": {"literal": "this"},
                "resource": {"literal": "aws_availability_zones"},
                "type": "data",
            },
            {
                "name": {"literal": "this"},
                "params": {
                    "default": {"if_then_else": [
                        {"eq": ["var.vpc_id", {"literal": ""}]},
                        "true",
                        "false",
                    ]},
                    "id": "var.vpc_id",
                },
                "resource": {"literal": "aws_vpc"},
                "type": "data",
            },
            {
                "name": {"literal": "this"},
                "params": {
                    "availability_zone": "local.availability_zone",
                    "vpc_id": "data.aws_vpc.this.id",
                },
                "resource": {"literal": "aws_subnet"},
                "type": "data",
            },
        ]
        self.assertEqual(result, expected)

    def test_examples(self):
        def parser(text, attachments) -> Data:
            try:
                parse(text)
            except Exception as cause:
                logger.warning(
                    "Could not parse {{file}}", file=attachments["file"], cause=cause
                )

        result = (
            stream(File("tests/examples").leaves)
            .filter(it.extension == "tf")
            .attach(file=it)
            .read()
            .map(parser)
            .to_list()
        )

        print(result)
