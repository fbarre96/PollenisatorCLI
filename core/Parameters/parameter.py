from core.Parameters.validators import validateBool

class Parameter:
    def __init__(self, name, default=None, required=True, validator=None, completor=None, helper=""):
        self.name = name
        self.value = default
        self.required = required
        if validator is None:
            self.validator = self.defaultValidator
        else:
            self.validator = validator
        self.completor = completor
        self.help = helper

    def getValue(self):
        return str(self)
    
    def setValue(self, value):
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

    def getPossibleValues(self):
        if self.completor is None:
            return []
        return self.completor()

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
        keywords_args["completor"] = lambda: ["true", "false"]
        super().__init__(*args, **keywords_args)
    
    def getValue(self):
        return self.value.lower() == "true"