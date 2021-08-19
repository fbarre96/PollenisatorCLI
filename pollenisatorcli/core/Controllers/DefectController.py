from pollenisatorcli.core.Controllers.ElementController import ElementController

class DefectController(ElementController):
    

    def paramNameToDbName(self, param_name):
        if param_name == "types":
            return "type"
        return param_name

    @classmethod
    def getEases(cls):
        return ["Easy", "Moderate", "Difficult", "Arduous", "N/A"]
    
    @classmethod
    def getImpacts(cls):
        return ["Minor", "Important","Major", "Critical", "N/A"]
    
    @classmethod
    def getRisks(cls):
        return cls.getImpacts()
