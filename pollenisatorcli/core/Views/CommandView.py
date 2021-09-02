from pollenisatorcli.core.Views.ViewElement import ViewElement
from pollenisatorcli.core.Models.Command import Command
from pollenisatorcli.core.Controllers.CommandController import CommandController
from pollenisatorcli.core.Parameters.parameter import Parameter, BoolParameter, IntParameter, ListParameter, HiddenParameter, ComboParameter
from terminaltables import AsciiTable
from pollenisatorcli.core.settings import Settings
import re
from pollenisatorcli.utils.utils import command, cls_commands
name = "Command" # Used in command decorator

@cls_commands
class CommandView(ViewElement):
    name = "command"
    def __init__(self, controller, parent_context, prompt_session, **kwargs):
        super().__init__(controller, parent_context, prompt_session, **kwargs)
        self.fields = [
            Parameter("name",  required=True, readonly=self.controller.model.name != "", default=self.controller.model.name,
                      helper="The command name"),
            ComboParameter("level", Command.possible_lvls, required = True, readonly=self.controller.model.lvl != "", default=self.controller.model.lvl, helper="Granularity of the command (will be launched on those objects)"),
            Parameter("commandline_options", default=self.controller.model.text, required=True, helper="The command line options example: -p 443"),
            ListParameter("types", default=self.controller.model.types, validator=self.validatePentestType,
                      completor=self.getPentestTypes, helper="A comma separated list of pentest types defined in the global settings. When a pentest is created with a type matching one in list, this command will be added automatically"),
            Parameter("ports/services", default=self.controller.model.ports, helper="Only used when level is Port. Comma separated values. This command will be added to every port matching an element on this list.\n each value should <port_number|service_name|port-range>[/tcp|/udp]. If no protocol is specified, tcp will be used"),
            BoolParameter("safe", default=self.controller.model.safe, helper="[true, false] If true, this command wil be lauched in an autoscan, otherwise a user will have to launch it manually"),
            IntParameter("timeout", default=self.controller.model.timeout, helper="Set a time limit to a command execution (in seconds)"),
            IntParameter("priority", default=self.controller.model.priority, helper="Priority of this command compared to others. 0 = highest priority"),
            IntParameter("threads", default=self.controller.model.max_thread, helper="Set a maximum of parallele execution of this command for ONE worker"),
            ListParameter("tags", default=self.controller.model.tags, validator=self.validateTag, completor=self.getTags, helper="Tag set in settings to help mark a content with a caracteristic"),
            HiddenParameter("indb", default=self.controller.model.indb)
        ]
        

    @classmethod
    def print_info(cls, commands):
        if commands:
            table_data = [['Name', 'Options', 'Level', 'Priority', 'Safe', 'Max Threads']]
            for command in commands:
                if isinstance(command, dict):
                    command = Command(command)
                if isinstance(command, CommandController):
                    command = command.model
                table_data.append([command.name, command.text, str(command.lvl), str(command.priority), str(command.safe), str(command.max_thread)])
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

    def validatePentestType(self, value, field):
        pentest_types = Settings.getPentestTypes().keys()
        if value.strip() not in pentest_types:
            return f"{value} is not a validate pentest type, edit settings or choose an existing one ({', '.join(pentest_types)})."
        return ""

    

    def getPentestTypes(self, args, _cmd):
        ret = []
        pentest_types = list(Settings.getPentestTypes().keys())
        for pentest_type in pentest_types:
            if pentest_type.startswith(args[-1]):
                ret.append(pentest_type+",")
        return ret

    