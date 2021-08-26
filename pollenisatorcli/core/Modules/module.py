import os
import shlex
import time
import re
from prompt_toolkit import ANSI
from terminaltables import AsciiTable
from colorclass import Color
from datetime import datetime
from pollenisatorcli.utils.utils import command, cls_commands, main_help, print_formatted_text, print_formatted, style_table
from pollenisatorcli.core.apiclient import APIClient
from pollenisatorcli.core.Models.Wave import Wave
from pollenisatorcli.core.Models.Tool import Tool
from pollenisatorcli.AutoScanWorker import executeCommand

from multiprocessing.connection import Listener

name = "Global" # Used in command decorator (Tricks command help to show itself as in Global Module)



class Module:
    _cmd_list = []
    _module_cmds = dict
    def __init__(self, name, parent_context, description, prompt, completer, prompt_session):
        self.name = name
        self.parent_context = parent_context
        self.description = description
        self.prompt = prompt
        self.completer = completer
        self.prompt_session = prompt_session
        self.contexts = {}
        self.proc = None
    
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
        """Usage: help
        Description:
            Print this help menu 
        """        
        # Command specific help
        if command_help != "":
            if command_help not in self.__class__._cmd_list:
                msg = f"Command {command_help} not found.\n"
                msg += """List of available commands :\n"""

                for x in self.__class__._cmd_list:
                    msg += f'\t{x}\n'
                return msg
            else:
                return getattr(self, command_help).__doc__
        return None

    def print_command_help(self):
        msg = main_help()
        msg += f"""
{self.name} commands
=================
{self.description}
List of available commands :"""
        print_formatted(msg)
        module_cmds = self.__class__._module_cmds
        regex_desc = re.compile(r"description\s?:\s?(.+)$", re.IGNORECASE|re.MULTILINE)
        for moduleName in sorted(module_cmds):
            print_formatted(f'{moduleName}', 'module')
            table_data = [['Command', 'Description']]
            for x in module_cmds[moduleName]:
                desc = ""
                if x.__doc__:
                    desc = re.search(regex_desc, x.__doc__)
                    if desc:
                        desc = desc.group(1)
                    else:
                        desc = ""
                colored_name = Color("{autoblue}"+x.__name__+"{/autoblue}")
                colored_desc = Color("{autowhite}"+desc+"{/autowhite}")
                table_data.append([colored_name, colored_desc])
            table = AsciiTable(table_data)
            table = style_table(table)
            print_formatted_text(ANSI(table.table+"\n"))

    def print_help_footer(self):
        print_formatted("For more information about any commands hit :")
        print_formatted("help <command>", "cmd")
        
    @command
    def help(self, command_help=""):
        # Global help
        res = self.getCommandHelp(command_help)
        if res is not None:
            print_formatted(res)
            return
        self.print_command_help()
        self.print_help_footer()
    

    def takeCommands(self, apiclient):
        APIClient.setInstance(apiclient)
        address = ('localhost', 10817)
        password = os.environ["POLLEX_PASS"]
        excludedCommands = ["echo"]
        # LISTEN
        self.s = Listener(address, authkey=password.encode())
        while True:
            try:
                connection = self.s.accept()
            except:
                return False
            execCmd = connection.recv().decode()
            cmdName = os.path.splitext(os.path.basename(execCmd.split(" ")[0]))[0]
            if cmdName in excludedCommands:
                connection.close()
                continue
            args = shlex.join(shlex.split(execCmd)[1:])
            cmdName +="::"+str(time.time()).replace(" ","-")
            wave = Wave().initialize("Custom commands")
            wave.addInDb()
            tool = Tool()
            tool.initialize(cmdName, "Custom commands", "", None, None, None, "wave", execCmd, dated=datetime.now().strftime("%d/%m/%Y %H:%M:%S"), datef="None", scanner_ip="localhost")
            tool.updateInfos({"args":args})
            res, iid = tool.addInDb()
            if res:
                ret_code, outputfile = executeCommand(apiclient, str(iid), "auto-detect", True, True)
            connection.send(outputfile)
            connection.close()
        self.s.close()
        return True 

    def exit(self):
        """
        Description : Returns to previous module or quit program if in main module
        """
        if self.parent_context is not None:
            self.set_context(self.parent_context)