from unittest import TestCase
from pmo.syntax_util import split_into_blocks


class SyntaxUtilTest(TestCase):
    def test_split_into_blocks(self):
        lines = ["", "aa", " bbb", " cccc", "", "", "ddddd", "", "ee"]
        blocks = []
        for start, end in split_into_blocks(lines):
            blocks.append(','.join(lines[start: end]))
        self.assertListEqual(blocks, ['aa, bbb, cccc', 'ddddd', 'ee'])
