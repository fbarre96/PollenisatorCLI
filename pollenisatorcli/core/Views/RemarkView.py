from pollenisatorcli.core.Views.ViewElement import ViewElement
from terminaltables import AsciiTable
from pollenisatorcli.core.Parameters.parameter import Parameter, ComboParameter
from pollenisatorcli.utils.utils import command, cls_commands, print_error
from pollenisatorcli.core.apiclient import APIClient

@cls_commands
class RemarkView(ViewElement):
    name = "remark"
    def __init__(self, controller, parent_context, prompt_session, **kwargs):
        super().__init__(controller, parent_context, prompt_session, **kwargs)
        self.fields = [
            ComboParameter("type",  ["Positive", "Negative", "Neutral"], default=self.controller.model.type, required=True, helper="type of remark Positive, Negative or Neutral"),
            Parameter("title", required = True,  completor=self.getRemarksTitle, default=self.controller.model.title, helper="Remark title"),
        ]

    def getRemarksTitle(self, args):
        if not args:
            return []
        value = " ".join(args)
        if value.strip() == "" :
            return []
        res, msg = APIClient.searchRemark(value)
        ret = []
        if res is None:
            print_error(msg)
            return ret
        for r in res:
            ret.append(r["title"])
        return ret

    
    @classmethod
    def print_info(cls, remarks):
        pass
    