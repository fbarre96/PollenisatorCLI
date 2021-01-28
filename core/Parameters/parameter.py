from utils.utils import stringToDate, dateToString
from datetime import date
from terminaltables import AsciiTable

class Parameter:
    def __init__(self, name, default=None, required=False, validator=None, completor=None, helper="", readonly=False):
        self.name = name
        self.value = default
        self.required = required
        self.readonly = readonly
        if validator is None:
            self.validator = self.defaultValidator
        else:
            self.validator = validator
        self.completor = completor
        self.help = helper
        self.hidden = False

    def getValue(self):
        return str(self)
    
    def getStrValue(self):
        return str(self.getValue())
    
    def setValue(self, value):
        if self.readonly:
            return "This is a readonly parameter"
        msg = self.validator(value)
        if msg == "":
            self.value = value
        return msg

    def unsetValue(self):
        if self.readonly:
            return "This is a readonly parameter"
        self.value = ""

    def __repr__(self):
        return str(self.value)
    
    def __str__(self):
        if self.value is None:
            return ""
        return str(self.value)

    def defaultValidator(self, value):
        return ""
    
    def getHelp(self):
        return self.help

    def getPossibleValues(self, args):
        if self.completor is None:
            return []
        if args is None:
            args = []
        return self.completor(args)

    @classmethod
    def getParametersValues(cls, parameters):
        ret = dict()
        for param in parameters:
            ret[param.name] = param.getValue()
        return ret

class BoolParameter(Parameter):
    def __init__(self, *args, **kwargs):
        keywords_args = kwargs
        keywords_args["validator"] = self.validateBool
        keywords_args["completor"] = lambda args: ["true", "false"]
        super().__init__(*args, **keywords_args)
    def validateBool(self, value):
        return "" if value.lower() in ["true", "false"] else f"{value} is not a valid value. Expected format is 'true' or 'false'"

    def getValue(self):
        return str(self.value).lower() == "true"
    
class IntParameter(Parameter):
    def __init__(self, *args, **kwargs):
        keywords_args = kwargs
        keywords_args["validator"] = self.validateInt
        super().__init__(*args, **keywords_args)
    

    def validateInt(self, value):
        try:
            conversion = int(value)
        except ValueError:
            return f"{value} is not a valid number value."
        return ""
    
    def getValue(self):
        return int(self.value)

def validateDate(value):
    res = stringToDate(value)
    if res is None:
        return f"{value} is not a valide date. Expected format is 'dd/mm/YYYY hh:mm:ss'"
    return ""

class DateParameter(Parameter):
    def __init__(self, *args, **kwargs):
        keywords_args = kwargs
        if kwargs.get("validator", None) is None:
            keywords_args["validator"] = validateDate
        keywords_args["completor"] = self.completeDate
        super().__init__(*args, **keywords_args)
    
    
    def completeDate(self, args):
        today = date.today()
        d1 = dateToString(today)
        return [d1]
    
    def getValue(self):
        return str(self.value)

class ListParameter(Parameter):
    def __init__(self, *args, **kwargs):
        keywords_args = kwargs
        self.elem_validator = keywords_args.get("validator", lambda args:  "")
        keywords_args["validator"] = self.validateList
        super().__init__(*args, **keywords_args)
    
    def validateList(self, args):
        values = args.split(",")
        for value in values:
            msg = self.elem_validator(value)
            if msg != "":
                return msg
        # Check duplicates
        setOfElems = set()
        for elem in values:
            if elem in setOfElems:
                return f"{elem} is duplicated in this list"
            else:
                setOfElems.add(elem)         
        return ""

    def getStrValue(self):
        try:
            return ",".join(self.value)
        except TypeError:
            return ""

    def getValue(self):
        if isinstance(self.value, str):
            return self.value.split(",")
        return self.value

    def setValue(self, value):
        if self.readonly:
            return "This is a readonly parameter"
        msg = self.validateList(value)
        if msg == "":
            self.value = value.split(",")
        return msg

class HiddenParameter(Parameter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hidden = True

    def getValue(self):
        return self.value

class ComboParameter(Parameter):
    def __init__(self, name, legalValues, *args, **kwargs):
        keywords_args = kwargs
        self.legalValues = legalValues
        keywords_args["completor"] = lambda args: self.legalValues
        super().__init__(name, *args, **keywords_args)
        
    def setValue(self, new_value):
        if self.readonly:
            return "This is a readonly parameter"
        if new_value not in self.legalValues:
            return f"{new_value} is not a in the list of valid values, which are : {', '.join(self.legalValues)}"
        self.value = new_value
        return ""


class TableParameter(Parameter):
    def __init__(self, name, headers, *args, **kwargs):
        self.name = name
        self.headers = headers
        keywords_args = kwargs
        self.value = {}
        keywords_args["validator"] = self.validateTable
        super().__init__(name, *args, **keywords_args)
    
    def validateTable(self, args):
        return ""

    def getStrValue(self):
        table_data = [self.headers]
        sorted_keys = sorted(list(self.value.keys()))
        if len(sorted_keys) == 0:
            table_data.append(["",""])
        for sorted_key in sorted_keys:
            key = sorted_key
            val = self.value[key]
            if isinstance(val, str):
                table_data.append([key, val])
            elif isinstance(val, list):
                table_data.append([key, str(val[0])])
                for val_i in range(1, len(val)):
                    table_data.append(["", val[val_i]])
        table = AsciiTable(table_data)
        table.inner_column_border = False
        table.inner_footing_row_border = False
        table.inner_heading_row_border = True
        table.inner_row_border = False
        table.outer_border = False
        return (table.table)

    def getValue(self):
        return self.value

    def getKeys(self):
        return sorted(list(self.value.keys()))

    def setValue(self, key, value):
        if "," in value:
            value = [x.strip() for x in value.split(",")]
        self.value[key] = value
        return ""

    def unsetValue(self, key):
        if key not in self.value:
            return f"{key} does not exists in this table"
        del self.value[key]
        return ""