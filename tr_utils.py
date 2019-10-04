import argparse
import sys
import logging
import tr_templater
import tr_interface


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class _utils(object):
    class templater(object):
        util = tr_templater.TestRailTemplater

        @staticmethod
        def setup_args(tr_util_subargs:argparse._SubParsersAction):
            """
            Defines the parameters for use with the templater utility

            :param tr_util_subargs: The sub parser generated from the main instance of argparser
            :return:
            """
            templater_parser = tr_util_subargs.add_parser("templater")

            templater_arg_group = templater_parser.add_mutually_exclusive_group(required=True)
            templater_arg_group.add_argument("-secids", "-s",
                                             help="Section IDs in CSV format to template children test cases from",
                                             type=str)
            templater_arg_group.add_argument("-tcids", "-i", help="TestCase IDs in CSV format to template from", type=str)

            templater_parser.add_argument("-incchildren", "-c",
                                          help="Include all children sections if templating by section id", type=bool,
                                          required=False, default=False)
            templater_parser.add_argument("-fields", "-f", help="Field names in CSV format to template", required=True)
            templater_parser.add_argument("-tfname", "-tn", help="Template ID field name", required=False, type=str,
                                          default=None)
            templater_parser.add_argument("-markeroverride", "-mo", help="End of template marker override. Default "
            "value is: {0}".format(_utils.templater.util.get_default_end_marker()),
                                          required=False, type=str, default=None)

            return


        @staticmethod
        def execute_util(templater_params:argparse.Namespace, tr_instance:tr_interface.TestRailInterface):
            templater = _utils.templater.util(tr_instance, templater_params.trprojid, templater_params.tfname,
                                              templater_params.fields, templater_params.secids)

            dry_run = False
            if 'dryrun' in templater_params and templater_params.dryrun is not None:
                if templater_params.dryrun.lower() == "true":
                    dry_run = True

            templater.execute_templater(dry_run)
            return




def setup_templateid_gen_args(tr_util_subargs:argparse._SubParsersAction):
    """

    :param tr_util_subargs:
    :return:
    """

    return


def _setup_arg_parsers() -> argparse.Namespace:
    tr_utils_args = argparse.ArgumentParser()
    tr_utils_args.add_argument("-dryrun", help="Execute a dry run without writing and changes to TestRail",
                               required=False)
    tr_utils_args.add_argument("-trprojid", "-pid", help="The TestRail project ID to perform operations in.",
                               required=True)
    tr_utils_args.add_argument("-trsuiteid", "-tsid", help="The TestRail suite ID to operate in. Optional if using"
                                                           "single suite mode.",
                               required=False)
    tr_util_subargs = tr_utils_args.add_subparsers(help="Which TestRail utility to run", dest='util')

    _utils.templater.setup_args(tr_util_subargs)

    return tr_utils_args.parse_args()


def _select_and_execute_util(parsed_args) -> int:

    #todo TR instance

    if parsed_args.util == _utils.templater.__name__:
        _utils.templater.execute_util(parsed_args, tri)
        return 0

    return 0


def main():
    parsed_args = _setup_arg_parsers()

    _select_and_execute_util(parsed_args)

    #todo: [cec] Actual ret val
    return 0

if __name__ == '__main__':
    sys.exit(main())
