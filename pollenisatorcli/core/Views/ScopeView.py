from pollenisatorcli.core.Views.ViewElement import ViewElement
from terminaltables import AsciiTable
from pollenisatorcli.core.Models.Tool import Tool
from pollenisatorcli.core.Models.Scope import Scope
from pollenisatorcli.core.Models.Wave import Wave
from pollenisatorcli.core.Views.ToolView import ToolView
from pollenisatorcli.core.Views.ViewElement import ViewElement
from pollenisatorcli.core.Controllers.ToolController import ToolController
from pollenisatorcli.core.Controllers.ScopeController import ScopeController
from pollenisatorcli.core.Parameters.parameter import Parameter, BoolParameter, IntParameter, ListParameter, HiddenParameter, ComboParameter
from pollenisatorcli.utils.utils import isNetworkIp, isIp, isDomain
from pollenisatorcli.utils.utils import command, cls_commands
name = "Scope" # Used in command decorator

def validateScope(value):
        true_value = value.strip()
        if isNetworkIp(true_value) or isIp(true_value):
            return ""
        if isDomain(true_value):
            return ""
        return f"{value} is not a valid domain, IP address or Network IP"

@cls_commands
class ScopeView(ViewElement):
    name = "scope"
    children_object_types = {"tools":{"view":ToolView, "controller":ToolController, "model":Tool}}

    def __init__(self, controller, parent_context, prompt_session, **kwargs):
        super().__init__(controller, parent_context, prompt_session, **kwargs)
        self.fields = []
        if self.is_insert:
            self.fields.append(ListParameter("scope", required=True, validator=validateScope, helper="Type a list of scope comma separated")) 
        else:
            self.fields.append(Parameter("scope", required=True, validator=validateScope, default=self.controller.model.scope, readonly=True, helper="Declare this scope for a wave"))  

        self.fields += [
            ComboParameter("wave", Wave.fetchObjects({}), readonly=self.controller.model.wave != "", required=True, default=self.controller.model.wave, helper="the wave this scope is valid for"),
            Parameter("notes", default=self.controller.model.notes, helper="A space to take notes. Will appear in word report"),
            ListParameter("tags", default=self.controller.model.tags, validator=self.validateTag, completor=self.getTags, helper="Tag set in settings to help mark a content with a caracteristic"),
        ]

    

    def identifyPentestObjectsFromString(self, obj_str):
        """For a port, subclasses are tools and defects
        """
        # Tool test
        parent_db_key = self.controller.getDbKey()
        parent_db_key["name"] = obj_str
        tool_found = Tool.fetchObject(parent_db_key)
        if tool_found is not None:
            return ToolView, [ToolController(tool_found)]
        return None, []

    @classmethod
    def print_info(cls, scopes):
        if scopes:
            table_data = [['Scope', 'In wave', 'Tools : ', 'waiting', 'running', 'done']]
            for scope in scopes:
                if isinstance(scope, dict):
                    scope = Scope(scope)
                if isinstance(scope, ScopeController):
                    scope = scope.model
                tools = scope.getTools()
                done = 0
                running = 0
                not_done = 0
                for tool in tools:
                    tool_m = Tool(tool)
                    if tool_m.getStatus() == "done":
                        done += 1
                    elif tool_m.getStatus() == "running":
                        running += 1
                    else:
                        not_done += 1
                table_data.append([scope.scope, scope.wave, '', str(not_done), str(running), str(done)])
                table = AsciiTable(table_data)
                table.inner_column_border = False
                table.inner_footing_row_border = False
                table.inner_heading_row_border = True
                table.inner_row_border = False
                table.outer_border = False
            print(table.table)
        else:
            #No case
            pass