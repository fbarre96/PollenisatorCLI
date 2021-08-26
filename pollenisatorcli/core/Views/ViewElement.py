from colorclass import Color
from pollenisatorcli.core.settings import Settings
from pollenisatorcli.core.FormModules.formModule import FormModule
from pollenisatorcli.utils.completer import IMCompleter
from prompt_toolkit.formatted_text import FormattedText
from pollenisatorcli.utils.utils import command, cls_commands, print_error, print_formatted_text, print_formatted
from pollenisatorcli.core.Parameters.parameter import Parameter, TableParameter
from pollenisatorcli.core.apiclient import APIClient
from prompt_toolkit import ANSI
name = "Pentest objects" # Used in command decorator

@cls_commands
class ViewElement(FormModule):
    children_object_types = dict()
    name = "view"

    def __init__(self, controller, parent_context, prompt_session, **kwargs):
        self.parent_context = parent_context
        self.controller = controller
        self.prompt_session = prompt_session
        self.updatePrompt()
        self.is_insert = kwargs.get("is_insert", False)
        self.validateCommand = "submit"


    def updatePrompt(self):
        super().__init__(self.__class__.name, self.parent_context, f"View/Edit this {self.__class__.name} fields", FormattedText(
            [('class:title', f"{self.parent_context.name}"), ("class:subtitle", f" Edit {self.__class__.name} {self.controller.getDetailedString()}"), ("class:angled_bracket", " > ")]),
            IMCompleter(self), self.prompt_session)
    
    @classmethod
    def print_info(cls, objs):
        for elem in objs:
            print(str(elem))
    
    @classmethod
    def colorWithTags(cls, tags, string):
        definedTags = Settings.getTags()
        for tag in tags:
            if tag in list(definedTags.keys()):
                color = definedTags[tag]
                string = Color("{"+color+"}"+string+"{/"+color+"}")
                break
        return string
    
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
        field_updated = super().set(parameter_name, value)
        if field_updated is not None and not self.is_insert:
            self.controller.doUpdate({field_updated.name:field_updated.getValue()})
    
    @command
    def submit(self):
        """Usage: submit

        Description: Insert this element in database
        """
        if not super().checkRequiredFields():
            return
        values = Parameter.getParametersValues(self.fields)
        self.controller.doInsert(values)

    @command
    def delete(self):
        """Usage: delete

        Description: Delete this element from database
        """
        msg = FormattedText([("class:warning", "WARNING :"), ("class:normal", f" You are going to delete {self.controller.getDetailedString()}"), (
            "#ff0000", " permanently."), ("class:normal", "\nAre you sure? ")])
        print_formatted_text(msg)
        from prompt_toolkit.shortcuts import confirm
        result = confirm("")
        if result:
            res = self.controller.doDelete()
            if int(res) == 1:
                print_formatted(f"Successfully delete this {self.__class__.name}", "valid")
        self.exit()
    
    @command
    def show(self):
        """Usage: print

        Description: print info of this element
        """
        self.__class__.print_info([self.controller.model])
        print_formatted("\n")
        super().show()
        

    def validateTag(self, value, field):
        tag_list = Settings.getTags().keys()
        if value.strip() not in tag_list:
            return f"{value} is not a validate tag, edit settings or choose an existing one ({', '.join(tag_list)})."
        return ""

    def getTags(self, args, _cmd=""):
        ret = []
        tag_list = list(Settings.getTags().keys())
        for tag in tag_list:
            if tag.startswith(args[-1]):
                ret.append(tag+",")
        return ret

    @command
    def ls(self, object_type):
        """Usage: ls <children_object_type>

        Description: Will list direct children of this object if their type matches object type 

        Args:
            children_object_type: a children object type like port, tool, defect
        """
        if object_type in self.__class__.children_object_types:
            objects = self.__class__.children_object_types[object_type]["model"].fetchObjects(self.controller.model.getDbKey())
            self.__class__.children_object_types[object_type]["view"].print_info(objects)
            return True
        return False

    @command
    def tools(self):
        """Usage: tools

        Description: Interact with tools associated with this object
        """
        from pollenisatorcli.core.Modules.ToolModule import ToolModule
        if "tools" in self.__class__.children_object_types:
            tools = [tool for tool in self.__class__.children_object_types["tools"]["model"].fetchObjects(self.controller.model.getDbKey())]
            self.set_context(ToolModule(self.controller.model.getDetailedString(), self, self.prompt_session, tools))
        else:
            print_error("This context cannot have tools attached to it")

    @command
    def recap(self, status="all"):
        """Usage: recap ["done"|"error"|"running"|"ready"|"all"]
        Args:
            status: recap only the tools with the given status. If not set, all will be done
            
        Description: print info about each tools.
        """
        from pollenisatorcli.core.Modules.ToolModule import ToolModule
        if "tools" in self.__class__.children_object_types:
            tools = [tool for tool in self.__class__.children_object_types["tools"]["model"].fetchObjects(self.controller.model.getDbKey())]
            ToolModule(self.controller.model.getDetailedString()+" Tools", self, self.prompt_session, tools).recap(status)
        else:
            print_error("This context does not have tools attached to it")

    
    @command
    def edit(self, object_title, *args):
        """Usage: edit <object_title>

        Description: edit object module:
        
        Arguments:
            object_title: a string to identify an object.
        """
        if len(args) >= 1:
            object_title += " "+(" ".join(args))
        # will swap context to edit an object and access it's subobjects
        cls, objects_matching = self.identifyPentestObjectsFromString(object_title)
        if cls is not None:
            if len(objects_matching) == 1:
                self.set_context(cls(objects_matching[0], self, self.prompt_session))
            else:
                cls.print_info(objects_matching)
        else:
            print_error(f"No object found matching this {object_title}")

    def identifyPentestObjectsFromString(self, obj_str):
        """To be overwritten in sublclasses
        """
        return None, []
    
    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """  
        
        if cmd == "ls":
            return list(self.__class__.children_object_types.keys())
        elif cmd == "insert":
            return [x[:-1] for x in (self.__class__.children_object_types.keys())]
        elif cmd == "edit":
            return self.autoCompleteInfo(cmd_args, complete_event)
        ret = super().getOptionsForCmd(cmd, cmd_args, complete_event)
        if ret:
            return ret
        return []

    @command
    def insert(self, object_type, *args):
        """Usage: insert <child_object_type>

        Description: create a new child object in database
        """
        view = None
        for children_object_type in self.__class__.children_object_types:
            classe = self.__class__.children_object_types[children_object_type]
            if object_type+"s" == children_object_type:
                view = classe["view"](classe["controller"](classe["model"](self.controller.getDbKey())), self, self.prompt_session)
        if view is None:
            print_error(f"{object_type} is not a valid children level object type to insert.")
        else:
            view.is_insert = True
            self.set_context(view)

    def autoCompleteInfo(self, cmd_args, complete_event):
        """
        Returns auto complete possibilites for the "info" cmd
        Args:
            cmd_args: the current list of arguments given to info cmd (not completed)
            complete_event: the Completer event
        Returns:
            A list of suggestion for completion. 
            Starts by returning the object_titles if matches
        """
        #No optimal
        ret = []
        for children_type in self.__class__.children_object_types:
            objects = self.__class__.children_object_types[children_type]["model"].fetchObjects(self.controller.model.getDbKey())
            ret += [str(x) for x in objects]
        return ret
    
    