from core.Views.ViewElement import ViewElement
from terminaltables import AsciiTable
from core.Models.Tool import Tool
from core.Models.Scope import Scope

class ScopeView(ViewElement):

    @classmethod
    def print_info(cls, scopes):
        if len(scopes) >= 1:
            table_data = [['Scope', 'In wave', 'Tools : waiting', 'running', 'done']]
            for scope in scopes:
                if isinstance(scope, dict):
                    scope = Scope(scope)
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
                table_data.append([scope.scope, scope.wave, str(not_done), str(running), str(done)])
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