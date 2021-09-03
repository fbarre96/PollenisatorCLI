#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Usage description for docopt
"""
Pollenisator
Usage: 
    pollenisator.py [-h] [-v] [--host <host>] [--port <port>] [--http]

Options: 
    -h, --help                           Show this help menu.
    -v, --version                        Show version.
    --host                               API server IP. If not provided, the configuration file will be used. If provided, will update configuration file.  
    --port, -p                           API listening port. If not provided, the configuration file will be used. If provided, will update configuration file. 
    --http                              Call API using http instead of https
"""
"""
@author: Fabien Barré for AlgoSecure
# Date: 16/12/2020
# Major version released: 01/2021
"""
version = 1.0
import sys
from datetime import datetime
import asyncio
import shlex
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
from pollenisatorcli.core.apiclient import APIClient
from pollenisatorcli.core.FormModules.newPentestForm import NewPentestForm
from pollenisatorcli.core.FormModules.settingsForms import LocalSettings, PollenisatorSettings
from pollenisatorcli.core.Modules.module import Module
from pollenisatorcli.core.Modules.pentest import Pentest
from pollenisatorcli.core.Modules.admin import Admin
from pollenisatorcli.core.Modules.commandtemplate import CommandTemplate
from pollenisatorcli.utils.completer import IMCompleter
from pollenisatorcli.utils.utils import (CmdError, cls_commands, command,
                         getClientConfigFilePath, loadClientConfig, main_help,
                         print_error, print_formatted, saveCfg, style)

from colorclass import Windows
import os
from multiprocessing.connection import Client
name = "Pollenisator dbs"



@cls_commands
class Pollenisator(Module):
    def __init__(self):
        args = docopt(__doc__, version=version)
        client_config = loadClientConfig()
        if args["--host"]:
            client_config["host"] = args["<host>"]
        if args["--port"]:
            client_config["port"] = args["<port>"]
        client_config["https"] = False if args["--http"] else True
        saveCfg(client_config, getClientConfigFilePath())
        self.connected = False
        apiclient = APIClient.getInstance()
        res = apiclient.connect()
        if not res:
            return
        self.connected = True
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
            "local_settings": LocalSettings(self, self.prompt_session),
        }

        
        # Start in main module (this one)
        self.set_context(self)

    

        
    def parse_result(self, result):
        if len(result):
            if not self.context_switching(result):
                command = result.split(" ") # shlex.split will remove quotes i.e : query type == "tool"
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
        """Usage: ls
        
        Description : ls existings pentests
        """  
        apiclient = APIClient.getInstance()
        pentests = "\n".join(apiclient.getPentestList())
        print_formatted(f"Pentests:\n==========\n{pentests}", "important")

    @command
    def command_templates(self):
        """Usage: command_templates 
        
        Description : Open the submodule to edit command templates for every pentest
        """
        self.set_context(self.contexts["command_templates"])

    @command
    def global_settings(self):
        """Usage: global_settings 
        
        Description : Open pollenisator global settings module
        """
        self.set_context(self.contexts["global_settings"])

    @command
    def local_settings(self):
        """Usage: local_settings 
        
        Description : Open pollenisator local settings module
        """
        self.set_context(self.contexts["local_settings"])

    @command
    def open(self, pentest_name):
        """Usage: open <pentest_name>
        
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
        """Usage: new
        
        Description : Start the pentest creation wizard
        """ 
        self.set_context(self.contexts["new pentest"])

    @command
    def delete(self, pentest_name):
        """Usage: delete <pentest_name>
        
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
        """Usage: duplicate <pentest_name> <to_pentest>

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
            apiclient.setCurrentPentest(pentest_name)
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
    
    @command
    def admin(self):
        """Usage: admin
        Description: Open the admin module to handle users"""
        self.set_context(Admin(self, self.prompt_session))

    @command
    def change_password(self):
        """Usage: change_password
        Description: Ask current user to change its password"""
        apiclient = APIClient.getInstance()
        old = prompt("Old password > ", is_password=True)
        new = prompt("New password > ", is_password=True)
        conf = prompt("Confirm new password > ", is_password=True)
        if conf != new:
            print_error("New password and confirmation are different.")
            return
        
        msg = apiclient.changeUserPassword(old, new)
        if msg != "":
            print_error(msg)
        else:
            print_formatted("Changed password successfully", "success")

            
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
            return [""]+self.__class__._cmd_list
        return []

def pollex():
    """Send a command to execute for pollenisator-gui running instance
    """
    address = ('localhost', 10817)
    password = os.environ["POLLEX_PASS"]
    conn = Client(address, authkey=password.encode())
    conn.send(shlex.join(sys.argv[1:]).encode())
    try:
        resp = conn.recv()
        os.system(f"cat {resp}")
    except:
        pass
    conn.close()

def main():
    print_formatted(f"""
.__    ..              ,       
[__) _ || _ ._ * __ _.-+- _ ._.
|   (_)||(/,[ )|_) (_] | (_)[  
                   {version}            
""")
    Windows.enable(auto_colors=True, reset_atexit=True)  # Does nothing if not on Windows.
    pollenisator = Pollenisator()
    if pollenisator.connected:
        pollenisator.main_loop()

if __name__ == '__main__':
    main()
    
    