from utils.utils import command, cls_commands
from utils.utils import main_help
import sys

class Module:
    def __init__(self, name, parent_context, description, prompt, completer, prompt_session):
        self.name = name
        self.parent_context = parent_context
        self.description = description
        self.prompt = prompt
        self.completer = completer
        self.prompt_session = prompt_session
        self.contexts = []
        self.current_context = None
    
    def context_switching(self, func):
        for context in self.contexts:
            if context.name == func:
                self.set_context(context)
                return True
        return False
    
    def set_context(self, context):
        self.prompt_session.message = context.prompt
        self.prompt_session.completer = context.completer
        self.current_context = context
        if self.parent_context is not None:
            self.parent_context.setCurrentContext(context)

    def setCurrentContext(self, context):
        self.current_context = context
        if self.parent_context is not None:
            self.parent_context.setCurrentContext(context)

    def getCommandHelp(self, command_help=""):
        """
        Usage : help
        Description:
            Print this help menu 
        """        
        # Command specific help
        if command_help != "":
            if command_help not in self._cmd_list:
                msg = f"Command {command_help} not found.\n"
                msg += """List of available commands :\n"""

                for x in self._cmd_list:
                    msg += f'\t{x}\n'
                return msg
            else:
                return getattr(self, command_help).__doc__
        return None

    @command
    def help(self, command_help=""):
        # Global help
        res = self.getCommandHelp(command_help)
        if res is not None:
            print(res)
            return
        msg = main_help()
        msg += f"""
{self.name} commands
=================
{self.description}
List of available commands :\n"""

        for x in self._cmd_list:
            msg += f'\t{x}\n'
        msg += f"""
For more information about any commands hit : 
        help <command name>
        """
        
        print(msg)

    @command
    def exit(self):
        """
        Returns to previous module or quit program if in main module
        """
        if self.parent_context is not None:
            self.set_context(self.parent_context)
