from mo_dots import Data, exists
from mo_logs import logger
from mo_testing.fuzzytestcase import FuzzyTestCase

from mo_files import File
from mo_parsing.debug import Debugger
from mo_streams import it, stream
from terraform_parser import parse


class TestExamples(FuzzyTestCase):

    # https://github.com/futurice/terraform-examples/tree/master/aws/aws_reverse_proxy

    def test_main(self):
        content = File("tests/examples/aws/aws_domain_redirect/main.tf").read()
        result = parse(content)
        expected = {"aws_reverse_proxy": [
            {"source": {
                "literal": "git::ssh://git@github.com/futurice/terraform-utils.git//aws_reverse_proxy?ref=v11.0"
            }},
            {"origin_url": {"literal": "http://example.com/"}},
            {"site_domain": "var.redirect_domain"},
            {"name_prefix": "var.name_prefix"},
            {"comment_prefix": "var.comment_prefix"},
            {"cloudfront_price_class": "var.cloudfront_price_class"},
            {"viewer_https_only": "var.viewer_https_only"},
            {"lambda_logging_enabled": "var.lambda_logging_enabled"},
            {"tags": "var.tags"},
            {"add_response_headers": [
                {"Strict-Transport-Security": {"if_then_else": [
                    "var.redirect_with_hsts",
                    {"literal": "max-age=31557600; preload"},
                    {"literal": ""},
                ]}},
                {"Location": "var.redirect_url"},
            ]},
            {"override_response_status": {"if_then_else": [
                "var.redirect_permanently",
                {"literal": "301"},
                {"literal": "302"},
            ]}},
            {"override_response_status_description": {"if_then_else": [
                "var.redirect_permanently",
                {"literal": "Moved Permanently"},
                {"literal": "Found"},
            ]}},
            {"override_response_body": {"concat": [
                {
                    "literal": (
                        '\n  <!doctype html>\n  <html lang="en">\n  <head>\n    <meta'
                        ' charset="utf-8">\n    <title>Redirecting</title>\n  </head>\n'
                        '  <body>\n    <pre>Redirecting to: <a href="'
                    )
                },
                "var.redirect_url",
                {"literal": '">'},
                "var.redirect_url",
                {"literal": "</a></pre>\n  </body>\n  "},
            ]}},
        ]}
        self.assertEqual(result, expected)

    def test_data(self):
        content = File("tests/examples/aws/aws_ec2_ebs_docker_host/data.tf").read()
        result = parse(content)
        expected = [
            {"data": {"aws_availability_zones": {"literal": "this"}}},
            {"data": {"aws_vpc": {"this": [
                {"default": {"if_then_else": [
                    {"eq": ["var.vpc_id", {"literal": ""}]},
                    "true",
                    "false",
                ]}},
                {"id": "var.vpc_id"},
            ]}}},
            {"data": {"aws_subnet": {"this": [
                {"vpc_id": "data.aws_vpc.this.id"},
                {"availability_zone": "local.availability_zone"},
            ]}}},
        ]
        self.assertEqual(result, expected)

    def test_ebs_docker_host_main(self):
        content = File("tests/examples/aws/aws_ec2_ebs_docker_host/main.tf").read()
        result = parse(content)
        expected = [
            {"aws_instance": {"this": [
                {"instance_type": "var.instance_type"},
                {"ami": "var.instance_ami"},
                {"availability_zone": "local.availability_zone"},
                {"key_name": "aws_key_pair.this.id"},
                {"vpc_security_group_ids": "aws_security_group.this.id"},
                {"subnet_id": "data.aws_subnet.this.id"},
                {"user_data": {"sha1": "local.reprovision_trigger"}},
                {"tags": {"merge": [
                    "var.tags",
                    {"map": [{"literal": "Name"}, "var.hostname"]},
                ]}},
                {"volume_tags": {"merge": [
                    "var.tags",
                    {"map": [{"literal": "Name"}, "var.hostname"]},
                ]}},
                {"root_block_device": {"volume_size": "var.root_volume_size"}},
                {"connection": [
                    {"user": "var.ssh_username"},
                    {"private_key": {"file": "var.ssh_private_key_path"}},
                    {"agent": "false"},
                ]},
                {"provisioner": {"remote-exec": {"inline": [
                    {"concat": [
                        {"literal": "sudo hostnamectl set-hostname "},
                        "var.hostname",
                    ]},
                    {"concat": [
                        {"literal": "echo 127.0.0.1 "},
                        "var.hostname",
                        {"literal": " | sudo tee -a /etc/hosts"},
                    ]},
                ]}}},
                {"provisioner": {"remote-exec": {"script": {"concat": [
                    "path.module",
                    {"literal": "/provision-docker.sh"},
                ]}}}},
                {"provisioner": {"file": [
                    {"source": {"concat": [
                        "path.module",
                        {"literal": "/provision-swap.sh"},
                    ]}},
                    {"destination": {"concat": [
                        {"literal": "/home/"},
                        "var.ssh_username",
                        {"literal": "/provision-swap.sh"},
                    ]}},
                ]}},
                {"provisioner": {"remote-exec": {"inline": [
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
                ]}}},
            ]}},
            {"aws_volume_attachment": {"this": [
                {"count": {"if_then_else": [
                    {"eq": ["var.data_volume_id", {"literal": ""}]},
                    0,
                    1,
                ]}},
                {"device_name": {"literal": "/dev/xvdh"}},
                {"instance_id": "aws_instance.this.id"},
                {"volume_id": "var.data_volume_id"},
            ]}},
            {"null_resource": {"provisioners": [
                {"count": {"if_then_else": [
                    {"eq": ["var.data_volume_id", {"literal": ""}]},
                    0,
                    1,
                ]}},
                {"depends_on": {"literal": "aws_volume_attachment.this"}},
                {"connection": [
                    {"host": "aws_instance.this.public_ip"},
                    {"user": "var.ssh_username"},
                    {"private_key": {"file": "var.ssh_private_key_path"}},
                    {"agent": "false"},
                ]},
                {"provisioner": {"remote-exec": {"script": {"concat": [
                    "path.module",
                    {"literal": "/provision-ebs.sh"},
                ]}}}},
                {"provisioner": {"remote-exec": [
                    {"when": {"literal": "destroy"}},
                    {"inline": {"concat": [
                        {"literal": "sudo umount -v "},
                        "aws_volume_attachment.this.device_name",
                    ]}},
                ]}},
            ]}},
        ]
        self.assertEqual(result, expected)

    def test_variables(self):
        content = File("tests/examples/aws/aws_ec2_ebs_docker_host/variables.tf").read()
        result = parse(content)
        expect = [
            {"local": {"reprovision_trigger": {"concat": [
                {"literal": "\n    # Trigger reprovision on variable changes:\n    "},
                "var.hostname",
                {"literal": "\n    "},
                "var.ssh_username",
                {"literal": "\n    "},
                "var.ssh_private_key_path",
                {"literal": "\n    "},
                "var.ssh_public_key_path",
                {"literal": "\n    "},
                "var.swap_file_size",
                {"literal": "\n    "},
                "var.swap_swappiness",
                {"literal": "\n    "},
                "var.reprovision_trigger",
                {"literal": "\n    # Trigger reprovision on file changes:\n    "},
                {"file": {"concat": [
                    "path.module",
                    {"literal": "/provision-docker.sh"},
                ]}},
                {"literal": "\n    "},
                {"file": {"concat": ["path.module", {"literal": "/provision-ebs.sh"}]}},
                {"literal": "\n    "},
                {"file": {"concat": [
                    "path.module",
                    {"literal": "/provision-swap.sh"},
                ]}},
                {"literal": "\n  "},
            ]}}},
            {"local": {"availability_zone":                "data.aws_availability_zones.this.names[0]"}},
            {"var": {"hostname": [
                {"description": {
                    "literal": (
                        "Hostname by which this service is identified in metrics,"
                        " logs etc"
                    )
                }},
                {"default": {"literal": "aws-ec2-ebs-docker-host"}},
            ]}},
            {"var": {"instance_type": [
                {"description": {
                    "literal": (
                        "See https://aws.amazon.com/ec2/instance-types/ for options;"
                        " for example, typical values for small workloads are"
                        ' `"t2.nano"`, `"t2.micro"`, `"t2.small"`, `"t2.medium"`, and'
                        ' `"t2.large"`'
                    )
                }},
                {"default": {"literal": "t2.micro"}},
            ]}},
            {"var": {"instance_ami": [
                {"description": {
                    "literal": (
                        "See https://cloud-images.ubuntu.com/locator/ec2/ for options"
                    )
                }},
                {"default": {"literal": "ami-0bdf93799014acdc4"}},
            ]}},
            {"var": {"ssh_private_key_path": [
                {"description": {
                    "literal": (
                        "SSH private key file path, relative to Terraform project root"
                    )
                }},
                {"default": {"literal": "ssh.private.key"}},
            ]}},
            {"var": {"ssh_public_key_path": [
                {"description": {
                    "literal": (
                        "SSH public key file path, relative to Terraform project root"
                    )
                }},
                {"default": {"literal": "ssh.public.key"}},
            ]}},
            {"var": {"ssh_username": [
                {"description": {
                    "literal": (
                        "Default username built into the AMI (see 'instance_ami')"
                    )
                }},
                {"default": {"literal": "ubuntu"}},
            ]}},
            {"var": {"vpc_id": [
                {"description": {
                    "literal": (
                        "ID of the VPC our host should join; if empty, joins your"
                        " Default VPC"
                    )
                }},
                {"default": {"literal": ""}},
            ]}},
            {"var": {"reprovision_trigger": [
                {"description": {
                    "literal": (
                        "An arbitrary string value; when this value changes, the host"
                        " needs to be reprovisioned"
                    )
                }},
                {"default": {"literal": ""}},
            ]}},
            {"var": {"root_volume_size": [
                {"description": {
                    "literal": (
                        "Size (in GiB) of the EBS volume that will be created and"
                        " mounted as the root fs for the host"
                    )
                }},
                {"default": 8},
            ]}},
            {"var": {"data_volume_id": [
                {"description": {
                    "literal": "The ID of the EBS volume to mount as `/data`"
                }},
                {"default": {"literal": ""}},
            ]}},
            {"var": {"swap_file_size": [
                {"description": {
                    "literal": "Size of the swap file allocated on the root volume"
                }},
                {"default": {"literal": "512M"}},
            ]}},
            {"var": {"swap_swappiness": [
                {"description": {
                    "literal": "Swappiness value provided when creating the swap file"
                }},
                {"default": {"literal": "10"}},
            ]}},
            {"var": {"allow_incoming_http": [
                {"description": {
                    "literal": (
                        "Whether to allow incoming HTTP traffic on the host security"
                        " group"
                    )
                }},
                {"default": "false"},
            ]}},
            {"var": {"allow_incoming_https": [
                {"description": {
                    "literal": (
                        "Whether to allow incoming HTTPS traffic on the host security"
                        " group"
                    )
                }},
                {"default": "false"},
            ]}},
            {"var": {"allow_incoming_dns": [
                {"description": {
                    "literal": (
                        "Whether to allow incoming DNS traffic on the host security"
                        " group"
                    )
                }},
                {"default": "false"},
            ]}},
            {"var": {"tags": [
                {"description": {
                    "literal": (
                        "AWS Tags to add to all resources created (where possible); see"
                        " https://aws.amazon.com/answers/account-management/aws-tagging-strategies/"
                    )
                }},
                {"type": {"literal": "map"}},
                {"default": {"literal": {}}},
            ]}},
        ]
        self.assertEqual(result, expect)

    def test_splat(self):
        content = """locals {
          function_id         = "${element(concat(aws_lambda_function.local_zipfile.*.id, list("")), 0)}${element(concat(aws_lambda_function.s3_zipfile.*.id, list("")), 0)}"
        }"""
        result = parse(content)
        expect = {"local": {"function_id": {"concat": [
            {"element": [
                {"concat": [
                    "aws_lambda_function.local_zipfile.*.id",
                    {"list": {"literal": ""}},
                ]},
                0,
            ]},
            {"element": [
                {"concat": [
                    "aws_lambda_function.s3_zipfile.*.id",
                    {"list": {"literal": ""}},
                ]},
                0,
            ]},
        ]}}}
        self.assertEqual(result, expect)

    def test_output(self):
        content = """output "hostname" {
          description = "Hostname by which this service is identified in metrics, logs etc"
          value       = "${var.hostname}"
        }"""
        result = parse(content)
        expect = {"output": {"hostname": [
            {"description": {
                "literal": (
                    "Hostname by which this service is identified in metrics, logs etc"
                )
            }},
            {"value": "var.hostname"},
        ]}}
        self.assertEqual(result, expect)

    def test_neg_int(self):
        content = """output "host" {value="${-1}"}"""
        result = parse(content)
        expect = {"output": {"host": {"value": -1}}}
        self.assertEqual(result, expect)

    def test_comment(self):
        content = """/**/"""
        result = parse(content)
        expect = None
        self.assertEqual(result, expect)

    def test_dashes_in_identifier(self):
        content = """output "host_w-dash" {}"""
        result = parse(content)
        expect = {"output": {"host_w-dash": {}}}
        self.assertEqual(result, expect)

    def test_0_in_path(self):
        content = """output "host" {  name    = "${aws_acm_certificate.this.domain_validation_options.0.resource_record_name}"}"""
        result = parse(content)
        expect = {"output": {"host": {"name": "aws_acm_certificate.this.domain_validation_options.0.resource_record_name"}}}
        self.assertEqual(result, expect)

    def test_dot_accessor_in_path(self):
        content = """output "host" {  subnet_id = aws_subnet.private_subnet[1].id}"""
        with Debugger():
            result = parse(content)
        expect = {"output": {"host": {"subnet_id": "aws_subnet.private_subnet[1].id"}}}
        self.assertEqual(result, expect)



    def test_examples(self):
        def parser(text, attachments) -> Data:
            try:
                return parse(text)
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

        self.assertTrue(all(exists(r) for r in result))
