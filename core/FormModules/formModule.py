from utils.utils import command, cls_commands, print_error, print_formatted
from core.Modules.module import Module
from core.apiclient import APIClient
from terminaltables import AsciiTable

class FormModule(Module):
    def __init__(self, name, parent_context, description, prompt, completer, prompt_session):
        super().__init__(name, parent_context, description, prompt, completer, prompt_session)
        self.fields = []

    
    @command
    def set(self, parameter_name, value):
        """Usage : set <parameter_name> <value>
        
        Description : Set the parameter to the given value

        Args:
            parameter_name  the parameter to change
            value           the value to give to the parameter
        """ 
        for field in self.fields:
            if field.name.lower() == parameter_name.lower():
                msg = field.setValue(value)
                if msg == "":
                    return True
                else:
                    print_error(msg)
                    return False
        print_error(f"Parameter {parameter_name} does not exist. Use command show to list available parameters")
        return False
    
    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """
        Returns a list of valid options for the given cmd
        """  
        if cmd == "set":
            if len(cmd_args) <= 1: # param name to complete
                return [x.name for x in self.fields]
            else: # param value to complete
                for field in self.fields:
                    if cmd_args[-2].lower() == field.name.lower():
                        return field.getPossibleValues()
        elif cmd == "help":
            return [""]+self._cmd_list+[x.name for x in self.fields]
        
        return []

    @command
    def show(self):
        """Usage : show
        
        Description : show the parameters and their assigned valued. required parameters ends with a *
        """ 
        msg = ""
        table_data = [['Parameters', 'Values']]
        
        for param in self.fields:
            paramName = param.name+"*" if param.required else param.name
            table_data.append([paramName, param.getValue()])
        table = AsciiTable(table_data)
        table.inner_column_border = False
        table.inner_footing_row_border = False
        table.inner_heading_row_border = True
        table.inner_row_border = False
        table.outer_border = False
            
        msg = f"{table.table}\n\n"
        print_formatted(msg, 'important')
    
    def validateParam(self, param, value):
        return True

    def getParameterHelp(self, parameter_name):
        for x in self.fields:
            if x.name.lower() == parameter_name.lower():
                return x.getHelp()
        return None
    
    def checkRequiredFields(self):
        for field in self.fields:
            if field.required and field.getValue() == "":
                print_error("Parameter {field.name} is required")
                return False
        return True
    
    @command
    def help(self, parameter_or_cmd_name=""):
        """Usage : help [parameter or command name]
        
        Description : show help menu or an helper on how to use the parameter or command name if one is given.
        """ 
        res = self.getCommandHelp(parameter_or_cmd_name)
        if res is not None and "not found" not in res:
            print(res)
            return
        res = self.getParameterHelp(parameter_or_cmd_name)
        if res is not None:
            print(res)
            return
        print(f"""
{self.name} form
=================
{self.description}
COMMANDS:""")
        for x in self._cmd_list:
            print_formatted(f'\t{x}', 'command')
        print("=================")
        print("""PARAMETERS :""")
        for x in self.fields:
            print_formatted(f'\t{x.name}', 'parameter')
        print("""
For more information about any parameter or command type :""")
        print_formatted("help <parameter_name>", 'cmd')
