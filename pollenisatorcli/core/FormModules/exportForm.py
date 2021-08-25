from pollenisatorcli.utils.utils import command, cls_commands, print_error, print_formatted, getExportDir
from pollenisatorcli.utils.completer import IMCompleter
from pollenisatorcli.core.FormModules.formModule import FormModule
from pollenisatorcli.core.Parameters.parameter import ListParameter, Parameter
from pollenisatorcli.core.settings import Settings
from pollenisatorcli.core.apiclient import APIClient
from prompt_toolkit.formatted_text import FormattedText
import os
import csv
name = "New pentest form" # Used in command decorator

@cls_commands
class exportForm(FormModule):
    def __init__(self, selection, parent_context, prompt_session):
        super().__init__('Export', parent_context, "Export the selection of items.", FormattedText(
            [('class:title', f"{parent_context.name}"), ("class:subtitle", f" Export form"), ("class:angled_bracket", " > ")]), IMCompleter(self), prompt_session)
        self.selection = selection
        self.fields = [
            Parameter("name", default=f"export.csv", required=True)
        ]
        for types, documents in self.selection.items():
            if documents:
                self.fields.append(ListParameter(f"{types}_fields", default=documents[0].keys(), validator=lambda value, field: "" if value in self.selection[field.name.split("_")[0]][0].keys() else f"Invalid value {value}",
                                        completor=self.getFieldCompletion))
        self.validateCommand = "export"

    @command
    def export(self):
        """Usage: export

        Description: export objects with choosen fields
        """
        if not super().checkRequiredFields():
            return
        values = Parameter.getParametersValues(self.fields)
        csv_filename = os.path.join(getExportDir(), str(values["name"]))
        
        headers = set(["type"])
        for key, value in values.items():
            if key.endswith("_fields"):
                for fieldToExport in value:
                    headers.add(fieldToExport.strip())
        with open(csv_filename, 'w', newline='') as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(headers)
            for types, documents in self.selection.items():
                if documents:
                    toExport = ["type"]+list(values[f"{types}_fields"])
                    for document in documents:
                        line = []
                        document["type"] = types
                        for header in headers:
                            if header in toExport:
                                line.append(str(document.get(header,"")))
                            else:
                                line.append("")
                        writer.writerow(line)
        print_formatted(f"Generated {csv_filename}", "success")

    
    def getFieldCompletion(self, args, cmd):
        ret = []
        types = cmd.split("_")[0]
        for valide_key in self.selection[types][0].keys():
            if valide_key.startswith(args[-1]):
                ret.append(valide_key+",")
        return ret
  