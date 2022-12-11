from mo_files import File
from mo_testing.fuzzytestcase import FuzzyTestCase


class TestExamples(FuzzyTestCase):

    # https://github.com/futurice/terraform-examples/tree/master/aws/aws_reverse_proxy

    def test_main(self):
        content = File("tests/examples/aws/aws_domain_redirect/main.tf").read()
        result = parse(content)
        expected = {}
        self.assertEqual(result, expected)