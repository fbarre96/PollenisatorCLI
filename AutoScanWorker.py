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
from core.apiclient import APIClient
from core.Models.Interval import Interval
from core.Models.Tool import Tool
from core.Models.Command import Command
from utils.utils import execute, fitNowTime
from utils.utils import print_error, print_formatted_text, print_formatted

def executeCommand(calendarName, toolId, parser=""):
    """
     remote task
    Execute the tool with the given toolId on the given calendar name.
    Then execute the plugin corresponding.
    Any unhandled exception will result in a task-failed event in the class.

    Args:
        calendarName: The calendar to search the given tool id for.
        toolId: the mongo Object id corresponding to the tool to execute.
        parser: plugin name to execute. If empty, the plugin specified in tools.d will be feteched.
    Raises:
        Terminated: if the task gets terminated
        OSError: if the output directory cannot be created (not if it already exists)
        Exception: if an exception unhandled occurs during the bash command execution.
        Exception: if a plugin considered a failure.
    """
    # Connect to given calendar
    apiclient = APIClient.getInstance()
    apiclient.setCurrentPentest(calendarName)
    toolModel = Tool.fetchObject({"_id":ObjectId(toolId)})
    if toolModel is None:
        return False, "Tool failed to be created"
    command_o = toolModel.getCommand()
        
    msg = ""
    ##
    success, comm, fileext = apiclient.getCommandline(toolId, parser)
    if not success:
        print_error(str(comm))
        toolModel.setStatus(["error"])
        return False, str(comm)
    outputRelDir = toolModel.getOutputDir(calendarName)
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
    if toolModel.wave == "Custom commands":
        timeLimit = None
    else:
        timeLimit = getWaveTimeLimit(toolModel.wave)
    # adjust timeLimit if the command has a lower timeout
    if command_o is not None:
        timeLimit = min(datetime.now()+timedelta(0, int(command_o.get("timeout", 0))), timeLimit)
    ##
    try:
        print_formatted_text(('TASK STARTED:'+toolModel.name))
        print_formatted_text("Will timeout at "+str(timeLimit))
        # Execute the command with a timeout
        returncode = execute(comm, timeLimit, True)
        if returncode == -1:
            raise Exception("Tool Timeout")
    except Exception as e:
        print_error(str(e))
        toolModel.setStatus(["error"])
        return False, str(e)
    # Execute found plugin if there is one
    outputfile = outputDir+fileext
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
    return True, ""
    
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


