from pollenisatorcli.utils.utils import command, cls_commands, print_error, print_formatted, print_formatted_text
from pollenisatorcli.utils.completer import IMCompleter
from pollenisatorcli.core.Modules.GlobalModule import GlobalModule
from pollenisatorcli.core.apiclient import APIClient
from pollenisatorcli.core.Models.Command import Command
from pollenisatorcli.core.Models.CommandGroup import CommandGroup
from pollenisatorcli.core.Controllers.CommandController import CommandController
from pollenisatorcli.core.Controllers.CommandGroupController import CommandGroupController
from pollenisatorcli.core.Views.CommandView import CommandView
from pollenisatorcli.core.Views.CommandGroupView import CommandGroupView
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit import prompt
name = "Command templates" # Used in command decorator

@cls_commands
class CommandTemplate(GlobalModule):
    def __init__(self, parent_context, prompt_session):
        super().__init__('command_template', parent_context, "Edit command templates.", FormattedText([('class:title', "Command templates"),('class:angled_bracket', " > ")]), IMCompleter(self), prompt_session)
    

    @command
    def ls(self, object_type):
        """Usage: ls commands|group_commands

        Description: List all objects from the given type
        """
        if object_type == "commands":
            commands = Command.fetchObjects({})
            CommandView.print_info(commands)
            return True
        elif object_type == "group_commands":
            groupcommands = CommandGroup.fetchObjects({})
            CommandGroupView.print_info(groupcommands)
            return True
        return False

    def identifyPentestObjectsFromString(self, obj_str):
        
        commands = [CommandController(x) for x in Command.fetchObjects({"name":obj_str})]
        if commands:
            return CommandView, commands

        group_commands = [CommandGroupController(x) for x in CommandGroup.fetchObjects({"name":obj_str})]
        if group_commands:
            return CommandGroupView, group_commands
        return None, []

    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """  
        apiclient = APIClient.getInstance()
        if cmd == "help":
            return [""]+self.__class__._cmd_list
        elif cmd in ["ls", "insert"]:
            return ["commands", "group_commands"]
        elif cmd == "info":
            return self.autoCompleteInfo(cmd_args, complete_event)
        elif cmd == "edit":
            return self.autoCompleteInfo(cmd_args, complete_event)
        return []

    @command
    def info(self, object_title, called_by_default=False):
        """Usage: info <object_title>|commands|group_commands

        Description: Show informations for the given object title:
        
        Arguments:
            object_title: a string to identify an object. or a class of objects as a plural
            * commands|group_commands: equivalent to ls call
            * Command: a commands name
            * Command group: a group of commands name
        """
        if self.ls(object_title):
            return # Ls worked
        cls, objects_matching = self.identifyPentestObjectsFromString(object_title)
        if isinstance(cls, list):
            for classe_i, classe in enumerate(cls):
                classe.print_info(objects_matching[classe_i])
        elif cls is not None:
            cls.print_info(objects_matching) 
        else:
            if not called_by_default:
                print_formatted(f"No info regarding {object_title}")
            return False
        return True

    @command
    def edit(self, object_title, *args):
        """Usage: edit <object_title>

        Description: edit object module:
        
        Arguments:
            object_title: a string to identify an object.
            * Command: a commands name
            * Command group: a group of commands name
        """
        # will swap context to edit an object and access it's subobjects
        if len(args) >= 1:
            object_title += " "+(" ".join(args))
        cls, objects_matching = self.identifyPentestObjectsFromString(object_title)
        if isinstance(cls, list):
            print_formatted_text("Many objects founds:")
            for classe_i, classe in enumerate(cls):
                print_formatted_text(f"{classe_i+1}. {classe.name.capitalize()}")
            resp = None
            while resp is None:
                resp = prompt("which type do you want to edit ? (enter number)")
                try:
                    resp = int(resp)
                    if resp - 1 >= len(cls):
                        raise ValueError()
                except ValueError:
                    resp = None
            cls = cls[resp-1]
            objects_matching = objects_matching[resp-1]
        if cls is not None:
            if len(objects_matching) == 1:
                self.set_context(cls(objects_matching[0], self, self.prompt_session))
            else:
                cls.print_info(objects_matching)
        else:
            print_error(f"No object found matching this {object_title}")

    @command
    def insert(self, object_type):
        """Usage: insert commands|group_commands

        Description: create a new object in database
        """
        view = None
        if object_type == "commands":
            view = CommandView(CommandController(Command({"indb":"pollenisator"})), self, self.prompt_session)
        elif object_type == "group_commands":
            view = CommandGroupView(CommandGroupController(CommandGroup()), self, self.prompt_session)
        else:
            print_error(f"{object_type} is not a valid top level object type to insert.")
        if view is not None:
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
        object_title: a string to identify an object. or a class of objects as a plural
            * commands|group_commands
            * Command: a command name
            * Command group: a group of commands name
        """
        ls_objects = ["commands", "group_commands"]
        toComplete = cmd_args[0]
        ret = []
        if len(toComplete) == 0:
            return ls_objects
        for ls_object in ls_objects:
            if ls_object.startswith(toComplete):
                ret.append(ls_object)
        # COMPLETE COMMANDS
        ret += [x.name for x in Command.fetchObjects({"name":{"$regex":toComplete+".*"}})]
        # COMPLETE GROUP OF COMMAND 
        ret += [x.name for x in CommandGroup.fetchObjects({"name":{"$regex":toComplete+".*"}})]
        return ret