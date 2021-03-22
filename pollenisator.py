#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Usage description for docopt
"""
Pollenisator
Usage: 
    pollenisator.py [--host host] [--port port] 

Options: 
    -h, --help                           Show this help menu.
    -v, --version                        Show version.
    --host                               API server IP. If not provided, the configuration file will be used. If provided, will update configuration file.  
    --port, -p                           API listening port. If not provided, the configuration file will be used. If provided, will update configuration file. 
"""
"""
@author: Fabien Barré for AlgoSecure
# Date: 16/12/2020
# Major version released: 01/2021
# @version: 1.0
"""
import sys
from datetime import datetime
from shlex import split
import asyncio
from docopt import DocoptExit, docopt
from prompt_toolkit import PromptSession
from prompt_toolkit import prompt
from prompt_toolkit import print_formatted_text
#from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import PathCompleter, WordCompleter, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.patch_stdout import patch_stdout
from core.apiclient import APIClient
from core.FormModules.newPentestForm import NewPentestForm
from core.FormModules.settingsForms import PollenisatorSettings
from core.Modules.module import Module
from core.Modules.pentest import Pentest
from core.Modules.commandtemplate import CommandTemplate
from utils.completer import IMCompleter
from utils.utils import (CmdError, cls_commands, command,
                         getClientConfigFilePath, loadCfg, main_help,
                         print_error, print_formatted, saveCfg, style)

from colorclass import Windows

@cls_commands
class Pollenisator(Module):
    def __init__(self):
        args = docopt(__doc__, version=version)
        client_config = loadCfg(getClientConfigFilePath())
        if args["host"]:
            client_config["host"] = args["host"]
        if args["port"]:
            client_config["port"] = args["ports"]
        saveCfg(client_config, getClientConfigFilePath())
        apiclient = APIClient.getInstance()
        if not apiclient.tryConnection():
            print_error("Could not connect to server. Use --host and --port option.")
            return
        rightLogin = False
        print_formatted("Connecting to http://"+str(client_config["host"]+":"+str(client_config["port"])))
        while not rightLogin:
            login = prompt("Username :", is_password=False)
            pwd = prompt("Password :", is_password=True)
            rightLogin = apiclient.login(login, pwd)
            if not rightLogin:
                print_error("Invalid username or password")

        self.prompt_session = PromptSession(
            "Pollenisator #",
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            complete_in_thread=True,
            complete_while_typing=True,
            style=style
        )
        self.prompt_session.path_completer = PathCompleter()

        super().__init__("Pollenisator", None, "Main Menu", FormattedText([('class:title', "Pollenisator"),('class:angled_bracket', " > ")]), IMCompleter(self), self.prompt_session)

        self.contexts = {
            "pentest": Pentest(self, self.prompt_session),
            "new pentest": NewPentestForm(self, self.prompt_session),
            "command_templates": CommandTemplate(self, self.prompt_session),
            "global_settings": PollenisatorSettings(self, self.prompt_session),
        }

        
        # Start in main module (this one)
        self.set_context(self)
        
    def parse_result(self, result):
        if len(result):
            if not self.context_switching(result):
                command = split(result)
                if not command:
                    return
                try:
                    # check if command first args is in current context
                    func_to_call = getattr(self.current_context, command[0], None)
                    if callable(func_to_call): # run it with the remaining args 
                        func_to_call(*command[1:])
                    else:  # check if a default exist and call it with all args
                        default_func_to_call = getattr(self.current_context, "cmd_default", None)
                        if callable(default_func_to_call):
                            default_func_to_call(*command[0:])
                        else:
                            print_error(f"The given commmand '{command[0]}' does not exist in this module.\nType 'help' to get the list of currently available commands\n")
                except TypeError as e:
                    print_error(f"Error type")
                    print(e)
                except SystemExit:
                    pass

    def main_loop(self):
        while True:
            with patch_stdout():
                try:
                    result = self.prompt_session.prompt(style=style, is_password=False)
                    if (self.current_context == self and result.strip().lower() == "exit"):
                        break
                    self.parse_result(result)
                except KeyboardInterrupt:
                    print_formatted_text("CTRL^C")
                    break

    @command
    def ls(self):
        """Usage : ls
        
        Description : ls existings pentests
        """  
        apiclient = APIClient.getInstance()
        pentests = "\n".join(apiclient.getPentestList())
        print_formatted(f"Pentests:\n==========\n{pentests}", "important")

    @command
    def command_templates(self):
        """Usage : command_templates 
        
        Description : Open the submodule to edit command templates for every pentest
        """
        self.set_context(self.contexts["command_templates"])
    @command
    def global_settings(self):
        """Usage : settings 
        
        Description : Open the pollensiator  glboal settings module
        """
        self.set_context(self.contexts["settings"])
    
    @command
    def open(self, pentest_name):
        """Usage : open <pentest_name>
        
        Description : Open the given database name and get the CLI in pentesting mode.

        Args:
            pentest_name  the pentest database name to load in application. 
        """  
        apiclient = APIClient.getInstance()
        if pentest_name not in apiclient.getPentestList():
            print_error("This pentest does not exist. Create it or choose one in the list below.")
            self.ls()
            return
        apiclient.setCurrentPentest(pentest_name)
        self.contexts["pentest"].prompt = FormattedText([('class:title',f"{self.current_context.name}"),("class:subtitle", f" {pentest_name}"), ("class:angled_bracket", " > ")])
        self.set_context(self.contexts["pentest"])
    @command
    def new(self):
        """Usage : new
        
        Description : Start the pentest creation wizard
        """ 
        self.set_context(self.contexts["new pentest"])

    @command
    def delete(self, pentest_name):
        """Usage : delete <pentest_name>
        
        Description : Delete the pentest given a pentest name
        """ 
        apiclient = APIClient.getInstance()
        msg = FormattedText([("class:warning", "WARNING :"), ("class:normal", f" You are going to delete {pentest_name}"), (
            "#ff0000", " permanently.")])
        print_formatted_text(msg)
        result = prompt('Confirm deletion ? No/yes > ')
        if result.lower() == "yes":
            res = apiclient.doDeletePentest(pentest_name)
            if res is None:
                print_error(f"Could not delete pentest {pentest_name}")
            elif not res:
                print_error(f"Could not found pentest {pentest_name}")
            else:
                print_formatted(f"Successfully deleted {pentest_name}", "valid")

    @command
    def duplicate(self, from_pentest, to_pentest):
        """Usage : duplicate <pentest_name> <to_pentest>

        Description : Duplicate the given pentest to a new database
        Arguments:
            from_pentest: the pentest name to duplicate 
            to_pentest: a name for the new pentest
        """
        apiclient = APIClient.getInstance()
        res = apiclient.copyDb(from_pentest, to_pentest)
        if res is None:
            print_error("API call failed, undefined error. Check server for more info")
        else:
            print_formatted(f"{to_pentest} successfully created", "valid")

    @command
    def export(self, pentest_or_command, pentest_name=None):
        """Usage: export pentest|commands <pentest_name>
        
        Description : Export a pentest database or the command database.

        Arguments:
            pentest_or_command: Either "pentest" or "commands". Choose if you want to export the command database or a pentest database. 
            pentest_name: if "pentest" is given as 1st arg, the pentest name to export
        """
        apiclient = APIClient.getInstance()
        if pentest_or_command == "pentest":
            if pentest_name is None:
                print_error("pentest was specified but no pentest name was given.")
                return            
            success, msg = apiclient.dumpDb(pentest_name)
            if not success:
                print_error(msg)
            else:
                print_formatted(f"Pentest successully exported : {msg}", "valid")
        elif pentest_or_command == "commands":
            success, msg = apiclient.dumpDb("pollenisator", "commands")
            if not success:
                print_error(msg)
                return
            success, msg = apiclient.dumpDb("pollenisator", "group_commands")
            if not success:
                print_error(msg)
                return
            print_formatted("Export completed in exports/pollenisator_commands.gz and exports/pollenisator_group_commands.gz", "valid")
        else:
            print_error("Invalid argument.")
            self.help("export")
    
    @command
    def import_commands(self, command_file):
        """Usage: Import global commands

        Description: Import the command database archive

        Arguments:
            command_file: relative path to command database compressed file 
        """
        apiclient = APIClient.getInstance()
        try:
            success = apiclient.importCommands(command_file)
        except IOError:
            print_error(f"Import failed. {command_file} was not found or is not a file.")
            return 
        if not success:
            print_error("Commands import failed")
        else:
            print_formatted("Commands import completed", "valid")

    @command
    def import_pentest(self, pentest_file):
        """Usage: Import pentest database

        Description: Import the pentest database archive

        Arguments:
            pentest_file: relative path to a pentest database compressed archive file (.gz)
        """
        apiclient = APIClient.getInstance()
        success = apiclient.importDb(pentest_file)
        if not success:
            print_error("Pentest database import failed")
        else:
            print_formatted("Pentest database import completed", "valid")


    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """  
        apiclient = APIClient.getInstance()
        if cmd in ["open", "delete", "duplicate"]:
            return apiclient.getPentestList()
        elif cmd == "export":
            if len(cmd_args) <= 1:
                return ["pentest", "commands"]
            elif len(cmd_args) == 2:
                if cmd_args[0] == "pentest":
                    return apiclient.getPentestList()
        elif cmd in ["import_commands", "import_pentest"]:
            return (Completion(completion.text, completion.start_position, display=completion.display) 
                        for completion in self.prompt_session.path_completer.get_completions(Document(cmd_args[0]), complete_event))
        elif cmd == "help":
            return [""]+self._cmd_list
        return []



if __name__ == '__main__':
    version = 1.0
    print_formatted(f"""
.__    ..              ,       
[__) _ || _ ._ * __ _.-+- _ ._.
|   (_)||(/,[ )|_) (_] | (_)[  
                   {version}            
""")
    Windows.enable(auto_colors=True, reset_atexit=True)  # Does nothing if not on Windows.
    pollenisator = Pollenisator()
    pollenisator.main_loop()
    
    