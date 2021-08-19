from pollenisatorcli.core.Controllers.ElementController import ElementController

class IntervalController(ElementController):

    def paramNameToDbName(self, param_name):
        translator = {"wave":"wave","start":"dated", "end":"datef"}
        return translator.get(param_name, None)


