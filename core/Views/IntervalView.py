from core.Views.ViewElement import ViewElement
from terminaltables import AsciiTable
from colorclass import Color
from utils.utils import dateToString
from core.Models.Interval import Interval
from core.Controllers.IntervalController import IntervalController
from core.Models.Wave import Wave
from core.Parameters.parameter import DateParameter, ComboParameter
from utils.utils import command, cls_commands
from core.apiclient import APIClient

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
        if len(intervals) >= 1:
            table_data = [['Wave', 'Start date', 'End date']]
            for interval in intervals:
                if isinstance(interval, dict):
                    interval = Interval(interval)
                if isinstance(interval, IntervalController):
                    interval = interval.model
                table_data.append([interval.wave, interval.dated, interval.datef])
                table = AsciiTable(table_data)
                table.inner_column_border = False
                table.inner_footing_row_border = False
                table.inner_heading_row_border = True
                table.inner_row_border = False
                table.outer_border = False
            print(table.table)
        else:
            #No case
            pass