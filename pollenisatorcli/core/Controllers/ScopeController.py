from pollenisatorcli.core.Controllers.ElementController import ElementController

class ScopeController(ElementController):
    def doInsert(self, values):
        toInsert = dict()
        for param_name in values:
            db_name = self.paramNameToDbName(param_name)
            if db_name is not None:
                # Update in database
                toInsert[db_name] = values[param_name]
        scopes = toInsert["scope"]
        err_count = 0
        ret = []
        for scope in scopes:
            toInsert["scope"] = scope
            self.model.__init__(toInsert)
            # Insert in database
            to_ret, _ = self.model.addInDb()
            if not ret:
                err_count += 1
            else:
                ret.append(to_ret)
        # Fetch the instance of this self.model now that it is inserted.
        return ret, err_count  # 0 errors