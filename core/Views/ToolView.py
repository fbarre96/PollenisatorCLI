from core.Views.ViewElement import ViewElement
from terminaltables import AsciiTable
from colorclass import Color
from utils.utils import dateToString
from core.Models.Tool import Tool

class ToolView(ViewElement):
    @classmethod
    def print_info(cls, tools):
        if len(tools) >= 1:
            table_data = [['Name', 'Assigned', 'Status', 'Started at', 'Ended at']]
            for tool in tools:
                if isinstance(tool, dict):
                    tool = Tool(tool)
                title_str = ViewElement.colorWithTags(tool.getTags(), tool.name)
                status_colors = {"done":"green", "running":"blue", "ready":"yellow"}
                status = tool.getStatus()
                status_color = status_colors.get(status, None)
                if status_color is not None:
                    status_str = Color("{"+status_colors[status]+"}"+status+"{/"+status_colors[status]+"}")
                else:
                    status_str = status
                assigned_str = tool.getDetailedString()
                table_data.append([assigned_str, assigned_str,status_str, dateToString(tool.dated), dateToString(tool.datef)])
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