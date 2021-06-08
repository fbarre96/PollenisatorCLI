from utils.utils import command, cls_commands, print_error, print_formatted, print_formatted_text, execute
from utils.completer import IMCompleter
from core.apiclient import APIClient
from prompt_toolkit.formatted_text import FormattedText
from terminaltables import AsciiTable
from core.settings import Settings
from core.FormModules.formModule import FormModule
from core.Models.Defect import Defect
from core.Models.Remark import Remark
from core.Views.DefectView import DefectView
from core.Views.RemarkView import RemarkView
from core.Controllers.DefectController import DefectController
from core.Controllers.ElementController import ElementController

from core.Parameters.parameter import Parameter, ComboParameter
from colorclass import Color
from prompt_toolkit.shortcuts import confirm
from bson import ObjectId
import os
from shutil import which
from prompt_toolkit.shortcuts import ProgressBar
from prompt_toolkit import ANSI

@cls_commands
class Report(FormModule):
    def __init__(self, parent_context, prompt_session):
        self.risk_colors = {"Mineur":"autoblue", "Important":"autoyellow", "Majeur":"autored", "Critique":"autoblack"}
        super().__init__('Report', parent_context, "Reporting module.", FormattedText([('class:title', "Report"),('class:angled_bracket', " > ")]), IMCompleter(self), prompt_session)
        settings = Settings()
        settings.reloadSettings()
        pentest_type = settings.getPentestType().lower()
        templates = APIClient.getInstance().getTemplateList()
        self.docx_models = [f for f in templates if f.endswith(".docx")]
        self.pptx_models = [f for f in templates if f.endswith(".pptx")]
        pentesttype_docx_models = [f for f in self.docx_models if pentest_type in f.lower()]
        default_word_model = None
        if pentesttype_docx_models:
            default_word_model = pentesttype_docx_models[0]
        elif self.docx_models:
            default_word_model = self.docx_models[0]

        pentesttype_pptx_models = [f for f in self.pptx_models if pentest_type in f.lower()]
        default_ppt_model = None
        if pentesttype_pptx_models:
            default_ppt_model = pentesttype_pptx_models[0]
        elif self.pptx_models:
            default_ppt_model = self.pptx_models[0]
        self.fields = [
            Parameter("client", required=True, helper="The client name to use for the report"),
            Parameter("contract", required=True, helper="The mission title"),
            ComboParameter("word_template", self.docx_models, default=default_word_model, required=True, helper="The template to use to generate a word report. Use download command to see them"),
            ComboParameter("powerpoint_template", self.pptx_models, default=default_ppt_model, required=True, helper="The template to use to generate a powerpoint report. Use download command to see them"),
        ]
        self.mainRedac = "N/A"
        self.defects_ordered = []
        self.remarks_list = []
        self.show()
    
    @command
    def show(self):
        """Usage: show
        Description: Show the form and the report table
        """
        super().show()
        self.updateDefectList()
        self.printReport()
        self.updateRemarkList()
        self.printRemarks()

    def updateDefectList(self):
        self.defects_ordered = []
        for line in Defect.getDefectTable():
            self.defects_ordered.append(Defect(line))
    
    def updateRemarkList(self):
        apiclient = APIClient.getInstance()
        self.remarks_list = [x for x in apiclient.find("remarks", {})]

    def printReport(self):
        table_data = [['ID', 'Title', 'Ease', 'Impact', 'Risk', 'Type', 'Redactor']]
        for i, defect_o in enumerate(self.defects_ordered):
            types = defect_o.mtype
            types = ", ".join(defect_o.mtype)
            risk_str = Color("{"+self.risk_colors[defect_o.risk]+"}"+defect_o.risk+"{/"+self.risk_colors[defect_o.risk]+"}")
            table_data.append([i+1, defect_o.title, defect_o.ease, defect_o.impact, risk_str, types, defect_o.redactor])
        table = AsciiTable(table_data,' Report ')
        print_formatted_text(ANSI(table.table))

    def printRemarks(self):
        table_data = [['ID', 'Type', 'Title']]
        for i, remark in enumerate(self.remarks_list):
            table_data.append([str(i+1), remark["type"], remark["title"]])
        table = AsciiTable(table_data,' Remarks ')
        print_formatted_text(ANSI(table.table))

    def getDefectWithId(self, defect_id):
        try:
            defect_n = int(defect_id)
            if defect_n < 1 or defect_n > len(self.defects_ordered):
                raise ValueError(f"{defect_id} must be a number between 1 and {len(self.defects_ordered)}")
            return self.defects_ordered[defect_n-1]
        except ValueError:
            raise ValueError(f"{defect_id} is not a number")

    @command
    def move(self, defect_id, target_id):
        """Usage : move <defect_id> <line id to go to>
        Description : Change the defect order by moving a defect to another line, sliding every other line below
        Args:
            defect_id : the defect to move line number
            target_id : the targeted line id,  the defect already there will be moved down.
        """
        try:
            target_n = int(target_id)
            if target_n < 1 or target_n > len(self.defects_ordered)+1:
                print_error(f"{target_id} must be between 1 and {len(self.defects_ordered)}")
                return
        except ValueError:
            print_error(f"{target_id} is not a valid number")
            return
        else:
            target_defect = self.getDefectWithId(target_id)
        try:
            defect_o = self.getDefectWithId(defect_id)
        except ValueError as e:
            print_error(e)
            return
        else:
            apiclient = APIClient.getInstance()
            apiclient.moveDefect(defect_o.getId(), target_defect.getId())
            self.show()
        
    @command
    def remove(self, defect_id):
        """Usage : remove <defect_id>
        Description : Remove the defect 
        Args:
            defect_id : the defect id to remove
        """
        try:
            defect_o = self.getDefectWithId(defect_id)
            answer = confirm(f"Are you sure you want to delete defect {defect_o.title}?")
            if not answer:
                return
            defectToDelete = Defect.fetchObject({"title": defect_o.title, "ip":"", "port":"", "proto":""})
            defectToDelete.delete()
        except ValueError as e:
            print_error(e)
            return
   
    @command 
    def setMainRedactor(self, main_redac_name):
        """Usage : setMainRedactor <main_redac_name>
        Description : Change all redactors N/A to this redactor's name
        Args:
            main_redac_name : the pentester name to replace N/A. Must exists in the pentest settings
        """
        settings = Settings()
        settings._reloadDbSettings()
        pentesters = settings.getPentesters()
        if main_redac_name not in pentesters:
            print_error(f"{main_redac_name} is not in pentesters settings")
            return 
        for defect in self.defects_ordered:
            if defect.redactor == "N/A":
                defect.redactor = main_redac_name
                defect.update({"redactor":defect.redactor})
        self.mainRedac = main_redac_name
    
    @command
    def edit(self, defect_id):
        """Usage : edit <defect_id>
        Description : edit the defect 
        Args:
            defect_id : the defect id to edit
        """
        defect_o =self.getDefectWithId(defect_id)
        self.set_context(DefectView(DefectController(defect_o), self, self.prompt_session))

    @command
    def add_defect(self):
        """Usage : add_defect 
        Description : add a global defect in database
        """
        view = DefectView(DefectController(Defect({"ip":""})), self, self.prompt_session, is_insert=True)
        self.set_context(view)

    @command
    def add_remark(self):
        """Usage : add_remark
        Description : add a remark in database
        """
        view = RemarkView(ElementController(Remark()), self, self.prompt_session, is_insert=True)
        self.set_context(view)
        self.updateRemarkList()
    
    @command
    def remove_remark(self, remarkID):
        """Usage : remove_remark <remarkID>s
        Description : remove a remark in database
        """
        try:
            remark_o = Remark(self.remarks_list[int(remarkID)-1])
            remark_o.delete()
        except ValueError:
            print_error("Second argument should be a number")
        except IndexError:
            print_error("Invalid id given")

    @command
    def generate(self, report_type):
        """Usage : generate <"word"|"powerpoint">
        Description : request a report based on the defect table
        Args:
            report_type: either "word" or "powerpoint"
        """
        if not super().checkRequiredFields():
            return
        values = Parameter.getParametersValues(self.fields)
        apiclient = APIClient.getInstance()
        toExport = apiclient.getCurrentPentest()
        if toExport != "":
            if report_type == "word":
                modele = values["word_template"]
            elif report_type == "powerpoint" or report_type == "ppt":
                modele = values["powerpoint_template"]
            res = None
            with ProgressBar() as pb:
                for i in pb(range(1)):
                    res = apiclient.generateReport(modele, values["client"].strip(), values["contract"], self.mainRedac)
            if res is None:
                print_error(str(res))
                return
            print_formatted(f"The document was generated in {res}", "success")
            if which("xdg-open"):
                os.system("xdg-open "+os.path.dirname(res))
            elif which("explorer"):
                os.system("explorer "+os.path.dirname(res))
            elif which("open"):
                os.system("open "+os.path.dirname(res))
    @command
    def download(self, template_name):
        """Usage : download  <template_name>
        Description : add a global defect in database
        """
        apiclient = APIClient.getInstance()
        path = apiclient.downloadTemplate(template_name)
        if path is None:
            print_error("Download failed.")
        if which("xdg-open") is not None:
            answer = confirm(f"Template downloaded here {path}. Do you want to open it ?")
            if answer:
                if which("xdg-open"):
                    os.system("xdg-open "+str(path))
                elif which("explorer"):
                    os.system("explorer "+str(path))
                elif which("open"):
                    os.system("open "+str(path))
                return
        else:
            print_formatted(f"The template was generated in {path}",cls="valid")

    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """  
        apiclient = APIClient.getInstance()
        ret = super().getOptionsForCmd(cmd, cmd_args, complete_event)
        if ret:
            return ret
        if cmd == "download":
            return self.docx_models + self.pptx_models
        elif cmd == "generate":
            return ["word", "powerpoint"]
        elif cmd in ["edit", "move", "remove"]:
            return [str(x) for x in range(1, len(self.defects_ordered)+1)]
        elif cmd == "setMainRedactor":
            settings = Settings()
            settings._reloadDbSettings()
            pentesters = settings.getPentesters()
            return pentesters
        return []   