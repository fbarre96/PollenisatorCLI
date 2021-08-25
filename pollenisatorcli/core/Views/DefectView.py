from pollenisatorcli.core.Views.ViewElement import ViewElement
from terminaltables import AsciiTable
from colorclass import Color
from pollenisatorcli.core.Models.Defect import Defect
from pollenisatorcli.core.Controllers.DefectController import DefectController
from pollenisatorcli.core.Parameters.parameter import Parameter, BoolParameter, IntParameter, ListParameter, HiddenParameter, ComboParameter
from pollenisatorcli.core.settings import Settings
from pollenisatorcli.core.apiclient import APIClient
from pollenisatorcli.utils.utils import command, cls_commands, print_error, print_formatted_text, style_table
from prompt_toolkit import ANSI
name = "Defect" # Used in command decorator


@cls_commands
class DefectView(ViewElement):
    name = "defect"
    def __init__(self, controller, parent_context, prompt_session, **kwargs):
        super().__init__(controller, parent_context, prompt_session, **kwargs)
        settings = Settings()
        settings.reloadSettings()
        defectTypes = settings.getPentestTypes()
        defect_types = defectTypes[settings.getPentestType()]
        for savedType in self.controller.model.mtype:
            if savedType.strip() not in defect_types:
                defect_types.insert(0, savedType)
        self.fields = [
            HiddenParameter("port", default=self.controller.model.port),
            HiddenParameter("ip", default=self.controller.model.ip),
            HiddenParameter("proto", default=self.controller.model.proto),
            Parameter("title", required = True,  completor=self.getDefectsTitle, default=self.controller.model.title, helper="Defect title"),
            ComboParameter("ease",  DefectController.getEases(), default=self.controller.model.ease, required=True, helper="ease of exploitation: \n0: Trivial to exploit, no tool required\n1: Simple technics and public tools needed to exploit\n2: public vulnerability exploit requiring security skills and/or the development of simple tools.\n3: Use of non-public exploits requiring strong skills in security and/or the development of targeted tools"),
            ComboParameter("impact",  DefectController.getImpacts(), default=self.controller.model.impact, required=True, helper="0: No direct impact on system security\n1: Impact isolated on precise locations of pentested system security\n2: Impact restricted to a part of the system security.\n3: Global impact on the pentested system security."),
            ComboParameter("risk",  DefectController.getRisks(), default=self.controller.model.risk, required=False, helper="0: small risk that might be fixed\n1: moderate risk that need a planed fix\n2: major risk that need to be fixed quickly.\n3: critical risk that need an immediate fix or an immediate interruption."),
            ListParameter("types", default=self.controller.model.mtype, validator=lambda value, field: "" if value in defect_types else "Not a valid type", completor=lambda args: defect_types),
            Parameter("notes", default=self.controller.model.notes, helper="A space to take notes. Will appear in word report"),
            ListParameter("tags", default=self.controller.model.tags, validator=self.validateTag, completor=self.getTags, helper="Tag set in settings to help mark a content with a caracteristic"),

        ]
        if self.controller.model.isAssigned():
            self.fields.append(ComboParameter("redactor",  settings.getPentesters()+["N/A"], default=self.controller.model.redactor, required=False, helper="Assign a pentester to redact this defect."))

    def getDefectsTitle(self, args, _cmd):
        if not args:
            return []
        value = " ".join(args)
        if value.strip() == "" :
            return []
        res, msg = APIClient.searchDefect(value)
        ret = []
        if res is None:
            print_error(msg)
            return ret
        for r in res:
            ret.append(r["title"])
        return ret

    @command
    def set(self, parameter_name, value, *args):
        """Usage: set <parameter_name> <value>
        
        Description : Set the parameter to the given value

        Args:
            parameter_name  the parameter to change
            value           the value to give to the parameter
        """ 
        if args:
            value += " "+(" ".join(args)) 
        super().set(parameter_name, value)
        if parameter_name == "ease" or parameter_name == "impact":
            ease = self.getFieldByName("ease").getStrValue()
            impact = self.getFieldByName("impact").getStrValue()
            risk = Defect.getRisk(ease, impact)
            self.set("risk", risk)
        elif parameter_name == "title":
            res, msg = APIClient.searchDefect(value)
            if res is None:
                print_error(msg)
                return
            if len(res) == 1:
                res = res[0]
                self.set("ease", res["ease"])
                self.set("impact", res["impact"])
                self.set("types", res["type"])


    @classmethod
    def print_info(cls, defects):
        if defects:
            table_data = [['Title', 'Risk']]
            for defect in defects:
                if isinstance(defect, dict):
                    defect = Defect(defect)
                if isinstance(defect, DefectController):
                    defect = defect.model
                title_str = ViewElement.colorWithTags(defect.getTags(), defect.getDetailedString())
                risks_colors = {"Critical":"autoblack", "Major":"autored", "Important":"automagenta", "Minor":"autoyellow", "":"autowhite"}
                risk_str = Color("{"+risks_colors.get(defect.risk, "autowhite")+"}"+defect.risk+"{/"+risks_colors.get(defect.risk,"autowhite")+"}")
                table_data.append([title_str, risk_str])
            table = AsciiTable(table_data)
            table = style_table(table)
            print_formatted_text(ANSI(table.table+"\n"))
        else:
            #No case
            pass
    