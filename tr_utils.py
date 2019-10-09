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

import argparse
import sys
import logging
import tr_templater
import tr_gen_template_ids
import tr_interface


_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class _utils(object):
    class common_args:
        @staticmethod
        def add_secs_or_caseids(sub_parser: argparse.ArgumentParser, reqd: bool = True):
            arg_group = sub_parser.add_mutually_exclusive_group(required=reqd)
            arg_group.add_argument("-secids", "-s",
                                             help="Section IDs in CSV format to template children test cases from",
                                             type=str, default=None)
            arg_group.add_argument("-tcids", "-i", help="TestCase IDs in CSV format to template from", type=str,
                                   default=None)

        @staticmethod
        def add_inc_children_secs(sub_parser: argparse.ArgumentParser, reqd: bool = False, default: bool = False):
            sub_parser.add_argument("-incchildren", "-c",
                                          help="Include all children sections if templating by section id", type=bool,
                                          required=reqd, default=default)

        @staticmethod
        def add_template_id_field_name(sub_parser: argparse.ArgumentParser, reqd: bool = False, default: bool = None):
            sub_parser.add_argument("-tfname", "-tn", help="Template ID field name", required=reqd, type=str,
                                          default=default)

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

            # add the section Ids or case Ids choice
            _utils.common_args.add_secs_or_caseids(templater_parser)

            # add option to include section children
            _utils.common_args.add_inc_children_secs(templater_parser)

            #add template ID field arg
            _utils.common_args.add_template_id_field_name(templater_parser)

            templater_parser.add_argument("-fields", "-f", help="Field names in CSV format to template", required=True)

            templater_parser.add_argument("-markeroverride", "-mo", help="End of template marker override. Default "
            "value is: {0}".format(_utils.templater.util.get_default_end_marker()),
                                          required=False, type=str, default=None)
            return

        @staticmethod
        def execute_util(templater_params:argparse.Namespace, tr_instance:tr_interface.TestRailInterface):
            templater = _utils.templater.util(tr_instance, templater_params.trprojid, templater_params.tfname,
                                              templater_params.fields, templater_params.secids, templater_params.tcids)

            dry_run = False
            if 'dryrun' in templater_params and templater_params.dryrun is not None:
                if templater_params.dryrun.lower() == "true":
                    dry_run = True

            templater.execute_templater(dry_run)
            return

    class template_id_gen(object):
        util = tr_gen_template_ids.TemplateIDGen

        @staticmethod
        def setup_args(tr_util_subargs: argparse._SubParsersAction):
            id_gen_parser = tr_util_subargs.add_parser("templateidgen")

            # add the section Ids or case Ids choice
            _utils.common_args.add_secs_or_caseids(id_gen_parser)

            # add option to include section children
            _utils.common_args.add_inc_children_secs(id_gen_parser)

            #add template ID field arg
            _utils.common_args.add_template_id_field_name(id_gen_parser)

            id_gen_parser.add_argument("-overwrite", "-ow",
                                          help="Overwrite data found in the TemplateID field. Defaults to "
                                               "True", type=bool, required=False, default=True)

        @staticmethod
        def execute_util(template_id_gen_params:argparse.Namespace, tr_instance:tr_interface.TestRailInterface):
            template_id_gen = _utils.template_id_gen.util(tr_instance, template_id_gen_params.tfname,
                                                          template_id_gen_params.trprojid,
                                                          template_id_gen_params.trsuiteid,
                                                          template_id_gen_params.secids, template_id_gen_params.tcids)

            dry_run = False
            if 'dryrun' in template_id_gen_params and template_id_gen_params.dryrun is not None:
                if template_id_gen_params.dryrun.lower() == "true":
                    dry_run = True

            template_id_gen.execute_id_gen(dry_run)
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
    tr_utils_args.add_argument("-trurl", help="The TestRail URL to use. Recommend usage of env vars for security",
                               required=False, default=None)
    tr_utils_args.add_argument("-truser", help="The TestRail username to use. Recommend usage of env vars for security",
                               required=False, default=None)
    tr_utils_args.add_argument("-trpass", help="The TestRail password. Recommend usage of env vars for security",
                               required=False, default=None)
    tr_utils_args.add_argument("-trprojid", "-pid", help="The TestRail project ID to perform operations in.",
                               required=True)
    tr_utils_args.add_argument("-trsuiteid", "-tsid", help="The TestRail suite ID to operate in. Optional if using"
                                                           "single suite mode.",
                               required=False)
    tr_util_subargs = tr_utils_args.add_subparsers(help="Which TestRail utility to run", dest='util')

    _utils.templater.setup_args(tr_util_subargs)

    return tr_utils_args.parse_args()


def _select_and_execute_util(parsed_args) -> int:

    tri = tr_interface.TestRailInterface(parsed_args.trurl, parsed_args.truser, parsed_args.trpass)

    if tri.is_initialized is False:
        _log.error("Failed to initialize TestRail interface. Cannot continue! Exiting.")
        return 3

    if parsed_args.util == _utils.templater.__name__:
        _utils.templater.execute_util(parsed_args, tri)
        #todo error code handle
        return 0

    return 0


def main():
    parsed_args = _setup_arg_parsers()
    _select_and_execute_util(parsed_args)

    # TODO: [cf] Actual ret val
    return 0

if __name__ == '__main__':
    sys.exit(main())
