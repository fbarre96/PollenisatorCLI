from prompt_toolkit.completion import Completer, Completion

class IMCompleter(Completer):

    def __init__(self, cls):
        self.cls = cls

    # Required by the Completer class
    # Document corresponds to the line hit by the user
    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor()
        cmd_args = document.text.split(" ")
        # should not happen
        if not cmd_args:
            return
        # if first arg is not finished, complete it (1st arg is command name), can be empty; 
        if len(cmd_args) == 1:
            for cmd in self.cls._cmd_list:
                if cmd.startswith(word_before_cursor) and cmd != word_before_cursor:
                    yield Completion(cmd, -len(word_before_cursor))
        # First arg is given, check for a valid command and its options
        else:
            if cmd_args[0] in self.cls._cmd_list:
                # get option for the command with this name
                options = self.cls.getOptionsForCmd(cmd_args[0], cmd_args[1:], complete_event)
                for option in options:
                    if isinstance(option, str):
                        if option.startswith(word_before_cursor) and option != word_before_cursor:
                            yield Completion(option, -len(word_before_cursor))
                    else: # Completion type expected
                        yield option