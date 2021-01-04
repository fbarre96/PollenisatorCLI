from core.Views.ViewElement import ViewElement
from terminaltables import AsciiTable
from colorclass import Color
from core.Models.Tool import Tool
from core.Models.Port import Port

class IpView(ViewElement):

    @classmethod
    def print_info(cls, ips):
        if len(ips) >= 1:
            table_data = [['Ip', 'In scope', 'Ports', 'Tools W ', 'R', 'D']]
            for ip in ips:
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
                    strs_ports.append(f"{port_m.port}/{port_m.service}/{port_m.proto}" if port_m.proto != "tcp" else f"{port_m.port}/{port_m.service}")
                ip_str = ip.ip
                if not ip.in_scopes:
                    ip_str = Color("{grey}"+ip_str+"{/grey}")
                else:
                    ip_str = ViewElement.colorWithTags(ip.getTags(), ip.ip)
                table_data.append([ip_str, len(ip.in_scopes) > 0, ", ".join(strs_ports), str(not_done), str(running), str(done)])
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