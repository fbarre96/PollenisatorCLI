from pollenisatorcli.core.Views.ViewElement import ViewElement
from terminaltables import AsciiTable
from pollenisatorcli.core.apiclient import APIClient
from pollenisatorcli.utils.utils import command, cls_commands, print_formatted_text, print_formatted, print_formatted, print_error
from pollenisatorcli.core.Parameters.parameter import Parameter, BoolParameter, IntParameter, ListParameter, HiddenParameter, ComboParameter, ListParameter
from pollenisatorcli.core.Models.Command import Command
from pollenisatorcli.core.Models.Worker import Worker

@cls_commands
class WorkerView(ViewElement):
    name = "worker"
    def __init__(self, controller, parent_context, prompt_session, **kwargs):
        super().__init__(controller, parent_context, prompt_session, **kwargs)
        apiclient = APIClient.getInstance()
        self.fields = [
            Parameter("name", readonly=True, required = True,  default=self.controller.model.name, helper="Worker name"),
            BoolParameter("excluded", readonly=True, required = True,  default=apiclient.getCurrentPentest() in self.controller.model.excludedDatabases, helper="Worker will not work for any of them"),   
            ListParameter("registeredCommands", readonly=True, required = True,  default=self.controller.model.registeredCommands, helper="The commands that this worker knows how to launch"),   
        ]

    @classmethod
    def print_info(cls, workers):
        registeredCommands = []
        apiclient = APIClient.getInstance()
        
        if len(workers) >= 1:
            table_data = [['Name', 'excluded', 'registered commands', ]]
            for worker in workers:
                if isinstance(worker, dict):
                    worker = Worker(worker)
                table_data.append([worker.name, apiclient.getCurrentPentest() in worker.excludedDatabases, ", ".join(worker.registeredCommands)])
                registeredCommands += worker.registeredCommands
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
        not_registered = []
        allCommands = Command.getList(None, apiclient.getCurrentPentest())
        for command in allCommands:
            if command not in registeredCommands:
                not_registered.append(str(command))
        print_formatted(f"Those commands are not registered by any worker:\n {chr(10).join(not_registered)}","warning")

    @command
    def set_exclusion(self):
        """Usage: set_exclusion
        Description: Will change the exclusion setting of this worker for this pentest
        """
        apiclient = APIClient.getInstance()
        isExcluded = apiclient.getCurrentPentest() in self.controller.model.excludedDatabases
        apiclient.setWorkerExclusion(self.controller.model.name, not (isExcluded))
        isExcluded = not isExcluded
        if isExcluded and apiclient.getCurrentPentest() not in self.controller.model.excludedDatabases:
            self.controller.model.excludedDatabases.append(apiclient.getCurrentPentest())
        else:
            if apiclient.getCurrentPentest() in self.controller.model.excludedDatabases:
                self.controller.model.excludedDatabases.remove(apiclient.getCurrentPentest())
        for field in self.fields:
            if field.name == "excluded":
                field.value = str(apiclient.getCurrentPentest() in self.controller.model.excludedDatabases).lower()

    @command
    def set_command_config(self, commandname, remote_bin_path, plugin):
        """Usage: set_command_config <commandname> <remote_bin_path> <plugin>
        Description: Will change the command settings in the given worker, resulting in him registering it
        Args:
            commandname : the commandname you want to configure inside this worker
            remote_bin_path: the remote path leading to the tool binary/script
            plugin: the plugin to associate with this command
        """
        apiclient = APIClient.getInstance()
        if commandname not in Command.getList():
            print_error(f"{commandname} is not a valid command")
            return
        if plugin not in apiclient.listPlugins():
            print_error(f"{plugin} is not a valid plugin")
            return
        apiclient.sendEditToolConfig(self.controller.model.name, commandname, remote_bin_path, plugin)

    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """  
        
        if cmd == "set_command_config":
            if len(cmd_args) == 1:
                return Command.getList()
            elif len(cmd_args) == 2:
                return []
            elif len(cmd_args) == 3:
                return APIClient.getInstance().listPlugins()
        ret = super().getOptionsForCmd(cmd, cmd_args, complete_event)
        if ret:
            return ret
        return []