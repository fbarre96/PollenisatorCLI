from prompt_toolkit.formatted_text import FormattedText
from pollenisatorcli.utils.completer import IMCompleter
from pollenisatorcli.utils.utils import command, cls_commands, print_error, print_formatted, print_formatted_text
from pollenisatorcli.core.Views.ToolView import ToolView
from pollenisatorcli.core.Views.ViewElement import ViewElement
from pollenisatorcli.core.Controllers.ToolController import ToolController
from pollenisatorcli.core.Models.Tool import Tool
from pollenisatorcli.core.Modules.GlobalModule import GlobalModule
from prompt_toolkit import ANSI
from datetime import datetime
from colorclass import Color
name = "Tool" # Used in command decorator

@cls_commands
class ToolModule(GlobalModule):
    def __init__(self, name, parent_context, prompt_session, tools):
        super().__init__(name, parent_context, "Interact and edit with "+name+" tools", FormattedText([('class:title', name),('class:subtitle', ' Tools'),('class:angled_bracket', " > ")]), IMCompleter(self), prompt_session)
        self.tools = tools
        self.ls()

    def refreshTools(self, toolname="all"):
        refreshed = []
        for tool in self.tools:
            if toolname == "all" or toolname == tool.name:
                tool = Tool.fetchObject(tool.getDbKey())
                refreshed.append(tool)
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
        """Usage: launch <tool name|"all"> ["local"]

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
    
    @command
    def recap(self, status="all"):
        """Usage: recap ["done"|"error"|"running"|"ready"|"all"]
        Args:
            status: recap only the tools with the given status. If not set, all will be done
            
        Description: print info about each tools.
        """
        self.refreshTools()
        done = []
        running = []
        error = []
        ready = []
        for tool in self.tools:
            assigned_str = Color("{autoblue}"+tool.getDetailedString()+"{/autoblue}")
            tags_str = ViewElement.colorWithTags(tool.getTags(), ", ".join(tool.tags))
            if tags_str.strip() != "":
                assigned_str += f" ({tags_str})"
            if "done" in tool.getStatus():
                tab = done
            elif "running" in tool.getStatus():
                tab = running
            elif "error" in tool.getStatus():
                tab = error
            else:
                tab = ready
            tab.append((tool,assigned_str))
        if status in ["all", "done"]:
            print_formatted("\nDone tools:", "subtitle")
            for tool, assigned_str in done:
                if tool.notes.strip() != "":
                    print_formatted_text(ANSI(f"\n{assigned_str}"))
                    print_formatted(f"{tool.notes}")
        if status == "all" or status == "running":
            print_formatted("\nRunning tools:", "subtitle")
            for tool, assigned_str in running:
                print_formatted_text(ANSI(f"{assigned_str}"))
                running_for = datetime.now() - datetime.strptime(tool.dated, "%d/%m/%Y %H:%M:%S")
                print_formatted(f"Running for {running_for}", cls="normal")
        if status == "all" or status == "error":
            print_formatted("\nErrored tools:", "subtitle")
            for tool, assigned_str in error:
                print_formatted_text(ANSI(f"{assigned_str}"))
        if status == "all" or status == "ready":
            print_formatted("Ready/not done tools:", "subtitle")
            for tool, assigned_str in ready:
                print_formatted_text(ANSI(f"{assigned_str}"))
     

    def launchCommandInToolView(self, toolname, funcname, *args):
        toolsToLaunch = []
        for tool in self.tools:
            if toolname.lower() == "all" or toolname.lower() == tool.name.lower():
                toolsToLaunch.append(ToolView(ToolController(tool), self, self.prompt_session))
        for toolToLaunch in toolsToLaunch:
            func = getattr(toolToLaunch, funcname)
            func(*args)

    
    @command
    def edit(self, tool_title, *args):
        """Usage: edit <tool_title>

        Description: edit tool object:
        
        Arguments:
            tool_title: a string to identify a tool.
        """
        if len(args) >= 1:
            tool_title += " "+(" ".join(args))
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
        elif cmd == "recap":
            return ["done","error","running","ready","all"]
        return []