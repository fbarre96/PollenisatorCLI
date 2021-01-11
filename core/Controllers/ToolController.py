from core.Controllers.ElementController import ElementController

class ToolController(ElementController):

    def paramNameToDbName(self, param_name):
        return param_name


