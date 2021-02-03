from utils.utils import command, cls_commands, print_formatted, print_error
from utils.utils import main_help
import sys
import os
from core.Views.Dashboard import Dashboard
from prompt_toolkit import prompt
import time
from core.apiclient import APIClient
from core.settings import Settings
from core.Models.Wave import Wave
from core.Models.Tool import Tool
from AutoScanWorker import executeCommand
from prompt_toolkit.shortcuts import ProgressBar

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
        from core.Views.ViewElement import ViewElement
        cmdArgs = " ".join(args)
        cmdName = os.path.splitext(os.path.basename(args[0]))[0]
        cmdName +="::"+str(time.time()).replace(" ","-")
        wave = Wave().initialize("Custom commands")
        wave.addInDb()
        tool = Tool()
        if isinstance(self, ViewElement):
            db_key = self.controller.model.getDbKey()
            lvl = "wave"
            if db_key.get("port", None) is not None:
                lvl = "port"
            elif db_key.get("ip", None) is not None:
                lvl = "ip"
            elif db_key.get("scope", None) is not None:
                lvl = "scope"
            tool.initialize(cmdName, db_key.get("wave", "Custom commands"), db_key.get("scope", None), db_key.get("ip", None), db_key.get("port", None), db_key.get("proto", None), lvl, text=cmdArgs, dated="None", datef="None", scanner_ip="localhost", infos={"args":" ".join(args)})
        else:
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

    @command
    def query(self, search_query):
        """Usage: query <terms[ terms...]|tag_name>

        Description : Print a list of object title matching the query

        Arguments:
            search_query: A python like condition with:
                            - condition operators (==, !=, >, < , <=, >=, not in, in, regex) 
                            - boolean logic (and, or, not)
            Search examples in match (python condition):
            type == "port"
            type == "port" and port == 443
            type == "port" and port regex "443$"
            type == "port" and (port == 80 or port == 443)
            type == "port" and port != 443
            type == "port" and port != 443 and port != 80
            type == "defect"
            type == "defect" and "Foo" in title
            type == "ip" and ip regex "[A-Za-z]"
            type == "ip" and ip regex "^1\.2"
            type == "tool" and "done" in status
            type == "tool" and "done" not in status
            type == "tool" and "ready" in status
            type == "ip" and infos.key == "ABC" 
        """
        from core.Views.CommandView import CommandView
        from core.Views.WaveView import WaveView
        from core.Views.ScopeView import ScopeView
        from core.Views.IpView import IpView
        from core.Views.PortView import PortView
        from core.Views.DefectView import DefectView
        from core.Views.ToolView import ToolView
        apiclient = APIClient.getInstance()
        if apiclient.getCurrentPentest() is None:
            print_error("Use open to connect to a pentest first")
            return
        settings = Settings()
        settings.reloadSettings()
        avail_tags = settings.getTags()
        if search_query in avail_tags:
            search_query = f"\"{search_query}\" == tags"
        results = apiclient.search(search_query)
        if results is not None:
            for types, documents in results.items():
                if types == "ports":
                    cls = PortView
                elif types == "defects":
                    cls = DefectView
                elif types == "commands":
                    cls = CommandView
                elif types == "waves":
                    cls = WaveView
                elif types == "scopes":
                    cls = ScopeView
                elif types == "ips":
                    cls = IpView
                elif types == "tools":
                    cls = ToolView
                else:
                    print_error("The given type is invalid : "+str(types))
                    return
                cls.print_info(documents)

    @command
    def upload(self, path, plugin_name):
        """Usage: upload <path/to/tool_file/or/directory> <plugin_name>

        Description: Upload the given file or all files in directory to be integrated on the server side using plugin-name
        """
        apiclient = APIClient.getInstance()
        if apiclient.getCurrentPentest() is None:
            print_error("Use open to connect to a pentest first")
            return
        files = []
        if os.path.isdir(path):
            # r=root, d=directories, f = files
            for r, _d, f in os.walk(path):
                for fil in f:
                    files.append(os.path.join(r, fil))
        else:
            files.append(path)
        # LOOP ON FOLDER FILES
        results = {}
        with ProgressBar() as pb:
            for f_i, file_path in pb(enumerate(files)):
                results = apiclient.importExistingResultFile(file_path, plugin_name)
        presResults = ""
        filesIgnored = 0
        for key, value in results.items():
            presResults += str(value) + " " + str(key)+".\n"
            if key == "Ignored":
                filesIgnored += 1
        if filesIgnored > 0:
            print_formatted(presResults, "warning")
        else:
            print_formatted(presResults, "valid")