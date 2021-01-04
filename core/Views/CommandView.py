from core.Views.ViewElement import ViewElement
from terminaltables import AsciiTable

class CommandView(ViewElement):

    @classmethod
    def print_info(cls, commands):
        if len(commands) >= 1:
            table_data = [['Name', 'Options', 'Level', 'Priority', 'Safe', 'Max Threads']]
            for command in commands:
                table_data.append([command.name, command.text, str(command.lvl), str(command.priority), str(command.safe), str(command.max_thread)])
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