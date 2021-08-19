from pollenisatorcli.utils.utils import command, cls_commands, print_error
from pollenisatorcli.utils.completer import IMCompleter
from pollenisatorcli.core.FormModules.formModule import FormModule
from pollenisatorcli.core.Parameters.parameter import Parameter, TableParameter, ComboParameter, BoolParameter, ListParameter
from pollenisatorcli.core.settings import Settings
from pollenisatorcli.core.apiclient import APIClient
from prompt_toolkit.formatted_text import FormattedText


@cls_commands
class PollenisatorSettings(FormModule):
    def __init__(self, parent_context, prompt_session):
        super().__init__('Pollenisator settings', parent_context, "Pollenisator global settings.", FormattedText(
            [('class:title', f"{parent_context.name}"), ("class:subtitle", f" global settings"), ("class:angled_bracket", " > ")]), IMCompleter(self), prompt_session)

    def reload(self):
        settings = Settings()
        settings._reloadGlobalSettings()
        self.fields = [
            TableParameter("pentest_types", ["Pentest types", "Defects categories"], default=settings.getPentestTypes(),
                      helper="Pentest types (Web, LAN ...) and their associated flaws categories (application, data...)"),

            TableParameter("tags", ["Tag names", "Color"], default=Settings.getTags(), helper="Tag list and associated colors"),
        ]

    @command
    def show(self):
        """Usage: show
        """
        self.reload()
        super().show()

    @command
    def save(self):
        """Usage:  save

        Description: save the settings
        """
        values = Parameter.getParametersValues(self.fields)
        settings_dict = {"pentest_types":values["pentest_types"], "tags": values["tags"]}
        apiclient = APIClient.getInstance()
        for k, v in settings_dict.items():
            if apiclient.getSettings({"key": k}) is None:
                apiclient.createSetting(k, v)
            else:
                apiclient.updateSetting(k, v)



@cls_commands
class PentestSettings(FormModule):
    def __init__(self, parent_context, prompt_session):
        super().__init__('Pentest settings', parent_context, "Pentest settings.", FormattedText(
            [('class:title', f"{parent_context.name}"), ("class:subtitle", f" Pentest settings"), ("class:angled_bracket", " > ")]), IMCompleter(self), prompt_session)
        self.reload()

    def reload(self):
        settings = Settings()
        settings.reloadSettings()
        self.fields = [
            ComboParameter("pentest_type", list(settings.getPentestTypes().keys()), default=settings.getPentestType(),
                      helper="Pentest types (Web, LAN ...) and their associated flaws categories (application, data...)"),
            ListParameter("pentesters",  default=settings.getPentesters(), helper="Pentesters names"),
            TableParameter("tags", ["Tag names", "Color"], default=Settings.getPentestTags(), helper="Tag list and associated colors"),
            BoolParameter("check_new_domain_ip_scope", default=settings.db_settings["include_domains_with_ip_in_scope"], required=False, helper="[true, false] If true, extend scope to any new domain if the ip returned by a DNS query is already in scope"),
            BoolParameter("check_new_domain_tld_in_scope", default=settings.db_settings["include_domains_with_topdomain_in_scope"], required=False, helper="[true, false]  If true, extend scope to any new domain if a parent domain is already in scope"),    
            BoolParameter("add_all_domains_found_in_scope", default=settings.db_settings["include_all_domains"], required=False, helper="/!\\ [true, false]  If true, extend scope to any new domain found by a tool"),    
        ]

    @command
    def show(self):
        """Usage: show
        """
        self.reload()
        super().show()

    @command
    def save(self):
        """Usage:  save

        Description: save the settings
        """
        values = Parameter.getParametersValues(self.fields)
        settings_dict = {"pentest_type":values["pentest_type"], "pentesters": values["pentesters"], "tags": values["tags"], "include_domains_with_ip_in_scope":values["check_new_domain_ip_scope"],
        "include_domains_with_topdomain_in_scope":values["check_new_domain_tld_in_scope"], "include_all_domains":values["add_all_domains_found_in_scope"]}
        apiclient = APIClient.getInstance()
        for k, v in settings_dict.items():
            apiclient.updateInDb(apiclient.getCurrentPentest(), "settings", {
                "key": k}, {"$set": {"value": v}})