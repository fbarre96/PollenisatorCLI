from pollenisatorcli.utils.utils import command, cls_commands, print_error, print_formatted, print_formatted_text
from pollenisatorcli.utils.completer import IMCompleter
from pollenisatorcli.core.Modules.GlobalModule import GlobalModule
from pollenisatorcli.core.apiclient import APIClient
from prompt_toolkit.formatted_text import FormattedText
name = "Scripts" # Used in command decorator


@cls_commands
class ScriptsModule(GlobalModule):
    def __init__(self, parent_context, prompt_session):
        super().__init__('Scripts', parent_context, "Scripts manager", FormattedText([('class:title', "Scripts"),('class:angled_bracket', " > ")]), IMCompleter(self), prompt_session)

   
    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """  
        return []
