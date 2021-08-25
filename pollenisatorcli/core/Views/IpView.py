from pollenisatorcli.core.Views.ViewElement import ViewElement
from pollenisatorcli.utils.utils import command, style_table
from terminaltables import AsciiTable
from colorclass import Color
from pollenisatorcli.core.Models.Tool import Tool
from pollenisatorcli.core.Models.Port import Port
from pollenisatorcli.core.Models.Ip import Ip
from pollenisatorcli.core.Views.PortView import PortView
from pollenisatorcli.core.Views.ToolView import ToolView
from pollenisatorcli.core.Controllers.PortController import PortController
from pollenisatorcli.core.Controllers.ToolController import ToolController
from pollenisatorcli.core.Controllers.IpController import IpController
from pollenisatorcli.core.Parameters.parameter import Parameter, BoolParameter, IntParameter, ListParameter, HiddenParameter, ComboParameter, TableParameter
from pollenisatorcli.utils.utils import command, cls_commands, print_formatted_text
from prompt_toolkit import ANSI
import webbrowser
name = "IP" # Used in command decorator


@cls_commands
class IpView(ViewElement):
    name = "ip"
    children_object_types = {"ports":{"view":PortView, "controller":PortController, "model":Port}, "tools":{"view":ToolView, "controller": ToolController,"model":Tool}}

    def __init__(self, controller, parent_context, prompt_session, **kwargs):
        super().__init__(controller, parent_context, prompt_session, **kwargs)
        self.fields = [
            Parameter("ip", readonly=self.controller.model.ip != "", required = True, default=self.controller.model.ip, helper="a hostname/ip"),
            Parameter("notes", default=self.controller.model.notes, helper="A space to take notes. Will appear in word report"),
            ListParameter("tags", default=self.controller.model.tags, validator=self.validateTag, completor=self.getTags, helper="Tag set in settings to help mark a content with a caracteristic"),
            TableParameter("infos", ["Info", "Value"], default=self.controller.model.infos, required=False, helper="Extra info table")
        ]

    
    def identifyPentestObjectsFromString(self, obj_str):
        """For an ip, subclasses are tools and ports
        """
        #PORT test
        parent_db_key = self.controller.getDbKey()
        try:
            parts = obj_str.split("/") 
            if len(parts) == 1:
                port_n = int(obj_str)
                proto = "tcp"
            else:
                port_n = int(parts[1])
                proto = parts[0]
            parent_db_key["port"] = str(port_n)
            parent_db_key["proto"] = proto
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
            self.__class__.children_object_types[object_type]["view"].print_info(objects)
            return True
        return False

    
    @classmethod
    def print_info(cls, ips, level_of_info="all", is_aggregated=False):
        if ips:
            if level_of_info == "all":
                table_data = [['Ip', 'Hostname/Ip', 'Ports', 'Defects','Tools total', 'Waiting', 'Running', 'Done']]
                alignements = ["left"]*len(table_data[0])
                for i in range(4,len(alignements)):
                    alignements[i] = "right"
            else:
                table_data = [['Ip', 'Hostname/Ip', 'Ports', 'Defects']]
                alignements = ["left"]*len(table_data[0])
                for i in range(2, len(alignements)):
                    alignements[i] = "right"

            oos_table_data = []
            for ip in ips:
                if isinstance(ip, dict):
                    ip_m = Ip(ip)
                elif isinstance(ip, IpController):
                    ip_m = ip.model
                else:
                    ip_m = ip
                port_count = ip_m.getPortCount() if not is_aggregated else len(ip["ports"])
                hostnames = ip_m.infos.get("hostname", [])
                hostname_str = ""
                if hostnames:
                    if isinstance(hostnames, list):
                        hostname_str = ", ".join(hostnames)
                    else:
                        hostname_str = hostnames
                
                ip_str = ", ".join(list(ip_m.infos.get("ip", "")))
                if ip_str:
                    alias_str = str(ip_str)
                else:
                    alias_str = hostname_str
                tools = ip_m.getTools() if not is_aggregated else ip["tools"]
                done = 0
                running = 0
                not_done = 0
                for tool in tools:
                    tool_m = Tool(tool)
                    if "done" in tool_m.getStatus():
                        done += 1
                    elif "running" in tool_m.getStatus():
                        running += 1
                    else:
                        not_done += 1
                ports = ip_m.getPorts() if not is_aggregated else ip["ports"]
                strs_ports = []
                for port in ports:
                    port_m = Port(port)
                    strs_ports.append(f"{port_m.port}/{port_m.proto}:{port_m.service}" if port_m.proto != "tcp" else f"{port_m.port}:{port_m.service}")
                ip_str = ip_m.ip
                if not ip_m.in_scopes:
                    ip_str = Color("{autoblack}"+ip_str+"{/autoblack}")
                else:
                    ip_str = ViewElement.colorWithTags(ip_m.getTags(), ip_m.ip)
                defect_count = ip_m.getDefectCount() if not is_aggregated else len(ip["defects"])
                strs_ports = ", ".join(strs_ports)
                if strs_ports.strip() == "":
                    strs_ports = "-"
                if len(ip_m.in_scopes) > 0: # out of scopes ip will be appended after
                    if level_of_info == "all":
                        table_data.append([ip_str, alias_str, strs_ports, str(defect_count), str(not_done+running+done), str(not_done), str(running), str(done)])
                    else:
                        table_data.append([ip_str, alias_str, str(port_count), str(defect_count)])
                else:
                    if level_of_info == "all":
                        oos_table_data.append([ip_str, alias_str,  strs_ports, str(defect_count), str(not_done+running+done), str(not_done), str(running), str(done)])
                    else:
                        oos_table_data.append([ip_str, alias_str, str(port_count), str(defect_count)])
            for oos_data in oos_table_data:
                table_data.append(oos_data)
            table = AsciiTable(table_data)
            table = style_table(table, alignements)
            print_formatted_text(ANSI(table.table+"\n"))
        else:
            #No case
            pass

    @command
    def browser(self):
        """Usage: browser
        Description: open the ip in a web browser
        """
        webbrowser.open_new_tab(self.controller.model.ip)