"""Hold functions to interact with the settings"""
import os
import json
from pollenisatorcli.core.apiclient import APIClient
from shutil import which


class Settings:
    """
    Represents the settings of pollenisator.
    There are three level of settings:
        * local settings: stored in a file under ../../config/settings.cfg
        * pentest db settings: stored in the pentest database under settings collection
        * global settings: stored in the pollenisator database under settings collection
    """
    tags_cache = None
    __pentest_types = None
    def __init__(self):
        """
        Load the tree types of settings and stores them in dictionnaries
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.confdir = os.path.join(dir_path, "../config/settings.cfg")

        self.local_settings = {}
        try:
            with open(self.confdir, "r") as f:
                self.local_settings = json.loads(f.read())
        except json.JSONDecodeError:
            self.local_settings = {}
        except IOError:
            self.local_settings = {}
        self.db_settings = {}
        self.global_settings = {}

    @classmethod
    def getPentestTags(cls):
        apiclient = APIClient.getInstance()
        db_tags = apiclient.find("settings", {"key":"tags"}, False)
        if db_tags is None:
            db_tags = {}
        else:
            db_tags = db_tags["value"]
        return db_tags

   

    @classmethod
    def getTags(cls, onlyGlobal=False, **kwargs):
        """
        Returns tags defined in settings.
        Returns:
            If none are defined returns {"todo":"yellow", "P0wned!":"red", "Interesting":"green", "Uninteresting":"blue", "Neutral":"white"}
            otherwise returns a dict with defined key values
        """
        apiclient = APIClient.getInstance()
        if kwargs.get("ignoreCache", False): #Check if ignore cache is true
            cls.tags_cache = None
        if cls.tags_cache is not None and not onlyGlobal:
            return cls.tags_cache
        cls.tags_cache = {"todo":"orange", "P0wned!":"red", "Interesting":"dark green", "Uninteresting":"sky blue", "Neutral":"white"}
        global_tags = apiclient.getSettings({"key": "tags"})
        if global_tags is not None:
            if isinstance(global_tags["value"], dict):
               global_tags = global_tags["value"]
            elif isinstance(global_tags["value"], str):
                global_tags = json.loads(global_tags["value"])
        if global_tags is None:
            global_tags = {}
        if not onlyGlobal:
            db_tags = cls.getPentestTags()
            cls.tags_cache = {**global_tags, **db_tags}
            return cls.tags_cache
        return global_tags

    @classmethod
    def getPentestTypes(cls):
        """
        Returns pentest types and associeted defect type defined in settings.
        Returns:
            If none are defined returns {"Web":["Base", "Application", "Data", "Politicy"], "LAN":["Infrastructure", "Active Directory", "Data", "Policy"]}
            otherwise returns a dict with defined key values
        """
        apiclient = APIClient.getInstance()
        if cls.__pentest_types is None:
            pentest_types = apiclient.getSettings({"key": "pentest_types"})
            if pentest_types is not None:
                if isinstance(pentest_types["value"], str):
                    cls.__pentest_types = json.loads(pentest_types["value"])
                elif isinstance(pentest_types["value"], dict):
                    cls.__pentest_types = pentest_types["value"]
                else:
                    cls.__pentest_types = {"Web":["Base", "Application", "Data", "Politicy"], "LAN":["Infrastructure", "Active Directory", "Data", "Politicy"]}
            else:
                cls.__pentest_types = {"Web":["Base", "Application", "Data", "Politique"], "LAN":["Infrastructure", "Active Directory", "Data", "Politicy"]}
        return cls.__pentest_types


    def getTerms(self):
        """
        Returns terminals configured 
        Returns:
            If none are defined returns ['''gnome-terminal --window --title="Pollenisator terminal" -- bash --rcfile setupTerminalForPentest.sh''',
             '''xfce4-terminal -x bash --rcfile setupTerminalForPentest.sh''',
             '''xterm -e bash --rcfile setupTerminalForPentest.sh''']
            otherwise returns a list with defined  values
        """
        self._reloadLocalSettings()
        return self.local_settings.get("terms",
            ["""gnome-terminal --window --title="Pollenisator terminal" -- bash --rcfile setupTerminalForPentest.sh""",
             """xfce4-terminal -x bash --rcfile setupTerminalForPentest.sh""",
             "xterm -e bash --rcfile setupTerminalForPentest.sh"])
    
    def getFavoriteTerm(self):
        """
        Returns favorite terminal configured 
        Returns:
            If none are defined returns first in the list of terms
            Otherwise returns the favorite terminal configured 
        """
        self._reloadLocalSettings()
        fav = self.local_settings.get("fav_term", None)
        if fav is None:
            terms = self.getTerms()
            for term in terms:
                term_name = term.split(" ")[0].strip()
                if which(term_name):
                    fav = term_name
        return fav

    def _reloadLocalSettings(self):
        """
        Reload local settings from local conf file
        """
        try:
            with open(self.confdir, "r") as f:
                self.local_settings = json.loads(f.read())
        except json.JSONDecodeError:
            self.local_settings = {}
        except IOError:
            self.local_settings = {}

    def _reloadDbSettings(self):
        """
        Reload pentest database settings from pentest database
        """
        apiclient = APIClient.getInstance()
        self.__class__.tags_cache = None
        dbSettings = apiclient.find("settings", {})
        if dbSettings is None:
            dbSettings = {}
        for settings_dict in dbSettings:
            try:
                self.db_settings[settings_dict["key"]] = settings_dict["value"]
            except KeyError:
                pass

    def _reloadGlobalSettings(self):
        """
        Reload pentest database settings from pollenisator database
        """
        apiclient = APIClient.getInstance()
        globalSettings = apiclient.getSettings()
        self.__class__.tags_cache = None
        for settings_dict in globalSettings:
            self.global_settings[settings_dict["key"]] = settings_dict["value"]

    def reloadSettings(self):
        """
        Reload local, database and global settings.
        """
        self._reloadLocalSettings()
        self._reloadDbSettings()
        self._reloadGlobalSettings()

    
    def saveLocalSettings(self):
        """
        Save local settings to conf file
        """
        with open(self.confdir, "w") as f:
            f.write(json.dumps(self.local_settings))

    def savePentestSettings(self):
        apiclient = APIClient.getInstance()
        settings = apiclient.find("settings")
        for k, v in self.db_settings.items():
            if k in settings:
                apiclient.update("settings", {
                    "key": k}, {"$set": {"value": v}})

    def save(self):
        """
        Save all the settings (local, database and global)
        """
        apiclient = APIClient.getInstance()

        for k, v in self.global_settings.items():
            if apiclient.getSettings({"key": k}) is None:
                apiclient.createSetting(k, v)
            else:
                apiclient.updateSetting(k, v)
        self.savePentestSettings()
        self.saveLocalSettings()

    def getPentestType(self):
        """Return selected database pentest type.
        Returns:
            Open database pentest type. string "None" if not defined"""
        return self.db_settings.get("pentest_type", "None")

    def getPentesters(self):
        """Return a list of pentesters registered for open pentest database
        Returns:
            List of pentesters names"""
        return self.db_settings.get("pentesters", [])