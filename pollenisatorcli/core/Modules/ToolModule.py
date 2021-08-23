from prompt_toolkit.formatted_text import FormattedText
from pollenisatorcli.utils.completer import IMCompleter
from pollenisatorcli.utils.utils import command, cls_commands, print_error, print_formatted, print_formatted_text
from pollenisatorcli.core.Views.ToolView import ToolView
from pollenisatorcli.core.Controllers.ToolController import ToolController
from pollenisatorcli.core.Models.Tool import Tool
from pollenisatorcli.core.Modules.GlobalModule import GlobalModule
name = "Tool" # Used in command decorator

@cls_commands
class ToolModule(GlobalModule):
    def __init__(self, name, parent_context, prompt_session, tools):
        super().__init__(name, parent_context, "Interact and edit "+name, FormattedText([('class:title', name),('class:angled_bracket', " > ")]), IMCompleter(self), prompt_session)
        self.tools = tools

    def refreshTools(self, toolname="all"):
        refreshed = []
        for tool in self.tools:
            if toolname == "all" or toolname == tool.name:
                res = Tool.fetchObject({"name":tool.name})
                if res is not None:
                    refreshed.append(res)
            else:
                refreshed.append(tool)
            
        self.tools = refreshed

    @command
    def ls(self):
        """Usage: ls

        Description: list the tools attached to the object
        """
        self.refreshTools()
        ToolView.print_info([tool for tool in self.tools])

    @command
    def launch(self, toolname, local=None):
        """Usage: launch <tool name|"all">["local"]

        Args:
            name: the toolname to launch or "All" to launch every tool at once 
            local: if local is given, the tool will be executed from this computer (the executor must have it in its local config toolds.d folder) 

        Description: Order execution of this tool 
        """
        self.refreshTools()
        self.launchCommandInToolView(toolname, "launch", local)
        self.refreshTools(toolname)

    @command
    def reset(self, toolname):
        """Usage: reset <tool name|"all">
        
        Args:
            name: the toolname to launch or "All" to launch every tool at once 

        Description: Reset the results of this tool if the tool is done only
        """
        self.refreshTools()
        self.launchCommandInToolView(toolname, "reset")
        self.refreshTools(toolname)

    @command
    def stop(self, toolname):
        """Usage: stop <tool name|"all">

        Args:
            name: the toolname to launch or "All" to launch every tool at once 

        Description: stop the exection of this tool if the tool is running only
        """
        self.refreshTools()
        self.launchCommandInToolView(toolname, "stop")
        self.refreshTools(toolname)

    @command
    def view(self, toolname):
        """Usage: view  <tool name|"all">

        Args:
            name: the toolname to launch or "All" to launch every tool at once 

        Description: Download and tries to open the result file. Only if the tool is done. tries to open it using xdg-open or os.startsfile
        """
        self.refreshTools()
        self.launchCommandInToolView(toolname, "view")

    def launchCommandInToolView(self, toolname, funcname, *args):
        toolsToLaunch = []
        for tool in self.tools:
            if toolname.lower() == "all" or toolname.lower() == tool.name.lower():
                toolsToLaunch.append(ToolView(ToolController(tool), self, self.prompt_session))
        for toolToLaunch in toolsToLaunch:
            func = getattr(toolToLaunch, funcname)
            func(*args)

    
    @command
    def edit(self, tool_title):
        """Usage: edit <tool_title>

        Description: edit tool object:
        
        Arguments:
            tool_title: a string to identify a tool.
        """
        self.refreshTools()
        # will swap context to edit an object and access it's subobjects
        objects_matching = Tool.fetchObject({"name":tool_title})
        if objects_matching is not None:
            self.set_context(ToolView(ToolController(objects_matching), self, self.prompt_session))
        else:
            print_error("This tool was not found")
        self.refreshTools(tool_title)

    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """  
        ret = super().getOptionsForCmd(cmd, cmd_args, complete_event)
        if ret:
            return ret
        elif cmd in ["stop","reset","view", "edit"]:
            return ["all"]+[tool.name for tool in self.tools]
        if cmd == "launch":
            if len(cmd_args) == 1:
                return ["all"]+[tool.name for tool in self.tools]
            elif len(cmd_args) == 2:
                return ["","local"]
        return []