from functools import wraps
from terminaltables import AsciiTable
import re
import time
import requests
import json
import subprocess
import os
import socket
from threading import Timer
from datetime import datetime
from bson import ObjectId
from netaddr import IPNetwork, IPAddress
from netaddr.core import AddrFormatError
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from inspect import getfullargspec

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return "ObjectId|"+str(o)
        elif isinstance(o, datetime):
            return str(o)
        elif isinstance(o, set):
            return list(o)
        return json.JSONEncoder.default(self, o)

class JSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
        
    def object_hook(self, dct): # pylint: disable=method-hidden
        for k,v in dct.items():
            if 'ObjectId|' in str(v):
                dct[k] = ObjectId(v.split('ObjectId|')[1])
        return dct

def CmdError(msg):
    print_error(msg)

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
    config_folder = getConfigFolder()
    try:
        os.makedirs(config_folder)
    except:
        pass
    with open(cfgfile, "w") as f:
        f.write(json.dumps(content))

def currentDir():
    return os.path.dirname(os.path.abspath(__file__))

def getMainDir():
    """Returns:
        the pollenisator main folder
    """
    p = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../")
    return p

def getConfigFolder():
    from os.path import expanduser
    home = expanduser("~")
    config = os.path.join(home,".config/pollenisatorcli/")
    return config


def getClientConfigFilePath():
    config = os.path.normpath(os.path.join(getConfigFolder(), "client.cfg"))
    return config

def loadClientConfig():
    p = getClientConfigFilePath()
    try:
        cfg = loadCfg(p)
    except FileNotFoundError:
        print_error(f"Client config {p} not found : A default one will be created.")
        cfg = {"host":"127.0.0.1", "port":5000, "https":False}
    return cfg

# Command decorator
def command(func):
    
    func._command = True
    @wraps(func)
    def wrapper(*args, **kwargs):
        cmd_args = args if args is not None else []
        # Func.__annotations__ allows to get arguments
        # required by the function func
        # self is not counted nor shown to the user
        func_args = getfullargspec(func)
        if func_args[1] is not None:  # varargs set
            return func(*args, **kwargs)
        expected_args_count = len(func_args[0]) - 1
        expected_args_names = func_args[1:]
        
        expected_args_defaults = func.__defaults__  if func.__defaults__ is not None else []
        if not(len(cmd_args)-1 <= expected_args_count and len(cmd_args)-1 >= expected_args_count - len(expected_args_defaults)):
            msg = "This command expected "
            if len(expected_args_defaults) == 0:
                msg += f"{expected_args_count}"
            else:
                msg += f" between {expected_args_count - len(expected_args_defaults)} and {expected_args_count}"
            msg += f" arguments "
            msg += f"but received {len(cmd_args)-1}."
            msg += "\n"+ func.__doc__
            return  CmdError(msg)
        return func(*args, **kwargs)
    return wrapper

# Get all commands
def cls_commands(cls):
    cls._cmd_list = []
    for commandName in dir(cls):
        command = getattr(cls, commandName)
        if hasattr(command, '_command'):
            cls._cmd_list.insert(0, commandName)

    return cls

def stringToDate(datestring):
    """Converts a string with format '%d/%m/%Y %H:%M:%S' to a python date object.
    Args:
        datestring: a string with format '%d/%m/%Y %H:%M:%S'
    Returns:
        the date python object if the given string is successfully converted, None otherwise"""
    ret = None
    if isinstance(datestring, str):
        if datestring != "None":
            ret = datetime.strptime(
                datestring, '%d/%m/%Y %H:%M:%S')
    return ret

def dateToString(date):
    """Converts a date object to a string with format '%d/%m/%Y %H:%M:%S'.
    Args:
        date: a python datetime object
    Returns:
         the date python object as a string if successfully converted, None otherwise"""
    return date.strftime('%d/%m/%Y %H:%M:%S')

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

# The style sheet.
style = Style.from_dict({
    'error': '#ff0066 bold',
    'valid': '#11ff00',
    'success': '#11ff00',
    'command': '#4444ff bold',
    'cmd': 'italic',
    'parameter': '#44ff00 italic',
    'important': 'bold',
    'title': 'bold #ebe534',
    'subtitle': 'bold #34eb5f',
    'angled_bracket': 'bold',
    'warning': '#eded42',
    'normal': ''
})
def print_formatted(msg, cls="normal"):
    text = FormattedText([
        (f'class:{cls}', msg)
    ])
    print_formatted_text(text, style=style)

def print_error(msg):
    text = FormattedText([
        ('class:error', 'ERROR : '),
        ('class:normal', msg),
    ])
    print_formatted_text(text, style=style)

def loadToolsConfig():
    """
    Load tools config file in the config/tools.d/ folder starting with
    config/tools.d/tools.json as default values
    Args:
        cfgfile: the path to a json config file
    Returns:
        Return the json converted values of the config file.
    """
    tool_config_folder = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "../../config/tools.d/")
    default_tools_config = os.path.join(tool_config_folder, "tools.json")
    default_tools_infos = None
    try:
        with open(default_tools_config) as f:
            default_tools_infos = json.loads(f.read())
    except Exception as e:
        raise Exception("Error when loading tools to register : "+str(e))
    for _r, _d, f in os.walk(tool_config_folder):
        for fil in f:
            if fil != "tools.json":
                try:
                    with open(default_tools_config) as f:
                        tools_infos = json.loads(f.read())
                        for key, value in tools_infos.items():
                            default_tools_infos[key] = value
                except json.JSONDecodeError:
                    print("Invalid json file : "+str(fil))
    return default_tools_infos

def saveToolsConfig(dic):
    """
    Save tools config file in the config/tools.d/ in tools.json 
    Args:
        dic: a dictionnary to write values
    """
    tool_config_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../config/tools.d/")
    default_tools_config = os.path.join(tool_config_folder, "tools.json")
    with open(default_tools_config, "w") as f:
        f.write(json.dumps(dic))

    
def isIp(ip):
    """
    Check if the given scope string is a network ip or a domain.
    Args:
        ip: the domain string or the network ipv4 range string
    Returns:
        Returns True if it is a network ipv4 range, False if it is a domain (any other possible case).
    """
    try:
        IPAddress(ip)
    except AddrFormatError:
        return False
    except ValueError:
        return False
    return True

def isDomain(domain_val):
    """Check if the gien value could be a valid domain. 
    Args:
        domain_val: the string we want to know if it matches a domain
    Returns:
        bool
    """
    return re.match(r"^((?!-))(xn--)?[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}\.(xn--)?([a-z0-9\-]{1,61}|[a-z0-9-]{1,30}\.[a-z]{2,})$", domain_val)


def isNetworkIp(domain_or_networks):
    """
    Check if the given scope string is a network ip or a domain.
    Args:
        domain_or_networks: the domain string or the network ipv4 range string
    Returns:
        Returns True if it is a network ipv4 range, False if it is a domain (any other possible case).
    """
    try:
        IPNetwork(domain_or_networks)
    except AddrFormatError:
        return False
    return True

def performLookUp(domain):
    """
    Uses the socket module to get an ip from a domain.

    Args:
        domain: the domain to look for in dns

    Returns:
        Return the ip found from dns records, None if failed.
    """
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None

def fitNowTime(dated, datef):
    """Check the current time on the machine is between the given start and end date.
    Args:
        dated: the starting date for the interval
        datef: the ending date for the interval
    Returns:
        True if the current time is between the given interval. False otherwise.
        If one of the args is None, returns False."""
    today = datetime.now()
    date_start = stringToDate(dated)
    date_end = stringToDate(datef)
    if date_start is None or date_end is None:
        return False
    return today > date_start and date_end > today


def execute(command, timeout=None, printStdout=True):
    """
    Execute a bash command and print output

    Args:
        command: A bash command
        timeout: a date in the futur when the command will be stopped if still running or None to not use this option, default as None.
        printStdout: A boolean indicating if the stdout should be printed. Default to True.

    Returns:
        Return the return code of this command

    Raises:
        Raise a KeyboardInterrupt if the command was interrupted by a KeyboardInterrupt (Ctrl+c)
    """

    try:
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        time.sleep(1) #HACK Break if not there when launching fast custom tools on local host
        try:
            if timeout is not None:
                if isinstance(timeout, float):
                    timeout = (timeout-datetime.now()).total_seconds()
                    timer = Timer(timeout, proc.kill)
                    timer.start()
                else:
                    if timeout.year < datetime.now().year+1:
                        timeout = (timeout-datetime.now()).total_seconds()
                        timer = Timer(timeout, proc.kill)
                        timer.start()
            stdout, stderr = proc.communicate(None, timeout)
            if printStdout:
                stdout = stdout.decode('utf-8')
                stderr = stderr.decode('utf-8')
                if str(stdout) != "":
                    print(str(stdout))
                if str(stderr) != "":
                    print(str(stderr))
        except Exception as e:
            print(str(e))
            proc.kill()
            return -1, ""
        finally:
            if timeout is not None:
                if isinstance(timeout, float):
                    timer.cancel()
                else:
                    if timeout.year < datetime.now().year+1:
                        timer.cancel()
        return proc.returncode, stdout
    except KeyboardInterrupt as e:
        raise e
