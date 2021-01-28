from utils.utils import command, cls_commands, print_formatted, print_error
from utils.utils import main_help
import sys
import os
from core.Views.Dashboard import Dashboard
from prompt_toolkit import prompt
import time
from core.apiclient import APIClient
from core.Models.Wave import Wave
from core.Models.Tool import Tool
from AutoScanWorker import executeCommand


@cls_commands
class Module:
    def __init__(self, name, parent_context, description, prompt, completer, prompt_session):
        self.name = name
        self.parent_context = parent_context
        self.description = description
        self.prompt = prompt
        self.completer = completer
        self.prompt_session = prompt_session
        self.contexts = {}
        self.current_context = None
    
    def context_switching(self, func):
        if func in self.contexts.keys():
            self.set_context(self.contexts[func])
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
        """Usage : help
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
            print_formatted(res)
            return
        msg = main_help()
        msg += f"""
{self.name} commands
=================
{self.description}
List of available commands :"""
        print_formatted(msg)
        for x in self._cmd_list:
            print_formatted(f'\t{x}', 'command')
        print_formatted("For more information about any commands hit :")
        print_formatted("help <command>", "cmd")
        

    @command
    def exit(self):
        """
        Returns to previous module or quit program if in main module
        """
        if self.parent_context is not None:
            self.set_context(self.parent_context)

    @command
    def scans(self):
        """Usage : scans
        Description : open the scan module
        """
        from core.Modules.scans import Scans

        if APIClient.getInstance().getCurrentPentest() is not None:
            self.set_context(Scans(self, self.prompt_session))
        else:
            print_error("Use open to connect to a database first")

    @command
    def pentest_settings(self):
        """Usage : pentest_settings
        Description : open the settings of this pentest
        """
        from core.FormModules.settingsForms import PentestSettings

        if APIClient.getInstance().getCurrentPentest() is not None:
            self.set_context(PentestSettings(self, self.prompt_session))
        else:
            print_error("Use open to connect to a database first")

    @command
    def dashboard(self):
        """Usage : dashboard
        Description : print dahsboards for this pentest
        """
        if APIClient.getInstance().getCurrentPentest() is None:
            print_error("Use open to connect to a database first")
            return
        dashboards = {"Services per hosts":Dashboard.printServicesPerHosts,
                      "Top ports": Dashboard.printTopPorts,
                      "Tools state": Dashboard.printToolsState}
        response = None
        while response != 0:
            print_formatted("Choose a dashboard to open:")
            for i,dashboard in enumerate(dashboards.keys()):
                print_formatted(f"{i+1}. {dashboard}")
            print_formatted("0. exit")
            response = prompt("Choice : ")
            try:
                response = int(response)
                if response > len(dashboards):
                    response = None
            except ValueError:
                response = None
            if response is not None:
                if response-1 >= 0 and response-1 < len(dashboards.keys()):
                    dashboards[list(dashboards.keys())[response-1]]()
    
    @command
    def report(self):
        """Usage : report
        Description : Generate reports with registered defects and add some manually
        """
        from core.Modules.report import Report

        if APIClient.getInstance().getCurrentPentest() is None:
            print_error("Use open to connect to a database first")
            return
        self.set_context(Report(self, self.prompt_session))
        

    @command
    def exec(self, *args):
        """Usage: exec <command line to another tool>
        Description: Will execute the given command line and will try to automatically import it if the binary is configured in server config/tools.d
        """
        if APIClient.getInstance().getCurrentPentest() is None:
            print_error("Use open to connect to a database first")
            return
        cmdArgs = " ".join(args)
        cmdName = os.path.splitext(os.path.basename(args[0]))[0]
        cmdName +="::"+str(time.time()).replace(" ","-")
        wave = Wave().initialize("Custom commands")
        wave.addInDb()
        tool = Tool()
        tool.initialize(cmdName, "Custom commands", None, None, None, None, "wave", text=cmdArgs, dated="None", datef="None", scanner_ip="localhost", infos={"args":" ".join(args)})
        res, iid = tool.addInDb()
        if res:
            res, msg = executeCommand(APIClient.getInstance().getCurrentPentest(), str(iid), "auto-detect")
            if not res:
                print_error(msg)
        return

    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """ 
        return []