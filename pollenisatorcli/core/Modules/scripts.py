from pollenisatorcli.utils.utils import command, cls_commands, print_error, print_formatted, print_formatted_text, getMainDir
from pollenisatorcli.utils.completer import IMCompleter
from pollenisatorcli.core.Modules.GlobalModule import GlobalModule
from pollenisatorcli.core.apiclient import APIClient
from prompt_toolkit.formatted_text import FormattedText
import os
import importlib
from collections import OrderedDict
name = "Scripts" # Used in command decorator

@cls_commands
class ScriptsModule(GlobalModule):
    def __init__(self, parent_context, prompt_session):
        super().__init__('Scripts', parent_context, "Scripts manager", FormattedText([('class:title', "Scripts"),('class:angled_bracket', " > ")]), IMCompleter(self), prompt_session)
        self.scripts = self.loadScripts()

    def loadScripts(self):
        full_script_path = self.getScriptsDir()
        script_shown = OrderedDict()
        for root, _, files in os.walk(full_script_path):
            for file in files:
                filepath = root + '/' + file
                if file.endswith(".py") and file != "__init__.py":
                    module_name = filepath.replace(full_script_path+"/", "")
                    script_shown[module_name] = file
        return script_shown
        
    def getScriptsDir(self):
        return os.path.normpath(os.path.join(getMainDir(), "scripts/"))

    @command
    def search(self, script_name, *args):
        """Usage: search <script name>
        Description: Return matching scripts paths
        """
        if args:
            script_name += " ".join(args)
        for script in self.scripts:
            if script_name.lower() in script.lower():
                print_formatted(script)
        
    @command
    def exec(self, script_path, *args):
        """Usage: exec <script name>
        Description: execute the given script path
        """
        if args:
            script_path += " ".join(args)
        if script_path not in self.scripts:
            print_error(f"{script_path}  not found")
            return
        self.executeScript(script_path)
            
    def executeScript(self, script_path):
        script_path = os.path.splitext(script_path)[0]
        module = os.path.join("pollenisatorcli/scripts/",script_path).replace("/", '.')
        imported = importlib.import_module(module)
        apiclient = APIClient.getInstance()
        success, res = imported.main(apiclient)
        if success:
            print_formatted(f"Script finished : {script_path} finished.\n{res}")
        else:
            print_error(f"Script failed : {script_path} failed.\n{res}")

    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """
        if cmd == "search" or cmd == "exec":
            return self.scripts.keys()
        ret = super().getOptionsForCmd(cmd, cmd_args, complete_event)
        if ret:
            return ret
        return []
