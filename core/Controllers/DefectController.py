from core.Controllers.ElementController import ElementController

class DefectController(ElementController):
    

    def paramNameToDbName(self, param_name):
        if param_name == "types":
            return "type"
        return param_name

    @classmethod
    def getEases(cls):
        return ["Facile", "Modérée", "Difficile", "Très difficile", "N/A"]
    
    @classmethod
    def getImpacts(cls):
        return ["Mineur", "Important","Majeur", "Critique", "N/A"]
    
    @classmethod
    def getRisks(cls):
        return cls.getImpacts()
