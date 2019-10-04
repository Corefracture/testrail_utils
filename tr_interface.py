from testrail_api import TestRailAPI
import os
import logging


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

    def __init__(self, tr_url=None, tr_user=None, tr_pass=None):
        """
        Initializes the TestRailInterface. If parameters are no provided the class utilizies os.getenv to
        attempt to retrieve the parameter data from environment variables.

        See _ENV_* variables in thi class for environment variable names.

        :param tr_url: The TestRail web URL to sign into. No trailing '/' needed. Provide http or https
        :param tr_user: The tr user account ot sign into
        :param tr_pass: The tr user password or API key
        """

        tr_url = os.getenv(self._ENV_URL_PARAM_NAME) if tr_url is None else tr_url
        tr_user = os.getenv(self._ENV_USER_PARAM_NAME) if tr_user is None else tr_user
        tr_pass = os.getenv(self._ENV_PASS_PARAM_NAME) if tr_pass is None else tr_pass

        if tr_url is None or tr_user is None or tr_pass is None:
            self._logger.error("Failed to obtain parameters to initialize TestRail API instance. Please check"
                               "the parameters and try again!")
        else:
            self._api = TestRailAPI(tr_url, tr_user, tr_pass)
            self._initialized = True

        return

    def case_data_have_error(self, case_data:dict) -> str:
        """
        Checks if a test case data dict has an error and returns the error statement
        :param case_data: The Test Case data dict
        :return: Returns the error message, if applicable, or an empty string if no error found
        """
        if 'error' in case_data:
            return case_data['error']
        else:
            return ""
