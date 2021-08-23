from pollenisatorcli.core.Controllers.ElementController import ElementController

class WorkerController(ElementController):
    def set_inclusion(self):
        return self.model.set_inclusion()

