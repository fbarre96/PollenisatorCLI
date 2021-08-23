from pollenisatorcli.utils.utils import command, cls_commands, print_error, print_formatted, print_formatted_text
from pollenisatorcli.utils.completer import IMCompleter
from pollenisatorcli.core.Modules.GlobalModule import GlobalModule
from pollenisatorcli.core.Models.Tool import Tool
from pollenisatorcli.core.Views.ToolView import ToolView
from pollenisatorcli.core.Models.Worker import Worker
from pollenisatorcli.core.Controllers.WorkerController import WorkerController
from pollenisatorcli.core.Views.WorkerView import WorkerView
from pollenisatorcli.core.apiclient import APIClient
import threading
from prompt_toolkit.formatted_text import FormattedText
from terminaltables import AsciiTable
from pollenisatorcli.core.settings import Settings
from pollenisatorcli.utils.utils import getConfigFolder, loadClientConfig, getMainDir
import docker
import re
import git
import shutil
import os
name = "Scans" # Used in command decorator


@cls_commands
class Scans(GlobalModule):
    def __init__(self, parent_context, prompt_session):
        super().__init__('Scans', parent_context, "Manage Scans.", FormattedText([('class:title', "Scan manager"),('class:angled_bracket', " > ")]), IMCompleter(self), prompt_session)

    @command
    def ls(self, object_title):
        """Usage: ls workers|scans

        Description: List all objects from the given type
        """
        apiclient = APIClient.getInstance()
        if object_title == "workers":
            workers = apiclient.getWorkers()
            WorkerView.print_info(workers)
        elif object_title == "scans":
            running_scans = Tool.fetchObjects({"status":"running"})
            ToolView.print_info([x for x in running_scans])
        else:
            print_error(f"Invalid object type {object_title}.")
            self.help("ls")

    @command
    def workers(self):
        """Usage: workers

        Description: Equivalent to ls workers
        """
        self.ls("workers")

    @command
    def boot_worker(self, no_cache=False):
        """Usage: boot_worker <True|False>
        Description: will launch a worker in local docker
        """
        x = threading.Thread(target=start_docker, args=(no_cache,))
        x.start()

    @command
    def scans(self):
        """Usage: workers

        Description: Equivalent to ls scans
        """
        self.ls("scans")

    @command
    def set_inclusion(self, worker):
        """Usage: set_inclusion <worker>

        Description: set worker inclusion for current pentest
        """
        apiclient = APIClient.getInstance()
        workers = apiclient.getWorkers()
        worker_t = None
        for worker_o in workers:
            if worker_o["name"] == worker:
                worker_t = worker_o
        Worker(worker_t).set_inclusion()

    @command
    def autoscan(self, action):
        """Usage: autoscan <status|start|stop>

        Description: Handle start tools automatically by priority order / threads limits / time limit and only if they are marked as safe.

        Args:
            action: Either start, stop or status
        """
        apiclient = APIClient.getInstance()
        autoscan_status = apiclient.getAutoScanStatus()
        settings = Settings()
        settings.reloadSettings()
        if action == "status":
            if autoscan_status:
                print_formatted("Autoscan is running")
            else:
                print_formatted("Autoscan is not running")
        elif action == "start":
            if autoscan_status:
                print_error("An autoscan is already running")
            else:
                workers = apiclient.getWorkers({"pentests":apiclient.getCurrentPentest()})
                workers = [w for w in workers]
                if len(workers) == 0:
                    print_error("No worker found, check workers list to see if there are workers registered and allowed for this pentest")
                    return
                if settings.db_settings.get("include_all_domains", False):
                    from prompt_toolkit.shortcuts import confirm
                    answer = confirm("The current settings will add every domain found in attack's scope. Are you sure ?")
                    if not answer:
                        return
                apiclient.sendStartAutoScan()
        elif action == "stop":
            if not autoscan_status:
                print_error("Autoscan is not running")
            else:
                apiclient.sendStopAutoScan()

    @command
    def edit(self, workername):
        """Usage: edit <workername>

        Description: Edit configuration of a worker

        Args:
            workername: the worker name to edit
        """
        apiclient = APIClient.getInstance()
        workers = apiclient.getWorkers()
        if not workers:
            print_error("No worker found")
        worker_t = None
        for worker in workers:
            if worker["name"] == workername:
                worker_t = worker
        if worker_t is None:
            print_error(f"{workername} is not registered in the worker list")
            return
        self.set_context(WorkerView(WorkerController(Worker(worker_t)), self, self.prompt_session))

    
    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """  
        apiclient = APIClient.getInstance()

        if cmd == "help":
            return [""]+self._cmd_list
        elif cmd == "ls":
            return ["scans", "workers"]
        elif cmd == "autoscan":
            return ["start", "stop", "status"]
        elif cmd == "edit" or "set_inclusion":
            workers = apiclient.getWorkers() 
            if workers is not None:
                return [x["name"] for x in workers]
        return []


def start_docker(force_reinstall):
    worker_subdir = os.path.join(getMainDir(), "PollenisatorWorker")
    if os.path.isdir(worker_subdir) and force_reinstall:
        shutil.rmtree(worker_subdir)
    if not os.path.isdir(worker_subdir):
        git.Git(getMainDir()).clone("https://github.com/fbarre96/PollenisatorWorker.git")

    shutil.copyfile(os.path.join(getConfigFolder(), "client.cfg"), os.path.join(getMainDir(), "PollenisatorWorker/config/client.cfg"))
    print_formatted("Docker not found: Building worker docker could take a while (1~10 minutes depending on internet connection speed)...")
    try:
        client = docker.from_env()
        clientAPI = docker.APIClient()
    except Exception as e:
        print_error(f"Unable to launch a docker : {e}")
        return
    image = client.images.list("pollenisatorworker")
    if len(image) == 0 or force_reinstall:
        try:
            log_generator = clientAPI.build(path=os.path.join(getMainDir(), "PollenisatorWorker/"), rm=True, tag="pollenisatorworker", nocache=force_reinstall)
            for byte_log in log_generator:
                log_line = byte_log.decode("utf-8").strip()
                if log_line.startswith("{\"stream\":\""):
                    log_line = log_line[len("{\"stream\":\""):-4]
                    print_formatted(log_line+"\n")
        except docker.errors.BuildError as e:
            print_error("Building error:\n"+str(e))
            return
        image = client.images.list("pollenisatorworker")
    if len(image) == 0:
        print_error("The docker build command failed, try to install manually...")
        return
    print_formatted("Starting worker docker ...")
    clientCfg = loadClientConfig()
    if clientCfg["host"] == "localhost" or clientCfg["host"] == "127.0.0.1":
        network_mode = "host"
    else:
        network_mode = None
    container = client.containers.run(image=image[0], network_mode=network_mode, volumes={os.path.join(getMainDir(), "PollenisatorWorker"):{'bind':'/home/Pollenisator', 'mode':'rw'}}, detach=True)
    print_formatted("Checking if worker is running")
    print_formatted(container.id)
    if container.logs() != b"":
        print_error(container.logs())
