"""Hold functions to interact with the admin api"""
from pollenisatorcli.core.apiclient import APIClient
from pollenisatorcli.core.Modules.module import Module
from pollenisatorcli.utils.utils import command, cls_commands, print_error, print_formatted, print_formatted_text, style_table
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit import prompt
from pollenisatorcli.utils.completer import IMCompleter
from prompt_toolkit.shortcuts import confirm
from terminaltables import AsciiTable
name = "Admin" # Used in command decorator

@cls_commands
class Admin(Module):
    """admin module"""

    def __init__(self, parent_context, prompt_session):
        super().__init__('Admin', parent_context, "Manage Users.", FormattedText([('class:title', "Admin"),('class:angled_bracket', " > ")]), IMCompleter(self), prompt_session)
        self.adminonly = True

    @command
    def ls(self):
        """Usage: ls 
        Description: List all users
        """
        apiclient = APIClient.getInstance()
        users = apiclient.getUsers()
        table_data = [['Username', 'Admin']]
        for user in users:
            username = user["username"]
            admin = "Admin" if "admin" in user["scope"] else ""
            table_data.append([username, admin])
        table = AsciiTable(table_data)
        table = style_table(table)
        print_formatted_text(table.table+"\n")
        
    @command
    def insert(self):
        """Usage: insert
        Description: Add a new user
        """
        apiclient = APIClient.getInstance()
        username = prompt('Username > ')
        password = prompt("Password > ",is_password=True)
        confirm_password = prompt("Confirm Password > ", is_password=True)
        if password != confirm_password:
            print_error("The password does not match the confirmation")
        apiclient.registerUser(username, password)

    @command
    def password(self, username):
        """Usage: password <username>
        Description: change password for the given username
        Args:
            username: the username that will change passwords
        """
        newPwd = prompt(f"New password for {username}> ", is_password=True)
        APIClient.getInstance().resetPassword(username, newPwd)

    @command
    def delete(self, username):
        """Usage: delete <username>
        Description: delete the given username
        Args:
            username: the username that will be deleted
        """
        apiclient = APIClient.getInstance()
        answer = confirm(f"Confirm deletion of {username}")
        if answer:
            apiclient.deleteUser(username) 
    

    def getOptionsForCmd(self, cmd, cmd_args, complete_event):
        """Returns a list of valid options for the given cmd
        """  
        apiclient = APIClient.getInstance()
        if cmd in ["delete", "password"]:
            return [x["username"] for x in apiclient.getUsers()]
        return []