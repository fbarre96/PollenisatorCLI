"""worker module. Execute code and store results in database, files in the SFTP server.
"""

import errno
import os
import ssl
import sys
import uuid
import time
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from multiprocessing import Process
from pollenisatorcli.core.apiclient import APIClient
from pollenisatorcli.core.Models.Interval import Interval
from pollenisatorcli.core.Models.Tool import Tool
from pollenisatorcli.core.Models.Command import Command
from pollenisatorcli.utils.utils import execute, fitNowTime, loadToolsConfig
from pollenisatorcli.utils.utils import print_error, print_formatted_text, print_formatted

def executeCommand(apiclient, toolId, parser="", local=True, allowAnyCommand=False):
    """
     remote task
    Execute the tool with the given toolId on the given calendar name.
    Then execute the plugin corresponding.
    Any unhandled exception will result in a task-failed event in the class.

    Args:
        apiclient: the apiclient instance.
        toolId: the mongo Object id corresponding to the tool to execute.
        parser: plugin name to execute. If empty, the plugin specified in tools.d will be fetched.
        local: boolean, set the execution in a local context
    Raises:
        Terminated: if the task gets terminated
        OSError: if the output directory cannot be created (not if it already exists)
        Exception: if an exception unhandled occurs during the bash command execution.
        Exception: if a plugin considered a failure.
    """
    # Connect to given calendar
    APIClient.setInstance(apiclient)
    toolModel = Tool.fetchObject({"_id":ObjectId(toolId)})
    if toolModel is None:
        return False, "Tool failed to be created"
    command_o = toolModel.getCommand()
    msg = ""
    ##
    success, comm, fileext, bin_path_server = apiclient.getCommandline(toolId, parser)
    if local:
        tools_infos = loadToolsConfig()
        # Read file to execute for given tool and prepend to final command
        if tools_infos.get(toolModel.name, None) is not None:
            bin_path_local = tools_infos[toolModel.name].get("bin")
            parser = tools_infos[toolModel.name].get("plugin", "Default.py")
            success, comm, fileext, bin_path_server = apiclient.getCommandline(toolId, parser)
            if bin_path_server == "":
                comm = bin_path_local +" "+comm
            else:
                comm = comm.replace(bin_path_server, bin_path_local)
            success = True
        elif allowAnyCommand:
            success, comm, fileext, bin_path_server = apiclient.getCommandline(toolId, parser)
            success = True
        else:
            success = False
            comm = "This tool is not configured for local usage; Please check Settings"
    else:
        success, comm, fileext, bin_path_server = apiclient.getCommandline(toolId, parser)
    if not success:
        toolModel.setStatus(["error"])
        return False, str(comm)
        
    outputRelDir = toolModel.getOutputDir(apiclient.getCurrentPentest())
    abs_path = os.path.dirname(os.path.abspath(__file__))
    toolFileName = toolModel.name+"_" + \
            str(time.time()) # ext already added in command
    outputDir = os.path.join(abs_path, "./results", outputRelDir)
    
    # Create the output directory
    try:
        os.makedirs(outputDir)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(outputDir):
            pass
        else:
            print_error(str(exc))
            toolModel.setStatus(["error"])
            return False, str(exc)
    outputDir = os.path.join(outputDir, toolFileName)
    comm = comm.replace("|outputDir|", outputDir)
    # Get tool's wave time limit searching the wave intervals
    if toolModel.wave == "Custom commands" or local:
        timeLimit = None
    else:
        timeLimit = getWaveTimeLimit(toolModel.wave)
    # adjust timeLimit if the command has a lower timeout
    if command_o is not None and timeLimit is not None:
        timeLimit = min(datetime.now()+timedelta(0, int(command_o.get("timeout", 0))), timeLimit)
    ##
    try:
        print_formatted_text(('TASK STARTED:'+toolModel.name))
        if timeLimit is not None:
            print_formatted_text("Will timeout at "+str(timeLimit))
        # Execute the command with a timeout
        returncode, stdout = execute(comm, timeLimit, False)
        if returncode == -1:
            raise Exception("Tool Timeout")
    except Exception as e:
        print_error(str(e))
        toolModel.setStatus(["error"])
        return False, str(e)
    # Execute found plugin if there is one
    outputfile = outputDir+fileext
    print_formatted(f"Uploading {outputfile} tool result ...")
    msg = apiclient.importToolResult(toolId, parser, outputfile)
    if msg != "Success":
        #toolModel.markAsNotDone()
        print_error(str(msg))
        toolModel.setStatus(["error"])
        return False, str(msg)
          
    # Delay
    if command_o is not None:
        if float(command_o.get("sleep_between", 0)) > 0.0:
            msg += " (will sleep for " + \
                str(float(command_o.get("sleep_between", 0)))+")"
        print_formatted_text(msg)
        time.sleep(float(command_o.get("sleep_between", 0)))
    return True, os.path.normpath(outputfile)
    
def getWaveTimeLimit(waveName):
    """
    Return the latest time limit in which this tool fits. The tool should timeout after that limit

    Returns:
        Return the latest time limit in which this tool fits.
    """
    intervals = Interval.fetchObjects({"wave": waveName})
    furthestTimeLimit = datetime.now()
    for intervalModel in intervals:
        if fitNowTime(intervalModel.dated, intervalModel.datef):
            endingDate = intervalModel.getEndingDate()
            if endingDate is not None:
                if endingDate > furthestTimeLimit:
                    furthestTimeLimit = endingDate
    return furthestTimeLimit


