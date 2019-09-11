import uuid
from tr_interface import TestRailInterface


class TemplaterArgs:
    def __init__(self):
        return


class TestRailTemplater:
    """

    """

    _END_TEMPLATE_MARKER = "!ENDTEMPLATE!"
    """ 
    This is the string identifier that designates where the template system should stop 'templating' and 
    leave the original data. For example if a string field contains "Hello! '_END_TEMPLATE_MARKER' Goodbye!"
    And Hello! is updated to Hiya! via template the new string would be "Hiya! '_END_TEMPLATE_MARKER' Goodbye!"
    
    This end tag also works for Steps field types. If a steps 'content' section contains '_END_TEMPLATE_MARKER' 
    all steps following that step will NOT be erased/updated during the template process.
    """

    def __init__(self, arg_parse_inst, tr_instance, section_ids_csv, template_fields_csv, template_id_field,
                 end_marker_override=None, dry_run=False):
        """

        :param arg_parse_inst: An instance of the arg parse class to properly parse the parameters for the template
        system
        :param tr_instance: An initialized instance of the TestRail API interface
        :param dry_run:
        """
        return