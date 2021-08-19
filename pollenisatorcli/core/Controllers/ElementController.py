class ElementController:
    def __init__(self, model):
        self.model = model
    
    def getDetailedString(self):
        return self.model.getDetailedString()

    def doDelete(self):
        """Ask the model to delete itself from database
        """
        return self.model.delete()

    def doUpdate(self, param_values):
        for param_name in param_values:
            db_name = self.paramNameToDbName(param_name)
            if db_name is not None:
                # Update in database
                self.model.update({db_name:param_values[param_name]})

    def doInsert(self, values):
        toInsert = dict()
        for param_name in values:
            db_name = self.paramNameToDbName(param_name)
            if db_name is not None:
                # Update in database
                toInsert[db_name] = values[param_name]
        
        self.model.__init__(toInsert)
        # Insert in database
        ret, _ = self.model.addInDb()
        if not ret:
            # command failed to be inserted, a duplicate exists
            # return None as inserted_id and 1 error
            return None, 1
        # Fetch the instance of this self.model now that it is inserted.
        return ret, 0  # 0 errors
    
    def paramNameToDbName(self, param_name):
        return param_name

    def getDbKey(self):
        return self.model.getDbKey()