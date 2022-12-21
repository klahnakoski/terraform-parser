import json

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
            "type": "module",
            "name": {"literal": "aws_reverse_proxy"},
            "params": [
                {
                    "name": "source",
                    "value": {
                        "literal": "git::ssh://git@github.com/futurice/terraform-utils.git//aws_reverse_proxy?ref=v11.0"
                    },
                },
                {"name": "origin_url", "value": {"literal": "http://example.com/"}},
                {"name": "site_domain", "value": "var.redirect_domain"},
                {"name": "name_prefix", "value": "var.name_prefix"},
                {"name": "comment_prefix", "value": "var.comment_prefix"},
                {
                    "name": "cloudfront_price_class",
                    "value": "var.cloudfront_price_class",
                },
                {"name": "viewer_https_only", "value": "var.viewer_https_only"},
                {
                    "name": "lambda_logging_enabled",
                    "value": "var.lambda_logging_enabled",
                },
                {"name": "tags", "value": "var.tags"},
                {
                    "name": "add_response_headers",
                    "value": [
                        {
                            "name": "Strict-Transport-Security",
                            "value": {"if_then_else": [
                                "var.redirect_with_hsts",
                                {"literal": "max-age=31557600; preload"},
                                {"literal": ""},
                            ]},
                        },
                        {"name": "Location", "value": "var.redirect_url"},
                    ],
                },
                {
                    "name": "override_response_status",
                    "value": {"if_then_else": [
                        "var.redirect_permanently",
                        {"literal": "301"},
                        {"literal": "302"},
                    ]},
                },
                {
                    "name": "override_response_status_description",
                    "value": {"if_then_else": [
                        "var.redirect_permanently",
                        {"literal": "Moved Permanently"},
                        {"literal": "Found"},
                    ]},
                },
                {
                    "name": "override_response_body",
                    "value": {"concat": [
                        {
                            "literal": (
                                '\n  <!doctype html>\n  <html lang="en">\n  <head>\n   '
                                ' <meta charset="utf-8">\n   '
                                " <title>Redirecting</title>\n  </head>\n  <body>\n   "
                                ' <pre>Redirecting to: <a href="'
                            )
                        },
                        "var.redirect_url",
                        {"literal": '">'},
                        "var.redirect_url",
                        {"literal": "</a></pre>\n  </body>\n  "},
                    ]},
                },
            ],
        }
        self.assertEqual(result, expected)

    def test_data(self):
        content = File("tests/examples/aws/aws_ec2_ebs_docker_host/data.tf").read()
        result = parse(content)
        expected = [
            {
                "name": {"literal": "this"},
                "resource": {"literal": "aws_availability_zones"},
                "type": "data",
            },
            {
                "name": {"literal": "this"},
                "params": [
                    {
                        "name": "default",
                        "value": {"if_then_else": [
                            {"eq": ["var.vpc_id", {"literal": ""}]},
                            "true",
                            "false",
                        ]},
                    },
                    {"name": "id", "value": "var.vpc_id"},
                ],
                "resource": {"literal": "aws_vpc"},
                "type": "data",
            },
            {
                "name": {"literal": "this"},
                "params": [
                    {"name": "vpc_id", "value": "data.aws_vpc.this.id"},
                    {"name": "availability_zone", "value": "local.availability_zone"},
                ],
                "resource": {"literal": "aws_subnet"},
                "type": "data",
            },
        ]
        self.assertEqual(result, expected)

    def test_ebs_docker_host_main(self):
        content = File("tests/examples/aws/aws_ec2_ebs_docker_host/main.tf").read()
        result = parse(content)
        expected = [
            {
                "name": {"literal": "this"},
                "params": [
                    {"name": "instance_type", "value": "var.instance_type"},
                    {"name": "ami", "value": "var.instance_ami"},
                    {"name": "availability_zone", "value": "local.availability_zone"},
                    {"name": "key_name", "value": "aws_key_pair.this.id"},
                    {
                        "name": "vpc_security_group_ids",
                        "value": "aws_security_group.this.id",
                    },
                    {"name": "subnet_id", "value": "data.aws_subnet.this.id"},
                    {
                        "name": "user_data",
                        "value": {"sha1": "local.reprovision_trigger"},
                    },
                    {
                        "name": "tags",
                        "value": {"merge": [
                            "var.tags",
                            {"map": [{"literal": "Name"}, "var.hostname"]},
                        ]},
                    },
                    {
                        "name": "volume_tags",
                        "value": {"merge": [
                            "var.tags",
                            {"map": [{"literal": "Name"}, "var.hostname"]},
                        ]},
                    },
                    {
                        "name": "root_block_device",
                        "value": {
                            "name": "volume_size",
                            "value": "var.root_volume_size",
                        },
                    },
                    {
                        "name": "connection",
                        "value": [
                            {"name": "user", "value": "var.ssh_username"},
                            {
                                "name": "private_key",
                                "value": {"file": "var.ssh_private_key_path"},
                            },
                            {"name": "agent", "value": "false"},
                        ],
                    },
                    {"provisioner": [
                        {"literal": "remote-exec"},
                        {
                            "name": "inline",
                            "value": [
                                {"concat": [
                                    {"literal": "sudo hostnamectl set-hostname "},
                                    "var.hostname",
                                ]},
                                {"concat": [
                                    {"literal": "echo 127.0.0.1 "},
                                    "var.hostname",
                                    {"literal": " | sudo tee -a /etc/hosts"},
                                ]},
                            ],
                        },
                    ]},
                    {"provisioner": [
                        {"literal": "remote-exec"},
                        {
                            "name": "script",
                            "value": {"concat": [
                                "path.module",
                                {"literal": "/provision-docker.sh"},
                            ]},
                        },
                    ]},
                    {"provisioner": [
                        {"literal": "file"},
                        {
                            "name": "source",
                            "value": {"concat": [
                                "path.module",
                                {"literal": "/provision-swap.sh"},
                            ]},
                        },
                        {
                            "name": "destination",
                            "value": {"concat": [
                                {"literal": "/home/"},
                                "var.ssh_username",
                                {"literal": "/provision-swap.sh"},
                            ]},
                        },
                    ]},
                    {"provisioner": [
                        {"literal": "remote-exec"},
                        {
                            "name": "inline",
                            "value": [
                                {"concat": [
                                    {"literal": "sh /home/"},
                                    "var.ssh_username",
                                    {"literal": "/provision-swap.sh "},
                                    "var.swap_file_size",
                                    {"literal": " "},
                                    "var.swap_swappiness",
                                ]},
                                {"concat": [
                                    {"literal": "rm /home/"},
                                    "var.ssh_username",
                                    {"literal": "/provision-swap.sh"},
                                ]},
                            ],
                        },
                    ]},
                ],
                "resource": {"literal": "aws_instance"},
                "type": "resource",
            },
            {
                "name": {"literal": "this"},
                "params": [
                    {
                        "name": "count",
                        "value": {"if_then_else": [
                            {"eq": ["var.data_volume_id", {"literal": ""}]},
                            "0",
                            "1",
                        ]},
                    },
                    {"name": "device_name", "value": {"literal": "/dev/xvdh"}},
                    {"name": "instance_id", "value": "aws_instance.this.id"},
                    {"name": "volume_id", "value": "var.data_volume_id"},
                ],
                "resource": {"literal": "aws_volume_attachment"},
                "type": "resource",
            },
            {
                "name": {"literal": "provisioners"},
                "params": [
                    {
                        "name": "count",
                        "value": {"if_then_else": [
                            {"eq": ["var.data_volume_id", {"literal": ""}]},
                            "0",
                            "1",
                        ]},
                    },
                    {
                        "name": "depends_on",
                        "value": {"literal": "aws_volume_attachment.this"},
                    },
                    {
                        "name": "connection",
                        "value": [
                            {"name": "host", "value": "aws_instance.this.public_ip"},
                            {"name": "user", "value": "var.ssh_username"},
                            {
                                "name": "private_key",
                                "value": {"file": "var.ssh_private_key_path"},
                            },
                            {"name": "agent", "value": "false"},
                        ],
                    },
                    {"provisioner": [
                        {"literal": "remote-exec"},
                        {
                            "name": "script",
                            "value": {"concat": [
                                "path.module",
                                {"literal": "/provision-ebs.sh"},
                            ]},
                        },
                    ]},
                    {"provisioner": [
                        {"literal": "remote-exec"},
                        {"name": "when", "value": {"literal": "destroy"}},
                        {
                            "name": "inline",
                            "value": {"concat": [
                                {"literal": "sudo umount -v "},
                                "aws_volume_attachment.this.device_name",
                            ]},
                        },
                    ]},
                ],
                "resource": {"literal": "null_resource"},
                "type": "resource",
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
