from colorclass import Color
from core.settings import Settings

class ViewElement:
    def __init__(self, controller):
        self.controller = controller
    
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