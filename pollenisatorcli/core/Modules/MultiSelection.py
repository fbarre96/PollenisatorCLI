from pollenisatorcli.core.Modules.module import Module
from pollenisatorcli.core.settings import Settings
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.shortcuts import confirm
from pollenisatorcli.utils.utils import cls_commands, command, print_error, print_formatted
from pollenisatorcli.utils.completer import IMCompleter
from pollenisatorcli.core.apiclient import APIClient
from pollenisatorcli.core.Views.CommandView import CommandView
from pollenisatorcli.core.Views.WaveView import WaveView
from pollenisatorcli.core.Views.ScopeView import ScopeView
from pollenisatorcli.core.Views.IpView import IpView
from pollenisatorcli.core.Views.PortView import PortView
from pollenisatorcli.core.Views.DefectView import DefectView
from pollenisatorcli.core.Views.ToolView import ToolView
from pollenisatorcli.core.Models.Command import Command
from pollenisatorcli.core.Models.Wave import Wave
from pollenisatorcli.core.Models.Scope import Scope
from pollenisatorcli.core.Models.Ip import Ip
from pollenisatorcli.core.Models.Port import Port
from pollenisatorcli.core.Models.Defect import Defect
from pollenisatorcli.core.Models.Tool import Tool
from pollenisatorcli.core.Controllers.CommandController import CommandController
from pollenisatorcli.core.Controllers.WaveController import WaveController
from pollenisatorcli.core.Controllers.ScopeController import ScopeController
from pollenisatorcli.core.Controllers.IpController import IpController
from pollenisatorcli.core.Controllers.PortController import PortController
from pollenisatorcli.core.Controllers.DefectController import DefectController
from pollenisatorcli.core.Controllers.ToolController import ToolController
from pollenisatorcli.core.FormModules.exportForm import exportForm
from pollenisatorcli.core.Modules.review import ReviewModule

name = "Selection" # Used in command decorator

@cls_commands
class MultiSelection(Module):
    """View for multi selected object."""
    def __init__(self, selection, parent_context, prompt_session,  **kwargs):
        self.selection = selection
        self.count = 0
        for types in self.selection:
            self.count += len(self.selection[types])
        super().__init__('Selection', parent_context, "Selection module.", FormattedText([('class:title', f"Selection of {self.count} objects"),('class:angled_bracket', " > ")]), IMCompleter(self), prompt_session)
       
    @command
    def show(self):
        for types, documents in self.selection.items():
            cls = self.factoryView(types)
            if documents:
                print_formatted(f"{types.capitalize()}:", "subtitle")
                cls.print_info(documents)

    @command
    def delete(self):
        """Usage: delete_all
        Description: bulk deletion of selected items
        """
        answer = confirm(f"Are you sure you want to delete {self.count} objects?")
        if not answer:
            return
        toDelete = {}
        for types, documents in self.selection.items():
            if documents:
                toDelete[types] = []
                for document in documents:
                    toDelete[types].append(document["_id"])
        apiclient = APIClient.getInstance()
        res = apiclient.bulkDelete(toDelete)
        if res is not None:
            print_formatted(f"Deleted {res} items successfully.", "success")
            self.exit()

    @command
    def review(self):
        """Usage: review
        Description : Review selected items one by one.
        """
        toReview = []
        for types, documents in self.selection.items():
            if documents:
                for document in documents:
                    model = self.factory(types, document)
                    toReview.append(model)
        self.set_context(ReviewModule(toReview, self, self.prompt_session))
        
    @command
    def export(self):
        """Usage: export
        Description: open the export form
        """
        self.set_context(exportForm(self.selection, self, self.prompt_session))

    def factoryView(self, types):
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
            raise TypeError("The given type is invalid : "+str(types))
        return cls

    def factory(self, types, document):
        if types == "ports":
            cls = Port(document)
        elif types == "defects":
            cls = Defect(document)
        elif types == "commands":
            cls = Command(document)
        elif types == "waves":
            cls = Wave(document)
        elif types == "scopes":
            cls = Scope(document)
        elif types == "ips":
            cls = Ip(document)
        elif types == "tools":
            cls = Tool(document)
        else:
            raise TypeError("The given type is invalid : "+str(types))
        return cls

    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """  
        
        return []