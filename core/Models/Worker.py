"""Interval Model. Useful to limit in a time frame some tools"""

from core.Models.Element import Element
from core.apiclient import APIClient
from bson.objectid import ObjectId
from datetime import datetime


class Worker(Element):
    """
    Represents an interval object that defines an time interval where a wave can be executed.

    Attributes:
        coll_name: collection name in pollenisator database
    """
    coll_name = "workers"

    def __init__(self, valuesFromDb=None):
        """Constructor
        Args:
            valueFromDb: a dict holding values to load into the object. A mongo fetched interval is optimal.
                        possible keys with default values are : _id (None), parent (None), tags([]), infos({}),
                        wave(""), dated("None"), datef("None")
        """
        if valuesFromDb is None:
            valuesFromDb = {}
        super().__init__(valuesFromDb.get("_id", None), valuesFromDb.get("parent", None),  valuesFromDb.get(
            "tags", []), valuesFromDb.get("infos", {}))
        self.initialize(valuesFromDb.get("name", ""), valuesFromDb.get("excludedDatabases", []),
                        valuesFromDb.get("registeredCommands", []), valuesFromDb.get("infos", {}))

    def initialize(self, name, excludedDatabases=[], registeredCommands=[], infos=None):
        """Set values of worker
        Args:
            name: the worker name
            excludedDatabases: a list of databases the worker will not work for
            registeredCommands: the list of registred command (known by this worker)
            infos: a dictionnary with key values as additional information. Default to None
        Returns:
            this object
        """
        self.name = name
        self.excludedDatabases = excludedDatabases
        self.registeredCommands = registeredCommands
        self.infos = infos if infos is not None else {}
        return self

    def delete(self):
        """
        Delete the Interval represented by this model in database.
        """
        apiclient = APIClient.getInstance()
        apiclient.deleteWorker(self.name) 


    def __str__(self):
        """
        Get a string representation of a worker.

        Returns:
            Returns the worker name.
        """
        return f"{self.name}"

    def getDetailedString(self):
        return self.name

    

    def getDbKey(self):
        """Return a dict from model to use as unique composed key.
        Returns:
            A dict (1 key :"name")
        """
        return {"name": self.name}
