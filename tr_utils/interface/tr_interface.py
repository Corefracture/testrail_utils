######################## LICENSE ########################
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
#########################################################

import logging
import os

from testrail_api import TestRailAPI


class TestRailInterface:
    """
    TestRail API interface wrapper. Provides a handle for a tr interface.
    """

    _ENV_URL_PARAM_NAME = "TR_URL"
    _ENV_USER_PARAM_NAME = "TR_USER"
    _ENV_PASS_PARAM_NAME = "TR_PASS"

    _logger = logging.getLogger(__name__)
    _initialized = False
    _api = None
    """
    Holds the initialized TestRailAPI instance
    """

    @property
    def tr(self) -> TestRailAPI:
        """
        Property method for returning the TestRailAPI
        :return: An instance of TestRailAPI, or None if the TestRailAPI hasn't been initialized
        """

        return self._api

    @property
    def is_initialized(self) -> bool:
        """
        Property to determine if the API has been initialized. If false this indicates the TestRail
        user, password, or URL was not set correctly
        :return: A bool indicating initialization status
        """
        return self._initialized

    def __init__(self, tr_url=None, tr_user=None, tr_pass=None, skip_login=False):
        """
        Initializes the TestRailInterface. If parameters are no provided the class utilizies os.getenv to
        attempt to retrieve the parameter data from environment variables.

        See _ENV_* variables in this class for environment variable names.

        :param tr_url: The TestRail web URL to sign into. No trailing '/' needed. Provide http or https
        :param tr_user: The tr user account ot sign into
        :param tr_pass: The tr user password or API key
        """

        tr_url = os.getenv(self._ENV_URL_PARAM_NAME) if tr_url is None else tr_url
        tr_user = os.getenv(self._ENV_USER_PARAM_NAME) if tr_user is None else tr_user
        tr_pass = os.getenv(self._ENV_PASS_PARAM_NAME) if tr_pass is None else tr_pass

        if skip_login is True:
            self._initialized = True
            return

        if tr_url is None or tr_user is None or tr_pass is None:
            self._logger.error("Failed to obtain parameters to initialize TestRail API instance. Please check "
                               "the parameters and try again!")
        else:
            self._api = TestRailAPI(tr_url, tr_user, tr_pass)
            self._initialized = True

        return

    def case_data_have_error(self, case_data: dict) -> str:
        """
        Checks if a test case data dict has an error and returns the error statement
        :param case_data: The Test Case data dict
        :return: Returns the error message, if applicable, or an empty string if no error found
        """
        if 'error' in case_data:
            return case_data['error']
        else:
            return ""

    # region Section Helpers

    def get_child_sections(self, template_section_ids: list, sections_data: list) -> list:
        """

        :return:
        """
        new_sec_ids = []

        try:
            for section_id in template_section_ids:
                new_sec_ids.append(section_id)
                child_secs = self._secs_get_child_sections(int(section_id), sections_data)
                if len(child_secs) > 0:
                    new_sec_ids.extend(child_secs)

        except Exception as e:
            self._logger.exception("Exception caught when attempting to get all children sections! Exception: {0}"
                                .format(e))

        return new_sec_ids

    def _secs_get_all_descendants_of_section(self, section_id, section_lookups: dict) -> list:
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
                ret_val.extend(self._secs_get_all_descendants_of_section(sec_id, section_lookups))

        return ret_val

    def retrieve_sections_data(self, project_id: int, suite_id: int):
        """

        :param project_id:
        :param suite_id:
        :return:
        """
        try:
            sections = self.tr.sections.get_sections(project_id, suite_id=suite_id)

        except Exception as e:
            self._logger.exception("Exception caught when retrieving sections data! Exception: {0}".format(e))
            sections = []

        return sections

    def _secs_get_child_sections(self, section_id: int, sections: list) -> list:
        """
        Gets all children sections under the provided section ID or sections
        :return:
        """
        ret_val = []

        try:
            temp_lookup = {}
            for section in sections:
                parent_id = section['parent_id']
                sec_id = section['id']
                temp_lookup[sec_id] = parent_id

            ret_val.extend(self._secs_get_all_descendants_of_section(section_id, temp_lookup))

        except Exception as e:
            self._logger.exception("Exception caught when retrieving source test cases for templater! "
                                   "Exception: {0}".format(e))

        return ret_val

    # endregion Section Helpers

    # region Suite Helpers

    def suites_get_default_suite(self, tr_proj_id: int) -> int:
        """
        Get the default suite ID for a TestRail project.
        :param tr_proj_id:
        :return:
        """
        ret_val = -1

        # Assume the project is using single suite mode and grab the default suite for the project
        try:
            suites = self.tr.suites.get_suites(tr_proj_id)
            if 'error' in suites or len(suites) == 0 or 'id' not in suites[0]:
                self._logger.error("Error encountered when attempting to identify default suite ID for project ID {0}. "
                                "Error: {1}".format(tr_proj_id, suites))
            else:
                ret_val = suites[0]['id']
        except Exception as e:
            self._logger.exception("Exception encountered when attempting to retrieving default suite ID for project"
                                   "ID: {0}. Excpetion: {1}", tr_proj_id, e)

        return ret_val

    # endregion Suite Helpers

    # region Test Case Helpers

    def get_case_ids_from_case_data(self, case_data: list) -> list:
        ret_val = []

        for case in case_data:
            ret_val.append(case['id'])

        return ret_val

    def retrieve_testcase_data(self, project_id: int, suite_id: int) -> list:
        """
        Retrieves the raw test case data for the project and test case suite IDs provided
        :return: Returns list containing TestCase data, or an empty list on failure
        """
        try:
            test_case_data = self.tr.cases.get_cases(project_id, suite_id=suite_id)

        except Exception as e:
            test_case_data = []
            self._logger.exception("Exception caught when retrieving test case data from TestRail Server!"
                                "Exception: {0}".format(e))

        return test_case_data

    # endregion Test Case Helpers
