from core.Views.ViewElement import ViewElement
from terminaltables import AsciiTable
from core.Models.Tool import Tool
from core.Models.Wave import Wave
from core.Models.Interval import Interval
from core.Models.Scope import Scope
from core.Controllers.ScopeController import ScopeController
from core.Controllers.ToolController import ToolController
from core.Controllers.IntervalController import IntervalController
from core.Controllers.WaveController import WaveController
from core.Views.ScopeView import ScopeView
from core.Views.ToolView import ToolView
from core.Views.IntervalView import IntervalView
from utils.utils import command, cls_commands, print_formatted_text
from core.Parameters.parameter import Parameter, BoolParameter, IntParameter, ListParameter, HiddenParameter, ComboParameter, ListParameter
import re

@cls_commands
class WaveView(ViewElement):
    name = "wave"
    children_object_types = {"scopes":{"view":ScopeView, "controller":ScopeController, "model":Scope},
                             "tools":{"view":ToolView, "controller": ToolController,"model":Tool},
                             "intervals":{"view":IntervalView, "controller":IntervalController, "model":Interval}}

    def __init__(self, controller, parent_context, prompt_session, **kwargs):
        super().__init__(controller, parent_context, prompt_session, **kwargs)
        self.fields = [
            Parameter("wave", readonly=self.controller.model.wave != "", required = True,  default=self.controller.model.wave, helper="Wave unique name"),
            ListParameter("tags", default=self.controller.model.tags, validator=self.validateTag, completor=self.getTags, helper="Tag set in settings to help mark a content with a caracteristic"),
        ]

    @command
    def edit(self, object_title):
        """Usage: edit <scope>|interval_<index starting from 1>|<tool name>

        Description: edit object module:
        
        Arguments:
            object_title: a string to identify an object.
        """
        super().edit(object_title)

    def identifyPentestObjectsFromString(self, obj_str):
        """For a wave, subclasses are tools, scopes and intervals
        """
        #interval test
        parent_db_key = self.controller.getDbKey()
        # Intervals do not have a searchable key, using index in db is mehhhhh
        match = re.search(r"interval_(\d+)", obj_str)
        if match is not None:
            to_get = int(match.groups(1)[0]) - 1
            try:
                interval_found = [x for x in Interval.fetchObjects(parent_db_key)][to_get]
            except IndexError:
                return None, []
            return IntervalView, [IntervalController(interval_found)]
        # scope test
        parent_db_key["scope"] = obj_str
        scope_found = Scope.fetchObject(parent_db_key)
        if scope_found is not None:
            return ScopeView, [ScopeController(scope_found)]
        del parent_db_key["scope"]
        # Tool test
        parent_db_key["name"] = obj_str
        parent_db_key["lvl"] = "wave"
        tool_found = Tool.fetchObject(parent_db_key)
        if tool_found is not None:
            return ToolView, [ToolController(tool_found)]
        return None, []

    @command
    def ls(self, object_type):
        """Usage: ls <scopes|intervals|tools>

        Description: Will list direct children of this object if their type matches object type 

        Args:
            children_object_type: a children object type like port, tool
        """
        if object_type in self.__class__.children_object_types:
            search_pipeline = self.controller.model.getDbKey()
            if object_type == "tools":
                search_pipeline["lvl"] = "wave"
            objects = self.__class__.children_object_types[object_type]["model"].fetchObjects(search_pipeline)
            for obt in objects:
                print_formatted_text(ViewElement.colorWithTags(obt.getTags(), obt.getDetailedString()))
            return True
        return False

    @classmethod
    def print_info(cls, waves):
        if len(waves) >= 1:
            table_data = [['Wave', 'Currently launchable', 'Tools : waiting', 'running', 'done']]
            for wave in waves:
                if isinstance(wave, dict):
                    wave = Wave(wave)
                if isinstance(wave, WaveController):
                    wave = wave.model
                tools = wave.getTools()
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
                table_data.append([wave.wave, wave.isLaunchableNow(), str(not_done), str(running), str(done)])
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