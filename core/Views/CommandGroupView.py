from core.Views.ViewElement import ViewElement
from core.Models.CommandGroup import CommandGroup
from core.Models.Command import Command
from core.Controllers.CommandGroupController import CommandGroupController
from core.Parameters.parameter import Parameter, ListParameter, IntParameter
from terminaltables import AsciiTable
from utils.utils import command, cls_commands

@cls_commands
class CommandGroupView(ViewElement):
    name = "command_group"
    def __init__(self, controller, parent_context, prompt_session, **kwargs):
        super().__init__(controller, parent_context, prompt_session, **kwargs)
        self.fields = [
            Parameter("name",  required=True, readonly=self.controller.model.name != "", default=self.controller.model.name,
                      helper="The group of commands name"),
            ListParameter("commands", default=self.controller.model.commands, validator=self.validateCommand, completor=self.getCommandList, helper="The command list (comma separated) in this group"),
            IntParameter("max_thread", default=self.controller.model.max_thread, helper="Set a maximum of parallele execution of this command for ONE worker"),
        ]
        

    @classmethod
    def print_info(cls, command_groups):
        if len(command_groups) >= 1:
            table_data = [['Name', 'Commands', 'Threads']]
            for command_group in command_groups:
                if isinstance(command_group, dict):
                    command_group = CommandGroup(command_group)
                if isinstance(command_group, CommandGroupController):
                    command_group = command_group.model
                table_data.append([command_group.name, command_group.commands, str(command_group.max_thread)])
                table = AsciiTable(table_data)
                table.inner_column_border = False
                table.inner_footing_row_border = False
                table.inner_heading_row_border = True
                table.inner_row_border = True
                table.outer_border = False
            print(table.table)
        else:
            #No case
            pass

    def validateCommand(self, value):
        return "" if  value in Command.getList() else f"{value} is not an existing command"
    
    def getCommandList(self, args):
        ret = []
        command_list = list(Command.getList())
        list_args = args[-1].split(",")
        for command in command_list:
            if list_args[-1].strip() == "" or command.startswith(list_args[-1].strip()):
                ret.append(command)
        for i in range(len(ret)):
            ret[i] = ",".join(args)+ret[i]
        return ret