from pollenisatorcli.core.Views.ViewElement import ViewElement
from pollenisatorcli.core.Views.DefectView import DefectView
from terminaltables import AsciiTable
from colorclass import Color
from pollenisatorcli.utils.utils import dateToString
from pollenisatorcli.core.Models.Command import Command
from pollenisatorcli.core.Models.Tool import Tool
from pollenisatorcli.core.Models.Port import Port
from pollenisatorcli.core.Models.Defect import Defect
from pollenisatorcli.core.Controllers.ToolController import ToolController
from pollenisatorcli.core.Controllers.DefectController import DefectController
from pollenisatorcli.core.Parameters.parameter import Parameter, DateParameter, ComboParameter, ListParameter
from pollenisatorcli.core.apiclient import APIClient
from pollenisatorcli.utils.utils import command, cls_commands, print_error, print_formatted_text, print_formatted, execute, style_table
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit import prompt
import os
from shutil import which
import webbrowser
from prompt_toolkit import ANSI
name = "Tool" # Used in command decorator


@cls_commands
class ToolView(ViewElement):
    name = "tool"
    children_object_types = {"defects":{"view":DefectView, "controller":DefectController, "model":Defect}}
    def __init__(self, controller, parent_context, prompt_session, **kwargs):
        super().__init__(controller, parent_context, prompt_session, **kwargs)
        if self.controller.model.port != "":
            self.controller.model.lvl = "port"
        elif self.controller.model.ip != "":
            self.controller.model.lvl = "ip"
        elif self.controller.model.scope != "":
            self.controller.model.lvl = "scope"
        else:
            self.controller.model.lvl = "wave"
        if self.controller.model.lvl in ["port", "ip"] and "done" in self.controller.getStatus():
            self.__class__._cmd_list.append("browser")
        command_list = Command.fetchObjects({"lvl": self.controller.model.lvl}, APIClient.getInstance().getCurrentPentest())
        command_names = ["None"]
        for command_doc in command_list:
            command_names.append(command_doc.name)
        apiclient = APIClient.getInstance()
        wave_list = apiclient.find("waves", {})
        wave_names = []
        for wave in wave_list:
            wave_names.append(wave)
        self.fields = [
            Parameter("Detail",  default=self.controller.model.getDetailedString(), required=True, readonly=True,
                      helper="The parent this tool is assigned to"),
            ComboParameter("name", command_names, default=self.controller.model.name, readonly=self.controller.model.name != "", required=True, helper="The command name this tool matches"),
            ComboParameter("wave", wave_names, default=self.controller.model.name, readonly=self.controller.model.wave != "", required=True, helper="The wave name this tool is assigned to"),
            Parameter("text", default=self.controller.model.text, readonly=True, helper="The command launched using this tool"),
            DateParameter("start",  required=True, default=self.controller.model.dated,
                      helper="The datetime of start of execution for this tool"),        
            DateParameter("end",  required=True, default=self.controller.model.datef,
                      helper="The ending datetime  of execution for this tool"),    
            Parameter("scanner_ip", default=self.controller.model.scanner_ip,  helper="The host that launched this tool"),
            Parameter("resultfile", readonly=True, default=self.controller.model.resultfile,  helper="The result file associated with this tool"),
            Parameter("status", readonly=True, default=self.controller.model.getStatus(), helper="The status of this tool"),
            Parameter("notes", default=self.controller.model.notes, helper="A space to take notes. Will appear in word report"),
            ListParameter("tags", default=self.controller.model.tags, validator=self.validateTag, completor=self.getTags, helper="Tag set in settings to help mark a content with a caracteristic"),
        ]

    @command
    def launch(self, local=None):
        """Usage: launch ["local"]

        Args:
            local: if local is given, the tool will be executed from this computer (the executor must have it in its local config toolds.d folder) 

        Description: Order execution of this tool 
        """

        status = self.controller.getStatus()
        if "done" in status:
            print_error("This tool is already done")
        elif "running" in status:
            print_error("This tool is already running")
        else:
            if local == "local":
                self.localLaunchCallback()
            else:
                self.safeLaunchCallback()


    def safeLaunchCallback(self, _event=None):
        """
        Callback for the launch tool button. Will queue this tool to a worker.
        Args:
            event: Automatically generated with a button Callback, not used.
        Returns:
            None if failed. 
        """
        apiclient = APIClient.getInstance()
        return apiclient.sendLaunchTask(self.controller.model.getId()) is not None

    def launchCallback(self, _event=None):
        """
        Callback for the launch tool button. Will queue this tool to a worker. #TODO move to ToolController
        Will try to launch respecting limits first. If it does not work, it will asks the user to force launch.

        Args:
            _event: Automatically generated with a button Callback, not used.
        """
        res = self.safeLaunchCallback()
        if not res:
            msg = FormattedText([("class:warning", "WARNING : Safe queue failed"), ("class:normal", f" This tool cannot be launched because no worker add space for its thread.\nDo you want to launch it anyway?")])
            print_formatted_text(msg)
            result = prompt('yes/no? ')
            if result.lower() == "yes":
                apiclient = APIClient.getInstance()
                apiclient.sendLaunchTask(self.controller.model.getId())
        else:
            self.updatePrompt()
    
    def localLaunchCallback(self):
        """
        Callback for the launch tool button. Will launch it on localhost pseudo 'worker'.  #TODO move to ToolController

        Args:
            event: Automatically generated with a button Callback, not used.
        """
        self.controller.model.launch()
        self.updatePrompt()

    @command
    def reset(self):
        """Usage: reset 

        Description: Reset the results of this tool if the tool is done only
        """
        status = self.controller.getStatus()
        if "done" in status:
            self.controller.markAsNotDone()
            self.updatePrompt()
        else:
            print_error("This tool is not done, it cannot be reset")
        

    @command
    def stop(self):
        """Usage: stop 

        Description: stop the exection of this tool if the tool is running only
        """
        status = self.controller.getStatus()
        if "running" in status:
            apiclient = APIClient.getInstance()
            success = apiclient.sendStopTask(self.controller.model.getId())
            delete_anyway = False
            if success == False:
                print_error("Stop failed. This tool cannot be stopped because its trace has been lost (The application has been restarted and the tool is still not finished).\nReset tool anyway?")
                delete_anyway = prompt("yes/no?")
                delete_anyway = delete_anyway.lower() == "yes"
            if delete_anyway:
                success = apiclient.sendStopTask(self.controller.model.getId(), True)
            if success:
                self.updatePrompt()
        else:
            print_error("This tool is not running, it cannot be stopped")

    @command
    def view(self):
        """Usage: view 

        Description: Download and tries to open the result file. Only if the tool is done. tries to open it using xdg-open or os.startsfile
        """
        abs_path = os.path.dirname(os.path.abspath(__file__))
        outputDir = os.path.join(abs_path, "../../results")
        apiclient = APIClient.getInstance()
        path = self.controller.getOutputDir(apiclient.getCurrentPentest())
        with ProgressBar() as pb:
            for i in pb(range(1)):
                path = apiclient.getResult(self.controller.getDbId(), os.path.join(outputDir,path, str(self.controller.model)))
        
        if path is not None:
            if os.path.isfile(path):
                if which("xdg-open") is not None:
                    print_formatted("Download completed : Would you like to open it?")
                    answer = prompt("yes/no? ")
                    if answer.lower() == "yes":
                        execute("xdg-open "+path)
                        return
                    else:
                        return
            path = None
        if path is None:
            print_error("Download failed: the file does not exist on the server")

    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """  
        ret = super().getOptionsForCmd(cmd, cmd_args, complete_event)
        if ret:
            return ret
        if cmd == "launch":
            return ["","local"]
        return []

    @classmethod
    def print_info(cls, tools):
        if tools:
            table_data = [['Name', 'Assigned', 'Status', 'Started at', 'Ended at']]
            for tool in tools:
                if isinstance(tool, dict):
                    tool = Tool(tool)
                if isinstance(tool, ToolController):
                    tool = tool.model
                title_str = ViewElement.colorWithTags(tool.getTags(), tool.name)
                status_colors = {"done":"green", "running":"blue", "ready":"yellow", "":"red"}
                status = tool.getStatus()
                if status:
                    status = status[0]
                else:
                    status = ""
                status_color = status_colors.get(status, None)
                if status_color is not None:
                    status_str = Color("{"+status_colors[status]+"}"+status+"{/"+status_colors[status]+"}")
                else:
                    status_str = status
                assigned_str = tool.getDetailedString()
                table_data.append([title_str, assigned_str, status_str, tool.dated, tool.datef])
            table = AsciiTable(table_data)
            table = style_table(table)
            print_formatted_text(ANSI(table.table+"\n"))
        else:
            #No case
            print("No information to display")
            pass
    
    def browser(self):
        """Usage: browser
        Description: open the ip:port in a web browser
        """
        if self.controller.model.lvl == "ip":
            webbrowser.open_new_tab(self.controller.model.ip)
        elif self.controller.model.lvl == "port":
            port_m = Port.fetchObject({"ip":self.controller.model.ip, "port":self.controller.model.port, "proto":self.controller.model.proto})
            ssl = port_m.infos.get("SSL", None) == "True" or ("https" in port_m.service or "ssl" in port_m.service)
            url = "https://" if ssl else "http://"
            url += port_m.ip+":"+str(port_m.port)+"/"
            webbrowser.open_new_tab(url)