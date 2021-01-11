from core.Models.Defect import Defect
from core.Models.Port import Port
from core.Models.Tool import Tool
from core.Views.ToolView import ToolView
from core.Views.DefectView import DefectView
from core.Views.ViewElement import ViewElement
from core.Controllers.ToolController import ToolController
from core.Controllers.DefectController import DefectController
from terminaltables import AsciiTable
from utils.utils import command
from core.Parameters.parameter import Parameter, BoolParameter, IntParameter, ListParameter, HiddenParameter, ComboParameter

def validatePort(value):
    return value >= 0 and value <= 65535
class PortView(ViewElement):
    name = "port"
    children_object_types = {"defects":{"view":DefectView, "controller":DefectController, "model":Defect}, "tools":{"view":ToolView, "controller":ToolController, "model":Tool}}

    def __init__(self, controller, parent_context, prompt_session):
        super().__init__(controller, parent_context, prompt_session)
        self.fields = [
            Parameter("ip", readonly=self.controller.model.ip, required=True, default=self.controller.model.ip, helper="the ip this port is opened on"),
            IntParameter("port", readonly=self.controller.model.port != "", required=True,  validator=validatePort, default=self.controller.model.port, helper="Open port number"),
            ComboParameter("proto", ["tcp","udp"], default="tcp", required=True, helper="IP transport protocol contacting this port", readonly=self.controller.model.proto != ""),
            Parameter("service",default=self.controller.model.service, helper="Service running detected on this port by a tool (nmap by default)"),    
            Parameter("product",default=self.controller.model.product, helper="Product name running detected on this port by a tool (nmap by default)"),    
            Parameter("notes", helper="A space to take notes. Will appear in word report"),
            Parameter("tags", default=self.controller.model.tags, validator=self.validateTag, completor=self.getTags, helper="Tag set in settings to help mark a content with a caracteristic"),
        ]

    def identifyPentestObjectsFromString(self, obj_str):
        """For a port, subclasses are tools and defects
        """
        #defect test
        parent_db_key = self.controller.getDbKey()
        try:
            defect_found = Defect.fetchObject(parent_db_key)
            parent_db_key["title"] = obj_str
            if defect_found is not None:
                return DefectView, [DefectController(defect_found)]
            else:
                return None, []
        except ValueError:
            pass
        # Tool test
        parent_db_key["name"] = obj_str
        tool_found = Tool.fetchObject(parent_db_key)
        if tool_found is not None:
            return ToolView, [ToolController(tool_found)]
        return None, []


    @classmethod
    def print_info(cls, ports):
        if len(ports) >= 1:
            table_data = [['Port', 'Service', "Product", 'Tools : waiting', 'running', 'done', 'Defects']]
            for port in ports:
                if isinstance(port, dict):
                    port = Port(port)
                tools = port.getTools()
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
                defects = list(port.getDefects())
                port_str = ViewElement.colorWithTags(port.getTags(), port.getDetailedString())
                table_data.append([port_str, port.service, port.product, str(not_done), str(running), str(done), len(defects)])
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
