from core.Views.ViewElement import ViewElement
from core.Models.Tool import Tool
from terminaltables import AsciiTable

class PortView(ViewElement):
    @classmethod
    def print_info(cls, ports):
        if len(ports) >= 1:
            table_data = [['Port', 'Service', "Product", 'Tools : waiting', 'running', 'done', 'Defects']]
            for port in ports:
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