from functools import wraps
from terminaltables import AsciiTable
import re
import time
import requests
import json
import os
from datetime import datetime
from bson import ObjectId

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return "ObjectId|"+str(o)
        elif isinstance(o, datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)

class JSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
        
    def object_hook(self, dct):
        for k,v in dct.items():
            if 'ObjectId|' in str(v):
                dct[k] = ObjectId(v.split('ObjectId|')[1])
        return dct

class CmdError(Exception):
    pass

def loadCfg(cfgfile):
    """
    Load a json config file.
    Args:
        cfgfile: the path to a json config file
    Raises:
        FileNotFoundError if the given file does not exist
    Returns:
        Return the json converted values of the config file.
    """
    infos = dict()
    try:
        with open(cfgfile, "r") as f:
            infos = json.loads(f.read())
    except FileNotFoundError as e:
        raise e
    return infos

def saveCfg(content, cfgfile):
    """
    Save in a json config file. Replace if file already exists.
    Args:
        content: a dictionnary containing the configuration key:values
        cfgfile: the path to a json config file
    """
    with open(cfgfile, "w") as f:
        f.write(json.dumps(content))

def currentDir():
    return os.path.dirname(os.path.abspath(__file__))

def getClientConfigFilePath():
    return os.path.normpath(os.path.join(currentDir(), "../config/client.cfg"))

# Command decorator
def command(func):
    
    func._command = True
    @wraps(func)
    def wrapper(*args, **kwargs):
        cmd_args = args if args is not None else []
        # Func.__annotations__ allows to get arguments
        # required by the function func
        # self is not counted nor shown to the user
        expected_args_count = func.__code__.co_argcount - 1
        expected_args_names = func.__code__.co_varnames[1:expected_args_count+1]
        expected_args_defaults = func.__defaults__  if func.__defaults__ is not None else []
        if not(len(cmd_args)-1 <= expected_args_count and len(cmd_args)-1 >= expected_args_count - len(expected_args_defaults)):
            msg = "This command expected "
            if len(expected_args_defaults) == 0:
                msg += f"{expected_args_count}"
            else:
                msg += f" between {expected_args_count - len(expected_args_defaults)} and {expected_args_count}"
            msg += f" arguments "
            if expected_args_count > 0:
                msg += f"{expected_args_names} "
            msg += f"but received {len(cmd_args)-1}."
            raise CmdError(msg)
        return func(*args, **kwargs)
    return wrapper

# Get all commands
def cls_commands(cls):
    cls._cmd_list = []
    for commandName in dir(cls):
        command = getattr(cls, commandName)
        if hasattr(command, '_command'):
            cls._cmd_list.append(commandName)

    return cls

def main_help():

    commands = ['exit']
    description = ['Return to the upper or quit this program']
    msg = ""
    table_data = [['Commands', 'Description']]
    
    for i in range(len(commands) - 1):
        table_data.append([commands[i], description[i]])
            
        table = AsciiTable(table_data)
        table.inner_column_border = False
        table.inner_footing_row_border = False
        table.inner_heading_row_border = True
        table.inner_row_border = False
        table.outer_border = False
        
        msg = f"""
Core commands
=============
{table.table}\n\n"""
    return msg



