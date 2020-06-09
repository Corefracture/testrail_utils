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

from ..utils.tr_templater import TestRailTemplater


class fixture_data:

    #region General Test Rail Data

    project_id = 1
    suite_id = 1

    fields_csv = "custom_steps, title"

    #endregion General Test Rail Data

    #region Test Cases

    cases_csv = "1,2,3,4,5,6"

    case_one = {"id": 1, "title": "Case 1", "section_id": 1, "suite_id": 1,  "custom_templateid": 1,
        "type_id": 1, "priority_id": 1, "custom_notes": "Some notes!", "custom_steps":
         [
             {"content": "Step 1", "expected": "Expected Results 1"},
             {"content": "Step 2", "expected": "Expected Results 2"}
         ]}

    case_two = {"id": 2, "title": "Case 2", "section_id": 3, "suite_id": 1,  "custom_templateid": 2,
        "type_id": 1, "priority_id": 1, "custom_notes": "Some notes!", "custom_steps":
        [
            {"content": "Step 1", "expected": "Expected Results 1"},
            {"content": "Step 2", "expected": "Expected Results 2"}
        ]}

    case_templated_one = {"id": 3, "title": "Case 1 modified", "section_id": 5, "suite_id": 1, "custom_templateid": 1,
        "type_id": 2, "priority_id": 2, "custom_notes": "Some changed notes for templated case 1!", "custom_steps":
         [
             {"content": "Step 1", "expected": "Expected Results 1"},
             {"content": "Step 2 Modified", "expected": "Expected Results 2 Modified"}
         ]}

    case_templated_two = {"id": 4, "title": "Case 2 modified", "section_id": 6, "suite_id": 1, "custom_templateid": 2,
        "type_id": 3, "priority_id": 3, "custom_notes": "Some changed notes for templated case 2!", "custom_steps":
        [
            {"content": "Step 1", "expected": "Expected Results 1"},
            {"content": "Step 2 Modified", "expected": "Expected Results 2"},
            {"content": TestRailTemplater.get_default_end_marker(), "expected": ""},
            {"content": "Non-Template Step 3", "expected": "Expected Results 3"},
        ]}

    #endregion Test Cases

    #region Sections


    section_one = {"id": 1, "suite_id": 1, "name": "Section 1", "parent_id": None}
    section_two = {"id": 2, "suite_id": 1, "name": "Section 2", "parent_id": None}
    section_child_one = {"id": 3, "suite_id": 1, "name": "Child Section 1", "parent_id": 1, "depth": 1}
    section_grandchild_one = {"id": 4, "suite_id": 1, "name": "Grandchild Section 1", "parent_id": 3, "depth": 2}
    section_child_two = {"id": 5, "suite_id": 1, "name": "Child Section 2", "parent_id": 2, "depth": 1}
    section_grandchild_two = {"id": 6, "suite_id": 1, "name": "Grandchild Section 2", "parent_id": 5, "depth": 2}

    sections_list = [section_one, section_two, section_child_one, section_grandchild_one, section_child_two,
                     section_grandchild_two]

    #endregion Sections


