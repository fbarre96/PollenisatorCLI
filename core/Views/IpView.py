from core.Views.ViewElement import ViewElement
from utils.utils import command
from terminaltables import AsciiTable
from colorclass import Color
from core.Models.Tool import Tool
from core.Models.Port import Port
from core.Models.Ip import Ip
from core.Views.PortView import PortView
from core.Views.ToolView import ToolView
from core.Controllers.PortController import PortController
from core.Controllers.ToolController import ToolController
from core.Parameters.parameter import Parameter, BoolParameter, IntParameter, ListParameter, HiddenParameter, ComboParameter

class IpView(ViewElement):
    name = "ip"
    children_object_types = {"ports":{"view":PortView, "controller":PortController, "model":Port}, "tools":{"view":ToolView, "controller": ToolController,"model":Tool}}

    def __init__(self, controller, parent_context, prompt_session):
        super().__init__(controller, parent_context, prompt_session)
        self.fields = [
            Parameter("ip", readonly=self.controller.model.ip != "", required = True,  default=self.controller.model.ip, helper="an ip"),
            Parameter("notes", helper="A space to take notes. Will appear in word report"),
            Parameter("tags", default=self.controller.model.tags, validator=self.validateTag, completor=self.getTags, helper="Tag set in settings to help mark a content with a caracteristic"),
        ]

    
    def identifyPentestObjectsFromString(self, obj_str):
        """For an ip, subclasses are tools and ports
        """
        #PORT test
        parent_db_key = self.controller.getDbKey()
        try:
            port_n = int(obj_str)
            parent_db_key["port"] = port_n
            port_found = Port.fetchObject(parent_db_key)
            if port_found is not None:
                return PortView, [PortController(port_found)]
            else:
                return None, []
        except ValueError:
            pass
        # Tool test
        parent_db_key["name"] = obj_str
        parent_db_key["lvl"] = "ip"
        tool_found = Tool.fetchObject(parent_db_key)
        if tool_found is not None:
            return ToolView, [ToolController(tool_found)]
        return None, []

    @command
    def ls(self, object_type):
        """Usage: ls <ports|tools>

        Description: Will list direct children of this object if their type matches object type 

        Args:
            children_object_type: a children object type like port, tool
        """
        if object_type in self.__class__.children_object_types:
            search_pipeline = self.controller.model.getDbKey()
            if object_type == "tools":
                search_pipeline["lvl"] = "ip"
            objects = self.__class__.children_object_types[object_type]["model"].fetchObjects(search_pipeline)
            for obt in objects:
                print(obt.getDetailedString())
            return True
        return False

   
    @classmethod
    def print_info(cls, ips):
        if len(ips) >= 1:
            table_data = [['Ip', 'In scope', 'Ports', 'Tools total', 'Waiting', 'Running', 'Done']]
            for ip in ips:
                if isinstance(ip, dict):
                    ip = Ip(ip)
                tools = ip.getTools()
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
                ports = ip.getPorts()
                strs_ports = []
                for port in ports:
                    port_m = Port(port)
                    strs_ports.append(f"{port_m.port}/{port_m.proto}:{port_m.service}" if port_m.proto != "tcp" else f"{port_m.port}:{port_m.service}")
                ip_str = ip.ip
                if not ip.in_scopes:
                    ip_str = Color("{grey}"+ip_str+"{/grey}")
                else:
                    ip_str = ViewElement.colorWithTags(ip.getTags(), ip.ip)
                table_data.append([ip_str, len(ip.in_scopes) > 0, ", ".join(strs_ports), str(not_done+running+done), str(not_done), str(running), str(done)])
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