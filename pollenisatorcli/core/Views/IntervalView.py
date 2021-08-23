from pollenisatorcli.core.Views.ViewElement import ViewElement
from terminaltables import AsciiTable
from colorclass import Color
from prompt_toolkit import ANSI
from pollenisatorcli.utils.utils import dateToString
from pollenisatorcli.core.Models.Interval import Interval
from pollenisatorcli.core.Controllers.IntervalController import IntervalController
from pollenisatorcli.core.Models.Wave import Wave
from pollenisatorcli.core.Parameters.parameter import DateParameter, ComboParameter
from pollenisatorcli.utils.utils import command, cls_commands, style_table, print_formatted_text
from pollenisatorcli.core.apiclient import APIClient
name = "Interval" # Used in command decorator

@cls_commands
class IntervalView(ViewElement):
    name = "interval"

    def __init__(self, controller, parent_context, prompt_session, **kwargs):
        super().__init__(controller, parent_context, prompt_session, **kwargs)
        apiclient = APIClient.getInstance()
        wave_list = apiclient.find("waves", {})
        wave_names = []
        for wave in wave_list:
            wave_names.append(wave.wave)
        self.fields = [
            ComboParameter("wave", wave_names, required=True, readonly=self.controller.model.wave != "", default=self.controller.model.wave,
                      helper="The wave this interval is declared on"),
            DateParameter("start",  required=True, default=self.controller.model.dated,
                      helper="The starting time of this interval"),        
            DateParameter("end",  required=True, default=self.controller.model.datef,
                      helper="The ending time of this interval"),    
        ]
        

    @classmethod
    def print_info(cls, intervals):
        if intervals:
            table_data = [['Wave', 'Start date', 'End date']]
            for interval in intervals:
                if isinstance(interval, dict):
                    interval = Interval(interval)
                if isinstance(interval, IntervalController):
                    interval = interval.model
                table_data.append([interval.wave, interval.dated, interval.datef])
            table = AsciiTable(table_data)
            table = style_table(table)
            print_formatted_text(ANSI(table.table+"\n"))
        else:
            #No case
            pass