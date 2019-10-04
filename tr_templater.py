import logging
from tr_interface import TestRailInterface


class TestRailTemplater:
    """

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

    _tr: TestRailInterface = None
    _tr_proj_id: str = None
    _tr_suite_id: str = None
    _fields_to_template = None
    _template_id_field_name = None
    _template_src_section_ids = None
    _template_src_case_ids = None

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

    def __init__(self, tr_instance: TestRailInterface, tr_proj_id: str, template_id_field: str,
                 template_fields_csv: str, section_ids_csv: str = None, case_ids_csv: str = None,
                 tr_suite_id: str = None, end_marker_override: str = None, get_all_child_sections: bool = True):
        """

        :param tr_instance:
        :param template_fields_csv:
        :param template_id_field:
        :param section_ids_csv:
        :param case_ids_csv:
        :param end_marker_override:
        """

        if end_marker_override is not None:
            TestRailTemplater._set_default_end_marker(end_marker_override)

        self._tr = tr_instance
        self._tr_proj_id = tr_proj_id
        self._tr_suite_id = tr_suite_id
        self._template_id_field_name = template_id_field
        self._fields_to_template = template_fields_csv.split(',')
        self._get_all_child_sections = get_all_child_sections

        if section_ids_csv is not None:
            self._template_src_section_ids = section_ids_csv.split(',')

        if case_ids_csv is not None:
            self._template_src_case_ids = case_ids_csv.split(',')

        # Assume the project is using single suite mode and grab the default suite for the project
        if self._tr_suite_id is None:
            suites = self._tr.tr.suites.get_suites(self._tr_proj_id)
            if 'error' in suites or len(suites) == 0 or 'id' not in suites[0]:
                self._log.error("Error encountered when attempting to identify default suite ID for project ID {0}. "
                                "Error: {1}".format(self._tr_proj_id, suites['error']))
            else:
                self._tr_suite_id = suites[0]['id']

        return

    def execute_templater(self, dry_run: bool = False) -> int:
        """

        :param dry_run:
        :return:
        """

        if self._verify_params() is False:
            self._log.error("Templater missing or failed to parse the required parameters. Please check logs. Exiting!")
            return 1

        # Retrieve all test case data from the target project / suite
        self._log.info("Retrieving test case data for project {0} using suite ID: {1}".format(self._tr_proj_id,
                                                                                              self._tr_suite_id))
        test_case_data = self._tr.tr.cases.get_cases(self._tr_proj_id, suite_id=self._tr_suite_id)
        self._log.info("Found {0} test cases!".format(len(test_case_data)))

        if self._get_all_child_sections is True:
            self._template_src_section_ids = self._get_child_sections()

        # Get the template test cases from the source test case data
        self._log.info("Beginning to search for template test cases under the provided section IDs")
        template_case_data = self._get_template_cases(test_case_data, self._template_src_section_ids,
                                                      self._template_id_field_name)
        template_case_ids = self._get_case_ids_from_case_data(list(template_case_data.values()))
        self._log.info("Found {0} template test cases!".format(len(template_case_data)))

        self._log.info("Beginning to search for test cases to update that have matching template ID values")
        test_cases_to_update = self._get_cases_to_update(list(template_case_data.keys()), template_case_ids,
                                                         test_case_data, self._template_id_field_name)

        self._log.info("Beginning test case update process. Dry Run: {0}".format(dry_run))
        case_ids_updated = self._update_test_cases(template_case_data, test_cases_to_update, dry_run)

        self._log.info("Updated {0} test cases. The following test case IDs have been updated {1}".
                       format(len(case_ids_updated), str.join(',', case_ids_updated)))

        return 0

    # region Private Functions

    def _get_all_descendants_of_section(self, section_id, section_lookups: dict) -> list:
        """
        Recursively traverses section IDs to find all descendants of a section
        :param section_id: The parent section ID
        :param section_lookups: section lookup table, section id -> parent section id
        :return:
        """
        ret_val = []


        for sec_id, prnt_id in section_lookups.items():
            if section_id == prnt_id:
                ret_val.append(sec_id)
                ret_val.extend(self._get_all_descendants_of_section(sec_id, section_lookups))

        return ret_val

    def _get_case_ids_from_case_data(self, case_data: list) -> list:
        ret_val = []

        for case in case_data:
            ret_val.append(case['id'])

        return ret_val

    def _get_child_sections(self) -> list:
        """

        :return:
        """
        new_sec_ids = []

        try:
            sections = self._tr.tr.sections.get_sections(self._tr_proj_id, self._tr_suite_id)
            temp_lookup = {}
            for i in range(0, len(sections)):
                section = sections[i]
                parent_id = section['parent_id']
                sec_id = section['id']
                temp_lookup[sec_id] = parent_id
                new_sec_ids = []
            for section_id in self._template_src_section_ids:
                new_sec_ids.append(section_id)
                new_sec_ids.extend(self._get_all_descendants_of_section(int(section_id), temp_lookup))

        except Exception as e:
            self._log.exception("Exception caught when retrieving source test cases for templater! Exception: {0}"
                                .format(e))

        return new_sec_ids

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
                            update_result = self._tr.tr.cases.update_case(case_to_update['id'], **case_to_update)
                            if 'error' not in update_result:
                                cases_updated.append(str(case_to_update['id']))

        except Exception as e:
            self._log.exception("Exception caught when attempting to update test case data! Exception: {0}".format(e))

        return cases_updated

    def _is_steps_list_same(self, case_data_steps: list, template_data_steps: list, end_marker_index: int) -> bool:

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

    def _get_template_cases(self, test_case_data: list, section_ids: list, template_id_field: str) -> dict:
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
            self._log   .error("Missing TestRail project ID. This is required for the templater utility.")
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
