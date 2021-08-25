from pollenisatorcli.core.Views.ViewElement import ViewElement
from pollenisatorcli.core.Models.CommandGroup import CommandGroup
from pollenisatorcli.core.Models.Command import Command
from pollenisatorcli.core.Controllers.CommandGroupController import CommandGroupController
from pollenisatorcli.core.Parameters.parameter import Parameter, ListParameter, IntParameter
from terminaltables import AsciiTable
from pollenisatorcli.utils.utils import command, cls_commands, style_table, print_formatted_text
from prompt_toolkit import ANSI

name = "Command Group" # Used in command decorator

@cls_commands
class CommandGroupView(ViewElement):
    name = "command_group"
    def __init__(self, controller, parent_context, prompt_session, **kwargs):
        super().__init__(controller, parent_context, prompt_session, **kwargs)
        self.fields = [
            Parameter("name",  required=True, readonly=self.controller.model.name != "", default=self.controller.model.name,
                      helper="The group of commands name"),
            ListParameter("commands", default=self.controller.model.commands, validator=self.validatorCommand, completor=self.getCommandList, helper="The command list (comma separated) in this group"),
            IntParameter("max_thread", default=self.controller.model.max_thread, helper="Set a maximum of parallele execution of this command for ONE worker"),
        ]
        

    @classmethod
    def print_info(cls, command_groups):
        if command_groups:
            table_data = [['Name', 'Commands', 'Threads']]
            for command_group in command_groups:
                if isinstance(command_group, dict):
                    command_group = CommandGroup(command_group)
                if isinstance(command_group, CommandGroupController):
                    command_group = command_group.model
                table_data.append([command_group.name, command_group.commands, str(command_group.max_thread)])
                table = AsciiTable(table_data)
                table = style_table(table)
            print_formatted_text(ANSI(table.table+"\n"))
        else:
            #No case
            pass

    def validatorCommand(self, value, field):
        return "" if  value in Command.getList() else f"{value} is not an existing command"
    
    def getCommandList(self, args, _cmd):
        ret = []
        command_list = list(Command.getList())
        list_args = args[-1].split(",")
        for command in command_list:
            if list_args[-1].strip() == "" or command.startswith(list_args[-1].strip()):
                ret.append(command)
        for i in range(len(ret)):
            ret[i] = ",".join(args)+ret[i]
        return ret