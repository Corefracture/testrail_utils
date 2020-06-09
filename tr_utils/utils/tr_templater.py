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

from tr_utils.interface.tr_interface import TestRailInterface


class TestRailTemplater:
    """
    The 'Templater' utility allows for the use of template test cases that can have changes
    deployed to multiple test cases using the target test case as a template.

    High-level Overview
    -   Create a test cases to be used as the template cases
    -   Fill in the template ID field data in the custom template ID field. This is the field that contains the
        unique identifier which instructs which test cases should be updated when changes are made to
        the template case. Its VERY important this field is populated witha unique identifier for each case to be
        used as a template
    -   Deploy copies of the template cases to be used as normal test cases. Ensure the unique template ID has been
        set for each case you're deploying. Failure to include a unique template ID will cause the template
        update process to fail.
    -   Determine the field names to use for the template data. For example using just the title field will only
        make changes to the Title field data. You can choose to use a single field only or as many fields as you wish.
    -   Use either
        A: A CSV list of section IDs that contain the template test cases
        or
        B: A CSV list of test case IDs to use as template test cases
        Remember that if the constructor parameter: get_all_child_sections is set to True all child sections
        will be scanned for template cases as well.
    -   Execute the templater utility anytime you wish to deploy changes made to the base template cases out to all
        the test cases that derive from the template case.
    """

    _end_marker = "!ENDTEMPLATE!"
    """ 
    This is the string identifier that designates where the template system should stop 'templating' and 
    leave the original data. For example if a string field contains "Hello! '_END_TEMPLATE_MARKER' Goodbye!"
    And Hello! is updated to Hiya! via template the new string would be "Hiya! '_END_TEMPLATE_MARKER' Goodbye!"
    
    This end tag also works for Steps field types. If a steps 'content' section contains '_END_TEMPLATE_MARKER' 
    all steps following that step will NOT be erased/updated during the template process.
    """

    _log = logging.getLogger(__name__)

    @staticmethod
    def get_default_end_marker() -> str:
        return TestRailTemplater._end_marker

    @staticmethod
    def _set_default_end_marker(marker_override: str):
        """
        Overrides the default 'end marker' string.
        :return:
        """
        TestRailTemplater._end_marker = marker_override

        return

    def __init__(self, tr_instance: TestRailInterface, tr_proj_id: int, template_id_field: str,
                 template_fields_csv: str, section_ids_csv: str = None, case_ids_csv: str = None,
                 tr_suite_id: int = None, end_marker_override: str = None, get_all_child_sections: bool = True):
        """
        :param tr_instance: The instance of TestRailInterface. The test rail interface allows for communication
        to the test rail server, as well as some small utility functions

        :param template_fields_csv: A CSV formatted string containing the field names to template. Note: Custom
        test rail fields are prefixed with 'custom_'. For example a custom test rail field named "steps" would
        be referred to as 'custom_steps' when using the Test Rail API

        :param template_id_field: The name of the field containing the template ID data

        :param section_ids_csv: A CSV formatted string containing test case section IDs to scan for template
        test cases. Any test cases found within these section IDs are considered the cases to use as templates.

        Note: Cases to be templated cannot reside in the same section or any section found in one of these sections.

        :param case_ids_csv: A CSV formatted string containing individual case IDs to be used as templates. Use the
        case_ids_csv parameter instead of the section_ids parameter if your test cases and template cases reside
        in the same section

        :param end_marker_override: An override of the default end marker. See the _end_marker class variable
        """

        try:
            if end_marker_override is not None:
                TestRailTemplater._set_default_end_marker(end_marker_override)

            self._tr = tr_instance
            self._tr_proj_id = tr_proj_id
            self._tr_suite_id = tr_suite_id
            self._template_id_field_name = template_id_field
            self._fields_to_template = template_fields_csv.split(',')
            self._get_all_child_sections = get_all_child_sections

            self._template_src_section_ids = []
            if section_ids_csv is not None:
                for section_id in section_ids_csv.split(','):
                    self._template_src_section_ids.append(int(section_id))

            self._template_src_case_ids = []
            if case_ids_csv is not None:
                for case_id in case_ids_csv.split(','):
                    self._template_src_case_ids.append(int(case_id))

        except Exception as e:
            self._log.exception("Failed constructing the templater class! Exception: {0}".format(e))

        return

    def execute_templater(self, dry_run: bool = False) -> int:
        """
        Executes the templater utility
        :param dry_run: When set to True dry_run prevents changes from being written to the test rail database
        :return:
        """

        # Assume the project is using single suite mode and grab the default suite for the project
        if self._tr_suite_id is None:
            self._tr_suite_id = self._tr.suites_get_default_suite(self._tr_proj_id)

        if self._verify_params() is False:
            self._log.error("Templater missing or failed to parse the required parameters. Please check logs. Exiting!")
            return 1

        # Retrieve all test case data from the target project / suite
        self._log.info("Retrieving test case data for project {0} using suite ID: {1}".format(self._tr_proj_id,
                                                                                              self._tr_suite_id))
        test_case_data = self._tr.retrieve_testcase_data(self._tr_proj_id, suite_id=self._tr_suite_id)
        self._log.info("Found {0} test cases!".format(len(test_case_data)))

        if self._get_all_child_sections is True and len(self._template_src_section_ids) > 0:
            sections_data = self._tr.retrieve_sections_data(self._tr_proj_id, self._tr_suite_id)
            self._template_src_section_ids = self._tr.get_child_sections(self._template_src_section_ids, sections_data)


        if self._template_src_case_ids is None or len(self._template_src_case_ids) > 0:
            # Get the template test cases from the source test case data
            self._log.info("Beginning to search for template test cases under the provided section IDs")
            template_case_data = self._get_template_cases_from_secs(test_case_data, self._template_src_section_ids,
                                                                    self._template_id_field_name)
            self._template_src_case_ids = self._tr.get_case_ids_from_case_data(list(template_case_data.values()))
            self._log.info("Found {0} template test cases!".format(len(template_case_data)))
        else:
            self._log.info("Beginning to search for template test cases with the provided template test case ids")
            template_case_data = self._get_template_cases_from_case_ids(self._template_src_case_ids, test_case_data,
                                                                        self._template_id_field_name)

        self._log.info("Beginning to search for test cases to update that have matching template ID values")
        test_cases_to_update = self._get_cases_to_update(list(template_case_data.keys()), self._template_src_case_ids,
                                                         test_case_data, self._template_id_field_name)

        self._log.info("Beginning test case update process. Dry Run: {0}".format(dry_run))
        case_ids_updated = self._update_test_cases(template_case_data, test_cases_to_update, dry_run)

        self._log.info("Updated {0} test cases. The following test case IDs have been updated {1}".
                       format(len(case_ids_updated), str.join(',', case_ids_updated)))

        return 0

    # region Private Functions

    def _update_test_cases(self, template_test_cases: dict, cases_to_update: dict,
                           dry_run: bool) -> list:
        """

        :param template_test_cases:
        :param cases_to_update:
        :return:
        """
        cases_updated = []

        try:
            for template_id, template_data in template_test_cases.items():
                if template_id in cases_to_update:
                    for case_to_update in cases_to_update[template_id]:
                        change_made = False

                        for field in self._fields_to_template:
                            template_field_data = template_data[field]

                            if type(template_field_data) is list:
                                end_template_after_step_index = self._check_for_endmarker_step(case_to_update[field])
                                if self._is_steps_list_same(case_to_update[field], template_field_data,
                                                            end_template_after_step_index) is False:
                                    if end_template_after_step_index == -1:
                                        case_to_update[field] = template_field_data
                                        change_made = True
                                    else:
                                        new_steps = []
                                        new_steps.extend(template_field_data)
                                        case_steps = case_to_update[field]

                                        for i in range(end_template_after_step_index, len(case_steps)):
                                            new_steps.append(case_steps[i])

                                        case_to_update[field] = new_steps
                                        change_made = True

                            elif type(template_field_data) is str:
                                if case_to_update[field] != template_field_data:
                                    if self._end_marker in case_to_update[field]:
                                        new_str_data = self._handle_string_replacement(template_field_data,
                                                                                       case_to_update[field])
                                        if new_str_data != "":
                                            case_to_update[field] = new_str_data
                                            change_made = True
                            else:
                                if case_to_update[field] != template_field_data:
                                    case_to_update[field] = template_field_data
                                    change_made = True

                        if dry_run is False and change_made is True:
                            if self._update_test_case(case_to_update) is True:
                                cases_updated.append(str(case_to_update['id']))

        except Exception as e:
            self._log.exception("Exception caught when attempting to update test case data! Exception: {0}".format(e))

        return cases_updated

    def _update_test_case(self, case_data) -> bool:
        """
        Initiaties the update call to the TestRail server
        :param case_data: The test case data for the test case to update
        :return: Returns True on success, otherwise false
        """
        update_result = self._tr.tr.cases.update_case(case_data['id'], **case_data)

        return 'error' not in update_result

    def _is_steps_list_same(self, case_data_steps: list, template_data_steps: list, end_marker_index: int) -> bool:
        """
        Helper method to determine if there are custom steps added after an end marker has been
        found in a Test Steps field type.
        :param case_data_steps: The steps data list object
        :param template_data_steps: The steps data list from the template case
        :param end_marker_index: The test steps index of the end marker (if found) in the case data
        :return:
        """
        if len(case_data_steps) < len(template_data_steps):
            return False
        elif end_marker_index > -1 and end_marker_index != len(template_data_steps):
            return False
        else:
            for i in range(0, len(template_data_steps)):
                if case_data_steps[i]['content'] != template_data_steps[i]['content']:
                    return False
                if case_data_steps[i]['expected'] != template_data_steps[i]['expected']:
                    return False

        return True

    def _check_for_endmarker_step(self, case_data_steps: list) -> int:
        """
        Helper function to scan all test steps in a test steps data field for the end marker. This is to identify where
        the last index to update should be, in case any custom steps have been added past the templated steps
        :param case_data_steps:
        :return:
        """
        ret_val = -1

        for i in range(0, len(case_data_steps)):
            step = case_data_steps[i]
            if self._end_marker in step['content']:
                ret_val = i
                break

        return ret_val

    def _handle_string_replacement(self, template_data: str, case_data: str) -> str:
        """
        Helper function
        :param template_data:
        :param case_data:
        :return:
        """
        ret_val = "{0}{1}{2}"

        splits = case_data.split(self._end_marker)
        if len(splits) > 1:
            if template_data == splits[0]:
                return ""
            ret_val = ret_val.format(template_data, self._end_marker, splits[1])

        return ret_val

    def _get_template_cases_from_case_ids(self, src_template_case_ids: list, test_case_data: list,
                                          template_id_field: str) -> dict:
        """
        Retrieve the template test cases that reside under the provided sectin ids
        :param src_template_case_ids: The provided Template Test Case IDs
        :param test_case_data: The source test cases
        :param template_id_field: The field name of the Template ID field
        :return:
        """
        template_cases = {}

        try:
            for i in range(0, len(test_case_data)):
                if test_case_data[i]['id'] in src_template_case_ids:
                    template_cases[test_case_data[i][template_id_field]] = test_case_data[i]

        except Exception as e:
            self._log.exception("Exception hit when finding template test cases! Exception:{0}".format(e))

        return template_cases

    def _get_template_cases_from_secs(self, test_case_data: list, section_ids: list, template_id_field: str) -> dict:
        """
        Retrieve the template test cases that reside under the provided sectin ids
        :param test_case_data: The source test cases
        :param section_ids: The section IDs to find matching test cases
        :param template_id_field: The field name of the Template ID field
        :return:
        """
        template_cases = {}

        try:
            for i in range(0, len(test_case_data)):
                if test_case_data[i]['section_id'] in section_ids:
                    template_cases[test_case_data[i][template_id_field]] = test_case_data[i]

        except Exception as e:
            self._log.exception("Exception hit when finding template test cases! Exception:{0}".format(e))

        return template_cases

    def _get_cases_to_update(self, template_ids: list, template_case_ids: list,
                             test_case_data: list, template_field_id: str) -> dict:
        """
        Get all the test cases which have matching template id data.
        :param template_ids: The template ID retrieved from the source template test cases
        :param test_case_data: The source test cases
        :param template_field_id: The field name of the template ID field
        :return: Returns a dict of template Id (keys) and a list of test cases (dicts) to update
        """
        cases_to_update = {}

        for template_id in template_ids:
            cases_to_update[template_id] = []

        try:
            for test_case in test_case_data:
                if test_case[template_field_id] in template_ids and test_case['id'] not in template_case_ids:
                        cases_to_update[test_case[template_field_id]].append(test_case)

        except Exception as e:
            self._log.exception("Failure encountered when getting case data to update! Exception: {0}".format(e))

        for key, val in cases_to_update.items():
            self._log.info("Found {0} cases to update for template ID: {1}".format(len(val), key))

        return cases_to_update

    def _verify_params(self) -> bool:
        """
        Verifies the required parameters for the templater utility are populated.
        :return: Returns False if required parameters are missing or invalid.
        """

        if self._tr_proj_id is None:
            self._log.error("Missing TestRail project ID. This is required for the templater utility.")
            return False

        if self._template_src_case_ids is None and self._template_src_section_ids is None:
            self._log.error("Missing source test cases or test case sections to template from!")
            return False

        if self._template_id_field_name is None:
            self._log.error("Missing template ID field name! This value is needed to find cases to template with"
                            "updates.")
            return False

        if self._fields_to_template is None or len(self._fields_to_template) == 0:
            self._log.error("Missing field names to template. This value is needed to set field values in the templated"
                            "test cases")
            return False

        return True

    def _case_data_error_check(self, case_data: dict, case_id: str) -> bool:
        """
        Checks for case data error messages from test rail and logs out if one is encountered.
        :param case_data:
        :param case_id:
        :return: Retturns True if an error is found, or False if no error
        """
        err_check = self._tr.case_data_have_error(case_data)
        if len(err_check) > 0:
            self._log.error("Encountered an error from TestRail when attempting to get case id: {0}. Error: {1}"
                            .format(case_id, err_check))
            return True
        else:
            return False

    # endregion
