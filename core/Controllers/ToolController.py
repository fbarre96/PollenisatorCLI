from core.Controllers.ElementController import ElementController

class ToolController(ElementController):

    def paramNameToDbName(self, param_name):
        return param_name


    def getStatus(self):
        return self.model.getStatus()

    def getOutputDir(self, pentest):
        return self.model.getOutputDir(pentest)

    def getDbId(self):
        return self.model.getId()