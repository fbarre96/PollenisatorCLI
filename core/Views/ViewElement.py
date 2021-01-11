from colorclass import Color
from core.settings import Settings
from core.FormModules.formModule import FormModule
from utils.completer import IMCompleter
from prompt_toolkit.formatted_text import FormattedText
from utils.utils import command, cls_commands, print_error, print_formatted_text, print_formatted
from core.Parameters.parameter import Parameter
from core.apiclient import APIClient


@cls_commands
class ViewElement(FormModule):
    children_object_types = dict()
    name = "view"

    def __init__(self, controller, parent_context, prompt_session):
        self.controller = controller
        super().__init__(self.__class__.__name__, parent_context, f"View/Edit this {self.__class__.name} fields", FormattedText(
            [('class:title', f"{parent_context.name}"), ("class:subtitle", f" Edit {self.__class__.name} {controller.getDetailedString()}"), ("class:angled_bracket", " > ")]),
            IMCompleter(super()), prompt_session)
        self.is_insert = False
    
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
    def set(self, parameter_name, value):
        """Usage : set <parameter_name> <value>
        
        Description : Set the parameter to the given value

        Args:
            parameter_name  the parameter to change
            value           the value to give to the parameter
        """ 
        field_updated = super().set(parameter_name, value)
        if field_updated is not None and not self.is_insert:
            self.controller.doUpdate({parameter_name:field_updated.getValue()})
    
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
            "#ff0000", " permanently."), ("class:normal", "\nAre you sure? [No/yes]")])
        print_formatted_text(msg)
        result = input()
        if result.lower() == "yes":
            res = self.controller.doDelete()
            if int(res) == 1:
                print_formatted(f"Successfully delete this {self.__class__.name}", "valid")
    
    @command
    def show(self):
        """Usage: print

        Description: print info of this element
        """
        super().show()
        self.__class__.print_info([self.controller.model])

    def validateTag(self, value):
        tag_list = Settings.getTags().keys()
        if value.strip() not in tag_list:
            return f"{value} is not a validate tag, edit settings or choose an existing one ({', '.join(tag_list)})."
        return ""
    def getTags(self, args):
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
            for obt in objects:
                print(obt.getDetailedString())
            return True
        return False

    
    @command
    def edit(self, object_title):
        """Usage: edit <object_title>

        Description: edit object module:
        
        Arguments:
            object_title: a string to identify an object.
        """
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
        ret = super.getOptionsForCmd(cmd, cmd_args, complete_event)
        if ret:
            return ret
        if cmd in ["ls", "insert"]:
            return list(self.__class__.children_object_types.keys())
        elif cmd == "edit":
            return self.autoCompleteInfo(cmd_args, complete_event)
        return []


    @command
    def insert(self, object_type):
        """Usage: insert <child_object_type>

        Description: create a new child object in database
        """
        view = None
        for children_object_type in self.__class__.children_object_types:
            classe = self.__class__.children_object_types[children_object_type]
            if object_type == children_object_type:
                view = classe["view"](classe["controller"](classe["model"]({self.controller.getDbKey()})), self, self.prompt_session)
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