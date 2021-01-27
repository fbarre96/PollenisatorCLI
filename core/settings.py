"""Hold functions to interact with the settings"""
import os
import json
from core.apiclient import APIClient
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
    def getTags(cls):
        """
        Returns tags defined in settings.
        Returns:
            If none are defined returns {"todo":"yellow", "unscanned":"magenta", "P0wned!":"red", "Interesting":"dark green", "Uninteresting":"sky blue", "Neutral":"white"}
            otherwise returns a dict with defined key values
        """
        apiclient = APIClient.getInstance()
        if cls.tags_cache is not None:
            return cls.tags_cache
        tags = apiclient.findInDb(
            "pollenisator", "settings", {"key": "tags"}, False)
        if tags is not None:
            tags = json.loads(tags["value"])
            if isinstance(tags, dict):
                cls.tags_cache = tags
        if cls.tags_cache is None:
            cls.tags_cache = {"todo":"yellow", "unscanned":"magenta", "P0wned!":"red", "Interesting":"dark green", "Uninteresting":"sky blue", "Neutral":"white"}
        return cls.tags_cache

    @classmethod
    def getPentestTypes(cls):
        """
        Returns pentest types and associeted defect type defined in settings.
        Returns:
            If none are defined returns {"Web":["Socle", "Application", "Données", "Politique"], "LAN":["Infrastructure", "Active Directory", "Données", "Politique"]}
            otherwise returns a dict with defined key values
        """
        apiclient = APIClient.getInstance()
        if cls.__pentest_types is None:
            pentest_types = apiclient.findInDb(
                "pollenisator", "settings", {"key": "pentest_types"}, False)
            if pentest_types is not None:
                if isinstance(pentest_types["value"], str):
                    cls.__pentest_types = json.loads(pentest_types["value"])
                elif isinstance(pentest_types["value"], dict):
                    cls.__pentest_types = pentest_types["value"]
                else:
                    cls.__pentest_types = {"Web":["Socle", "Application", "Données", "Politique"], "LAN":["Infrastructure", "Active Directory", "Données", "Politique"]}
            else:
                cls.__pentest_types = {"Web":["Socle", "Application", "Données", "Politique"], "LAN":["Infrastructure", "Active Directory", "Données", "Politique"]}
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