from mo_files import File
from mo_parsing.debug import Debugger
from mo_testing.fuzzytestcase import FuzzyTestCase

from terraform_parser import parse


class TestExamples(FuzzyTestCase):

    # https://github.com/futurice/terraform-examples/tree/master/aws/aws_reverse_proxy

    def test_main(self):
        content = File("tests/examples/aws/aws_domain_redirect/main.tf").read()
        result = parse(content)
        expected = {}
        self.assertEqual(result, expected)