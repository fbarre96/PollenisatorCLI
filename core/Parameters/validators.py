from utils.utils import stringToDate

def validateDate(value):
    res = stringToDate(value)
    if res is None:
        return f"{value} is not a valide date. Expected format is 'dd/mm/YYYY hh:mm:ss'"
    return ""

def validateBool(value):
    return "" if value.lower() in ["true", "false"] else f"{value} is not a valide value. Expected format is 'true' or 'false'"