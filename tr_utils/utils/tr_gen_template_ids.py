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

import logging
import uuid

from tr_utils.interface.tr_interface import TestRailInterface


class TemplateIDGen:
    """
    Generates unique template IDs for the provided test case IDs or those found under the provided section IDs

    The Unique identifier is generated using the uuid package.
    """

    _log = logging.getLogger(__name__)

    def __init__(self, tr_instance: TestRailInterface, template_id_field: str, tr_proj_id: int, tr_suite_id: int,
                 section_ids_csv: str = None, case_ids_csv: str = None, overwrite_existing_id: bool = True,
                 get_all_child_sections: bool = True):
        """
        Template ID gen ctor

        :param tr_instance: Initialized instance of TestRailInterface
        :param template_id_field: The TestRail case field to write the unique ID to
        :param tr_proj_id: The TestRail project ID to work on
        :param tr_suite_id: The suite ID within the TestRail project ID, if applicable
        :param section_ids_csv: If searching for cases by sections. The List of section IDs to search
        :param case_ids_csv: If search for cases by case ID, the list of case IDs to update
        :param overwrite_existing_id: Overwrite existing data found in the template_id_field
        :param get_all_child_sections: If searching by section_ids, include all descendant sections in the search
        """
        self._tr = tr_instance
        self._tr_proj_id = tr_proj_id
        self._tr_suite_id = tr_suite_id
        self._template_id_field_name = template_id_field
        self._section_ids = section_ids_csv
        self._case_ids_to_template = case_ids_csv
        self._override_existing_id = overwrite_existing_id
        self._get_all_child_sections = get_all_child_sections

        if self._section_ids is not None:
            self._section_ids = self._section_ids.split(',')

        if self._case_ids_to_template is not None:
            self._case_ids_to_template = self._case_ids_to_template.split(',')

        return

    def execute_id_gen(self, dry_run: bool = False) -> int:
        """
        Executes the template ID generation utility.
        :param dry_run: If True, does not write any data to the TestRail database.
        :return:
        """
        test_case_data = self._tr.tr.cases.get_cases(int(self._tr_proj_id), suite_id=self._tr_suite_id)

        if self._get_all_child_sections is True:
            self._section_ids = self._get_child_sections()

        cases_to_update = self._get_cases_to_update(test_case_data, self._section_ids, self._case_ids_to_template)

        for test_case in cases_to_update:
            if dry_run is False:
                template_id = uuid.uuid4().hex
                self._log.debug("Template ID: {0} generated for CaseID: {1}", template_id, test_case['id'])
                test_case[self._template_id_field_name] = template_id
                self._tr.tr.cases.update_case(test_case['id'], **test_case)
        # TODO: cf: Error code setting and handling for failed steps.

        return 0

    def _get_cases_to_update(self, test_case_data: list, section_ids: list = None,
                             test_case_ids: list = None) -> list:
        """
        Searches the provided test case data and identifies test cases matching the test case ID list or the
        section ID list.
        :param test_case_data: The source list of test cases to loop over
        :param section_ids: If searching by section ids, the section id List
        :param test_case_ids: If searching by test case ids, the test case id List
        :return: Returns a list populated with test case objects for test cases found matching the test case ID list or
        the section IDs list.
        """
        cases_to_update = []

        if section_ids is None and test_case_ids is None:
            self._log.error("Section IDs list and Test Case IDs list were both None, cannot locate test cases"
                            "to update!")

            return cases_to_update

        try:
            # dupe code to avoid unneeded if checks
            if section_ids is not None:
                for test_case in test_case_data:
                    sec_id = test_case['section_id']
                    if sec_id is not None and str(sec_id) in section_ids:
                        if test_case[self._template_id_field_name] is None or self._override_existing_id is True:
                            cases_to_update.append(test_case)
            else:
                for test_case in test_case_data:
                    if test_case['id'] in test_case_ids:
                        if test_case[self._template_id_field_name] is None or self._override_existing_id is True:
                            cases_to_update.append(test_case)

        except Exception as e:
            self._log.exception("Failure encountered when getting case data to update! Exception: {0}".format(e))

        cases_len = len(cases_to_update)
        if cases_len > 0:
            self._log.info("Found {0} cases to generate template IDs for", cases_len)

        return cases_to_update

    def _get_child_sections(self) -> list:
        """
        Retrieve all descendants of the provided section ids
        :return: Returns a list of section ids
        """
        new_sec_ids = []

        try:
            sections = self._tr.tr.sections.get_sections(int(self._tr_proj_id), suite_id=self._tr_suite_id)
            for section_id in self._section_ids:
                new_sec_ids.append(section_id)
                child_secs = self._tr.get_child_sections([int(section_id)], sections)
                if len(child_secs) > 0:
                    new_sec_ids.extend(child_secs)

        except Exception as e:
            self._log.exception("Exception caught when retrieving source test cases for templater! Exception: {0}"
                                .format(e))

        return new_sec_ids

    def _verify_params(self) -> bool:
        """
        Verifies the required parameters for the templater utility are populated.
        :return: Returns False if required parameters are missing or invalid.
        """
        if self._tr_proj_id is None:
            self._log.error("Missing TestRail project ID. This is required for the templater utility.")
            return False

        if self._case_ids_to_template is None and self._section_ids is None:
            self._log.error("Missing source test cases or test case sections to template from!")
            return False

        if self._template_id_field_name is None:
            self._log.error("Missing template ID field name! This value is needed to find cases to template with"
                            "updates.")
            return False

        return True
