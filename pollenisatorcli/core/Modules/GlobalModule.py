from pollenisatorcli.core.Modules.module import Module
from pollenisatorcli.utils.utils import command, cls_commands, print_formatted, print_error
from pollenisatorcli.utils.utils import getMainDir
import sys
from pollenisatorcli.core.Views.Dashboard import Dashboard
from prompt_toolkit import prompt
import time
from pollenisatorcli.core.apiclient import APIClient
from pollenisatorcli.core.settings import Settings
from pollenisatorcli.core.Models.Wave import Wave
from pollenisatorcli.core.Models.Tool import Tool
from pollenisatorcli.AutoScanWorker import executeCommand
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document
import random
import string
import os
from shutil import which
import subprocess
from multiprocessing import Process

name = "Global"


@cls_commands
class GlobalModule(Module):
    def __init__(self, name, parent_context, description, prompt, completer, prompt_session):
        super().__init__(name, parent_context, description, prompt,  completer, prompt_session)

    
    @command
    def help(self, command_help=""):
        # Global help
        res = self.getCommandHelp(command_help)
        if res is not None:
            print_formatted(res)
            return
        self.print_command_help()
        self.print_help_footer()
        
    @command
    def exit(self):
        """
        Description : Returns to previous module or quit program if in main module
        """
        if self.parent_context is not None:
            self.set_context(self.parent_context)

    @command
    def scans(self):
        """Usage: scans
        Description : open the scan module
        """
        from pollenisatorcli.core.Modules.scans import Scans

        if APIClient.getInstance().getCurrentPentest() is not None:
            self.set_context(Scans(self, self.prompt_session))
        else:
            print_error("Use open to connect to a database first")

    @command
    def pentest_settings(self):
        """Usage: pentest_settings
        Description : open the settings of this pentest
        """
        from pollenisatorcli.core.FormModules.settingsForms import PentestSettings

        if APIClient.getInstance().getCurrentPentest() is not None:
            self.set_context(PentestSettings(self, self.prompt_session))
        else:
            print_error("Use open to connect to a database first")

    @command
    def dashboard(self):
        """Usage: dashboard
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
        """Usage: report
        Description : Generate reports with registered defects and add some manually
        """
        from pollenisatorcli.core.Modules.report import Report

        if APIClient.getInstance().getCurrentPentest() is None:
            print_error("Use open to connect to a database first")
            return
        self.set_context(Report(self, self.prompt_session))
        
    @command
    def terminal(self, trap_all=None):
        """Usage: terminal [trap_all]
        Description : Open a new terminal to execute commands"""
        apiclient = APIClient.getInstance()
        if self.proc is None:
            password = os.environ.get("POLLEX_PASS", None)
            if password is None:
                characters = string.ascii_letters + string.digits + string.punctuation
                password = ''.join(random.choice(characters) for i in range(15))
            os.environ["POLLEX_PASS"] = password
            self.proc = Process(target=self.takeCommands, args=(apiclient,))
            self.proc.daemon = True
            self.proc.start()
        settings = Settings()
        settings.reloadSettings()
        favorite = settings.getFavoriteTerm()
        if favorite is None:
            print_error("Terminal settings invalid : None of the terminals given in the settings are installed on this computer.")
            return False
        if which(favorite) is not None:
            terms = settings.getTerms()
            terms_dict = {}
            for term in terms:
                terms_dict[term.split(" ")[0]] = term
            command_term = terms_dict.get(favorite, None)
            if command_term is not None:
                if trap_all:
                    term_comm = terms_dict[favorite].replace("setupTerminalForPentest.sh", os.path.join(getMainDir(), "setupTerminalForPentest.sh"))
                else:
                    term_comm = term
                subprocess.Popen(term_comm, shell=True)
            else:
                print_error("Terminal settings invalid : Check your terminal settings")
        else:
            print_error(f"Terminal settings invalid : {favorite} terminal is not available on this computer. Choose a different one in the settings module.")
        return False


    @command
    def exec(self, *args):
        """Usage: exec <command line to another tool>
        Description: Will execute the given command line and will try to automatically import it if the binary is configured in server config/tools.d
        """
        if APIClient.getInstance().getCurrentPentest() is None:
            print_error("Use open to connect to a database first")
            return
        from pollenisatorcli.core.Views.ViewElement import ViewElement
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
            res, msg = executeCommand(APIClient.getInstance(), str(iid), "auto-detect", True)
            if not res:
                print_error(msg)
        return

    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """ 
        if cmd == "terminal":
            return ["trap_all", ""]
        elif cmd == "upload":
            return self.autoCompleteUpload(cmd_args, complete_event)
        return []

    def autoCompleteUpload(self, cmd_args, complete_event):
        """
        Returns auto complete possibilites for the "upload" cmd
        Args:
            cmd_args: the current list of arguments given to info cmd (not completed)
            complete_event: the Completer event
        """
        apiclient = APIClient.getInstance()
        if len(cmd_args) == 1:
                return (Completion(completion.text, completion.start_position, display=completion.display) 
                            for completion in self.prompt_session.path_completer.get_completions(Document(cmd_args[0]), complete_event))
        
        elif len(cmd_args) == 2:
            plugins = apiclient.listPlugins()+["auto-detect"]
            ret = [x for x in plugins if x.startswith(cmd_args[1])]
            return ret
        return []

    @command
    def query(self, *args):
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
        from pollenisatorcli.core.Views.CommandView import CommandView
        from pollenisatorcli.core.Views.WaveView import WaveView
        from pollenisatorcli.core.Views.ScopeView import ScopeView
        from pollenisatorcli.core.Views.IpView import IpView
        from pollenisatorcli.core.Views.PortView import PortView
        from pollenisatorcli.core.Views.DefectView import DefectView
        from pollenisatorcli.core.Views.ToolView import ToolView
        search_query = " ".join(args)
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