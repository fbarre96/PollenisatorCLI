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
from prompt_toolkit import PromptSession
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter, PathCompleter
from shlex import split
from docopt import docopt, DocoptExit
import sys
import functools
from datetime import datetime

from utils.utils import command, cls_commands,main_help, loadCfg, saveCfg, getClientConfigFilePath
from utils.completer import IMCompleter
from core.apiclient import APIClient
from core.Modules.pentest import Pentest
from core.Modules.module import Module

@cls_commands
class Pollenisator(Module):
    def __init__(self):
        
        self.prompt_session = PromptSession(
            'Pollenisator > ',
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            complete_in_thread=True,
            complete_while_typing=True
        )
        self.prompt_session.path_completer = PathCompleter()

        super().__init__("Main", None, "Main", "Pollenisator > ", IMCompleter(self), self.prompt_session)
        self.contexts = [
            Pentest(self, self.prompt_session),
        ]
        args = docopt(__doc__, version=version)
        client_config = loadCfg(getClientConfigFilePath())
        if args["host"]:
            client_config["host"] = args["host"]
        if args["port"]:
            client_config["port"] = args["ports"]
        saveCfg(client_config, getClientConfigFilePath())
        apiclient = APIClient.getInstance()
        if not apiclient.tryConnection():
            print("Could not connect to server. Use --host and --port option.")
            return
        # Start in main module (this one)
        self.set_context(self)
        
    def parse_result(self, result):
        if len(result):
            if not self.context_switching(result):
                command = split(result)
                try:
                    bound_cmd_handler = functools.partial(getattr(self.current_context, command[0]), *command[1:])
                    run_in_terminal(bound_cmd_handler)
                except TypeError:
                    print (f"Error type")
                except AttributeError as ae:
                    print (f"Error with the command '{command[0]}':\n{ae}")
                except SystemExit:
                    pass

    def main_loop(self):
        while True:
            try:
                result = self.prompt_session.prompt()
                if (self.current_context == self and result.strip().lower() == "exit"):
                    break
                self.parse_result(result)
            except KeyboardInterrupt:
                print("CTRL^C")
                break

    @command
    def list(self):
        """
        Usage : list
        
        Description : list existings pentests
        """  
        apiclient = APIClient.getInstance()
        pentests = "\n".join(apiclient.getPentestList())
        print(f"Pentests:\n==========\n{pentests}\n")
    
    @command
    def open(self, pentest_name):
        """
        Usage : open <pentest_name>
        
        Description : Open the given database name and get the CLI in pentesting mode.

        Args:
            pentest_name  the pentest database name to load in application. 
        """  
        apiclient = APIClient.getInstance()
        if pentest_name not in apiclient.getPentestList():
            print("This pentest does not exist. Create it or choose one in the list below.")
            self.list()
            return
        apiclient.setCurrentPentest(pentest_name)
        self.context_switching("pentest")
        self.prompt_session.message = f"{self.current_context.prompt} {pentest_name} > "



if __name__ == '__main__':
    version = 1.0
    print(f"""
.__    ..              ,       
[__) _ || _ ._ * __ _.-+- _ ._.
|   (_)||(/,[ )|_) (_] | (_)[  
                   {version}            
""")
    pollenisator = Pollenisator()
    pollenisator.main_loop()
    
    