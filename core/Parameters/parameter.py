from core.Parameters.validators import validateBool, validateInt

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
        keywords_args["validator"] = validateBool
        keywords_args["completor"] = lambda args: ["true", "false"]
        super().__init__(*args, **keywords_args)
    
    def getValue(self):
        return str(self.value).lower() == "true"
    
class IntParameter(Parameter):
    def __init__(self, *args, **kwargs):
        keywords_args = kwargs
        keywords_args["validator"] = validateInt
        super().__init__(*args, **keywords_args)
    
    def getValue(self):
        return int(self.value)

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
        return ""

    def getStrValue(self):
        return ",".join(self.value)

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