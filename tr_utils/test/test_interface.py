# ******************* LICENSE ***************************
# MIT License
# Copyright (c) 2019 Corefracture, cf, Chris Coleman

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ********************************************************

import unittest

from .fixtures import fixture_data
from ..interface.tr_interface import TestRailInterface


class TestTestRailInterface(unittest.TestCase):
    def setUp(self):
        self.fixture_data = fixture_data()
        self.tr = TestRailInterface(skip_login=True)

    # region Sections Test

    def test_child_sections_root(self):
        """
        Test getting children of a root section
        :return:
        """
        secs = self.tr.get_child_sections([self.fixture_data.section_one["id"]], self.fixture_data.sections_list)

        self.assertEqual(3, len(secs))
        self.assertTrue(1 in secs and 3 in secs and 4 in secs)

    def test_child_sections_grandchild_test(self):
        """
        Test getting children of a child
        :return:
        """
        secs = self.tr.get_child_sections([self.fixture_data.section_child_one["id"]], self.fixture_data.sections_list)

        self.assertEqual(2, len(secs))
        self.assertTrue(3 in secs and 4 in secs)

    def test_child_sections_mutiple_roots(self):
        """
        Test getting children of a child
        :return:
        """
        secs = self.tr.get_child_sections([self.fixture_data.section_one["id"],
                                 self.fixture_data.section_two["id"]], self.fixture_data.sections_list)

        self.assertEqual(6, len(secs))
        self.assertTrue(1 in secs and 3 in secs and 4 in secs and 2 in secs and 5 in secs and 6 in secs)

    def test_child_sections_mutiple_mix_root(self):
        """
        Test getting children of a child
        :return:
        """
        secs = self.tr.get_child_sections([self.fixture_data.section_child_one["id"],
                                 self.fixture_data.section_two["id"]], self.fixture_data.sections_list)

        self.assertEqual(5, len(secs))
        self.assertTrue(3 in secs and 4 in secs and 2 in secs and 5 in secs and 6 in secs)


    # endregion Sections Test

if __name__ == '__main__':
    unittest.main()
