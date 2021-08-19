from pollenisatorcli.core.apiclient import APIClient
from terminaltables import AsciiTable
from pollenisatorcli.utils.utils import print_formatted

class Dashboard:
    @classmethod
    def printServicesPerHosts(cls):
        apiclient = APIClient.getInstance()
        results = apiclient.aggregate("ports", [{"$group":{"_id":{"ip": "$ip"}, "count":{"$sum":1}}}, {"$sort": {"count":-1}}])
        if results is not None:
            table_data = [['Hostname', 'Ports']]
            table = AsciiTable(table_data)
            for result in results:
                table_data.append([result["_id"]["ip"], result["count"] ])
                table.inner_column_border = False
                table.inner_footing_row_border = False
                table.inner_heading_row_border = True
                table.inner_row_border = False
                table.outer_border = False
            print_formatted(table.table)
        else:
            #No case
            print_formatted("No information to display")
            pass

    @classmethod
    def printTopPorts(cls):
        apiclient = APIClient.getInstance()
        results = apiclient.aggregate("ports", [{"$group":{"_id":{"port": "$port"}, "count":{"$sum":1}}}, {"$sort": {"count":-1}}])
        if results is not None:
            table_data = [['Port', 'Count']]
            for result in results:
                table_data.append([result["_id"]["port"], result["count"] ])
                table = AsciiTable(table_data)
                table.inner_column_border = False
                table.inner_footing_row_border = False
                table.inner_heading_row_border = True
                table.inner_row_border = False
                table.outer_border = False
            print_formatted(table.table)
        else:
            #No case
            print_formatted("No information to display")
            pass

    @classmethod
    def printToolsState(cls):
        apiclient = APIClient.getInstance()
        results = {}
        totalresults = apiclient.aggregate("tools", [{"$group":{"_id":{"name": "$name"}, "count":{"$sum":1}}}, {"$sort": {"count":-1}}])
        for result in totalresults:
            results[result["_id"]["name"]] = {"total":result["count"]}
        doneresults = apiclient.aggregate("tools", [{"$match":{"status":"done"}},{"$group":{"_id":{"name": "$name"}, "count":{"$sum":1}}}, {"$sort": {"count":-1}}])
        for result in doneresults:
            results[result["_id"]["name"]]["done"] = result["count"]
        runningresults = apiclient.aggregate("tools", [{"$match":{"status":"running"}},{"$group":{"_id":{"name": "$name"}, "count":{"$sum":1}}}, {"$sort": {"count":-1}}])
        for result in runningresults:
            results[result["_id"]["name"]]["running"] = result["count"]
        errorresults = apiclient.aggregate("tools", [{"$match":{"status":"error"}},{"$group":{"_id":{"name": "$name"}, "count":{"$sum":1}}}, {"$sort": {"count":-1}}])
        for result in errorresults:
            results[result["_id"]["name"]]["error"] = result["count"]
        if results:
            table_data = [['Tool', 'Ready', 'Running', 'Done', "Error", "Total"]]
            for tool_name, tool_counts in results.items():
                total = tool_counts["total"]
                ready_count = total - tool_counts.get("done",0) - tool_counts.get("running", 0) - tool_counts.get("error", 0)
                table_data.append([tool_name, ready_count, result.get("running", 0), result.get("done", 0), result.get("error", 0), total])
                table = AsciiTable(table_data)
                table.inner_column_border = False
                table.inner_footing_row_border = False
                table.inner_heading_row_border = True
                table.inner_row_border = False
                table.outer_border = False
            print_formatted(table.table)
        else:
            #No case
            print_formatted("No information to display")
            pass