from utils.utils import command, cls_commands, print_error, print_formatted, print_formatted_text
from utils.completer import IMCompleter
from core.Modules.module import Module
from core.Models.Tool import Tool
from core.Views.ToolView import ToolView
from core.Models.Worker import Worker
from core.Controllers.WorkerController import WorkerController
from core.Views.WorkerView import WorkerView
from core.apiclient import APIClient
from prompt_toolkit.formatted_text import FormattedText
from terminaltables import AsciiTable
from core.settings import Settings

@cls_commands
class Scans(Module):
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
    def scans(self):
        """Usage: workers

        Description: Equivalent to ls scans
        """
        self.ls("scans")

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
                workers = apiclient.getWorkers({"excludedDatabases":{"$nin":[apiclient.getCurrentPentest()]}})
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
        elif cmd == "edit":
            workers = apiclient.getWorkers() 
            if workers is not None:
                return [x["name"] for x in workers]
        return []