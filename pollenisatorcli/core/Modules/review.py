from pollenisatorcli.utils.utils import command, cls_commands, print_error, print_formatted
from pollenisatorcli.utils.completer import IMCompleter
from pollenisatorcli.core.Modules.module import Module
from pollenisatorcli.core.settings import Settings
from pollenisatorcli.core.apiclient import APIClient
from prompt_toolkit.formatted_text import FormattedText
from pollenisatorcli.core.Views.CommandView import CommandView
from pollenisatorcli.core.Views.WaveView import WaveView
from pollenisatorcli.core.Views.ScopeView import ScopeView
from pollenisatorcli.core.Views.IpView import IpView
from pollenisatorcli.core.Views.PortView import PortView
from pollenisatorcli.core.Views.DefectView import DefectView
from pollenisatorcli.core.Views.ToolView import ToolView
name = "Review" # Used in command decorator

@cls_commands
class ReviewModule(Module):
    def __init__(self, toReview, parent_context, prompt_session):
        self.count = len(toReview)
        super().__init__('Review', parent_context, "Review a selection of items.", FormattedText(
            [('class:title', f"{parent_context.name}"), ("class:subtitle", f" Reviewing {self.count} objects"), ("class:angled_bracket", " > ")]), IMCompleter(self), prompt_session)
        self.toReview = toReview
        self.current = self.toReview[0]
        self.printCurrent()
        

    def nextSelection(self):
        if self.toReview:
            del self.toReview[0]
            self.count -= 1
            self.prompt_session.message = FormattedText([('class:title', f"{self.parent_context.name}"), ("class:subtitle", f" Reviewing {self.count} objects"), ("class:angled_bracket", " > ")])
            if self.toReview:
                self.current = self.toReview[0]
                self.printCurrent()
            else:
                self.exit()
        else:
            self.exit()

    def printCurrent(self):
        print_formatted(self.current.getDetailedString(), cls="title")
        print_formatted(self.current.notes)

    @command
    def skip(self):
        """Usage: skip
        Description: skip current object
        """
        self.nextSelection()
    
    @command
    def next(self):
        """Usage: next
        Description: skip current object (alias of skip)
        """
        self.skip()

    @command
    def tag(self, tag_name):
        """Usage: tag <tag_name>
        Description: Tag the current object
        """
        settings = Settings()
        settings._reloadDbSettings()
        tags = settings.getTags()
        if tag_name not in tags:
            print_error(f"{tag_name} is not a registered tag ({tags})")
            return
        self.current.addTag(tag_name)
        self.next()

    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """  
        if cmd == "tag":
            if len(cmd_args) == 1:
                settings = Settings()
                settings._reloadDbSettings()
                tags = settings.getTags()
                return tags
        return []