from pollenisatorcli.utils.utils import command, cls_commands, print_error, print_formatted
from pollenisatorcli.utils.completer import ParamCompleter
from pollenisatorcli.core.Parameters.parameter import TableParameter
from pollenisatorcli.core.Modules.module import Module
from pollenisatorcli.core.apiclient import APIClient
from terminaltables import AsciiTable
from prompt_toolkit.formatted_text import FormattedText
name = "Form" # Used in command decorator

@cls_commands
class FormModule(Module):
    def __init__(self, name, parent_context, description, prompt, completer, prompt_session):
        super().__init__(name, parent_context, description, prompt, completer, prompt_session)
        self.fields = []
        self.validateCommand = "(SEE HELP)"

    
    @command
    def set(self, parameter_name, value, *args):
        """Usage: set <parameter_name> <value>
        
        Description : Set the parameter to the given value

        Args:
            parameter_name  the parameter to change
            value           the value to give to the parameter
        """
        if args:
            value += " ".join(args) 
        for field in self.fields:
            field_name = field.name
            if isinstance(field, TableParameter) and "." in parameter_name:
                if field_name.lower() == parameter_name.split(".")[0]:
                    msg = field.setValue(parameter_name.split(".")[1], value)
                    if msg == "":
                        return field
                    else:
                        print_error(msg)
                        return None
            if field.name.lower() == parameter_name.lower():
                msg = field.setValue(value)
                if msg == "":
                    return field
                else:
                    print_error(msg)
                    return None
        print_error(f"Parameter {parameter_name} does not exist. Use command show to list available parameters")
        return None

    @command
    def unset(self, parameter_name):
        for field in self.fields:
            field_name = field.name
            if isinstance(field, TableParameter) and "." in parameter_name:
                if field_name.lower() == parameter_name.split(".")[0]:
                    msg = field.unsetValue(parameter_name.split(".")[1])
                    if msg == "":
                        return field
                    else:
                        print_error(msg)
                        return None
            if field.name.lower() == parameter_name.lower():
                msg = field.unsetValue()
                if msg == "":
                    return field
                else:
                    print_error(msg)
                    return None
        print_error(f"Parameter {parameter_name} does not exist. Use command show to list available parameters")
        return None


    

    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """
        Returns a list of valid options for the given cmd
        """  
        if cmd == "set":
            ret = []
            if len(cmd_args) == 1:
                params = cmd_args[0].split(".")
                field = self.getFieldByName(params[0])
                if isinstance(field, TableParameter):
                    for key in field.getKeys():
                        ret.append(cmd_args[0]+"."+key)
                if ret:
                    return ret
                ret = [x.name for x in self.fields if x.isWritable() and not x.hidden]
                return ret
            else: # param value to complete
                for field in self.fields:
                    if cmd_args[0].lower() == field.name.lower():
                        return field.getPossibleValues(cmd_args[1:], cmd_args[0])
        elif cmd == "unset":
            if len(cmd_args) <= 1: # param name to complete
                return [x.name for x in self.fields]
        elif cmd == "help":
            return [""]+self.__class__._cmd_list+[x.name for x in self.fields] # pylint: disable=no-member
        
        return []

    @command
    def show(self):
        """Usage: show
        
        Description : show the parameters and their assigned valued. required parameters ends with a *
        """ 
        msg = ""
        table_data = [['Parameters', 'Values']]
        other_tables = []
        for param in self.fields:
            if isinstance(param, TableParameter):
                other_tables.append(param)
            else:
                paramName = param.name+"*" if param.required else param.name
                paramName = paramName+"-" if param.readonly else paramName
                if not param.hidden:
                    table_data.append([paramName, param.getStrValue()])
                
        table = AsciiTable(table_data)
        table.inner_column_border = False
        table.inner_footing_row_border = False
        table.inner_heading_row_border = True
        table.inner_row_border = False
        table.outer_border = False
        
        msg = f"{table.table}\n"
        print_formatted(msg, 'important')

        for table in other_tables:
            print_formatted(f"\n{table.name}")
            print_formatted(table.getStrValue())
    
    def validateParam(self, param, value):
        return True

    def getParameterHelp(self, parameter_name):
        for x in self.fields:
            if x.name.lower() == parameter_name.lower() and not x.hidden:
                return x.getHelp()
        return None

    def getFieldByName(self, name):
        for field in self.fields:
            if field.name == name:
                return field
    
    def checkRequiredFields(self):
        for field in self.fields:
            if field.required and field.getValue() == "":
                print_error(f"Parameter {field.name} is required")
                return False
        return True
    
    @command
    def help(self, parameter_or_cmd_name=""):
        """Usage: help [parameter or command name]
        
        Description : show help menu or an helper on how to use the parameter or command name if one is given.
        """ 
        res = self.getCommandHelp(parameter_or_cmd_name)
        if res is not None and "not found" not in res:
            print_error(res)
            return
        res = self.getParameterHelp(parameter_or_cmd_name)
        if res is not None:
            print_error(res)
            return
        self.print_command_help() # Show help for Form only
        print_formatted("=================")
        print_formatted("""PARAMETERS :""")
        for x in self.fields:
            if not x.hidden and x.isWritable():
                print_formatted(f'\t{x.name}', 'parameter')
        print_formatted("""
For more information about any parameter or command type :""")
        print_formatted("help <parameter_name>", 'cmd')

    @command
    def wizard(self):
        """Usage: wizard

        Description : Will prompt every parameters 
        """
        self.set_context(FormWizard(self, self.prompt_session, self, self.validateCommand))
        
@cls_commands
class FormWizard(Module):
    def __init__(self, parent_context, prompt_session, form, validationCommand=" "):
        super().__init__('Wizard', parent_context, "Fill the form with a wizard. TAB to autocomplete", ">", None, prompt_session)
        self.form = form
        print_formatted("Wizard started : type help or exit at any moment. Type skip for not required parameters that you don't want to set", "info")
        self.current_field = -1
        self.validationCommand = validationCommand
        self.nextField()
    
    def nextField(self):
        self.current_field += 1
        if self.current_field >= len(self.form.fields):
            self.parent_context.show()
            print_formatted(f"Check values and use the command '{self.validationCommand}' to validate this form (help)", "warning")
            self.exit()
        else:
            if self.form.fields[self.current_field].hidden or self.form.fields[self.current_field].readonly:
                self.nextField()
            else:
                required = "*" if self.form.fields[self.current_field].required else ""
                self.prompt = FormattedText(
                    [('class:title', f"{self.parent_context.name} wizard"), ("class:subtitle", f" Set value of {self.form.fields[self.current_field].name}{required}"), ("class:angled_bracket", " > ")])
                self.prompt_session.message = FormattedText(
                    [('class:title', f"{self.parent_context.name} wizard"), ("class:subtitle", f" Set value of  {self.form.fields[self.current_field].name}{required}"), ("class:angled_bracket", " > ")])
                self.prompt_session.completer = ParamCompleter(self.form.fields[self.current_field].completor)
                self.completer = self.prompt_session.completer
                helper = self.form.fields[self.current_field].getHelp()
                if helper is not None:
                    print_formatted(self.form.fields[self.current_field].name +" : "+helper, 'parameter')
                    if not self.form.fields[self.current_field].required:
                        print_formatted(f"(skip to keep current value {self.form.fields[self.current_field].getValue()})", "parameter")

    def cmd_default(self, *args):
        args_str = " ".join(list(args))
        error_msg = ""

        if args_str == "skip":
            if self.form.fields[self.current_field].required:
                error_msg = f"{self.form.fields[self.current_field].name} cannot be skiped as it required"
        else:
            error_msg = self.form.fields[self.current_field].setValue(args_str)
        if error_msg != "":
            print_error(error_msg)
        else:
            self.nextField()
    
    @command
    def help(self):
        """Usage: help
        Description : show help
        """
        res = self.form.fields[self.current_field].getHelp()
        if res is not None:
            print_formatted(res, 'parameter')
        
