import os.path


class Config:
    """
    Represents spectrum2 configuration options.

    I'm guessing this is the format of the spectrum config file in BNF
    <config_file> ::= <line>*
    <line> ::= <space>* <expr> <space>* <newline> | <space*>
    <expr> ::= <section> | <assignment>
    <section> ::= [<identifier>*]
    <assignment> ::= <identifier> <space>* = <space>* <value>
    """
    def __init__(self, path_to_config_file):
        """
        Initialises configuration file.

        @param path_to_config_file: The absolute path
                                    to the configuration file.
        """
        self.config_path = path_to_config_file
        self.options = self.load_config(self.config_path)

        # Load backend_logging information
        if 'logging.backend_config' in self.options:
            if os.path.isfile(self['logging.backend_config']):
                config = self.load_config(self['logging.backend_config'])
                self.options.update(config)

    def load_config(self, file_name):
        # Current section heading,
        # It's a dictionary because variables in python closures can't be
        # assigned to.
        section = {'a': ''}
        options = dict()

        # Recursive descent parser

        def consume_spaces(line):
            i = 0
            for c in line:
                if c != ' ':
                    break
                i += 1

            return line[i:]

        def read_identifier(line):
            i = 0
            for c in line:
                if c in (' ', ']', '[', '='):
                    break
                i += 1

            # no identifier
            if i == 0:
                return (None, 'No identifier')

            return (line[:i], line[i:])

        def parse_section(line):
            if not line or line[0] != '[':
                return (None, 'expected [')

            line = line[1:]
            identifier, line = read_identifier(line)

            if not line or line[0] != ']' or identifier is None:
                return (None, line)

            return (identifier, line[1:])

        def parse_assignment(line):
            key, line = read_identifier(line)
            if key is None:
                return (None, None, line)

            line = consume_spaces(line)
            if not line or line[0] != '=':
                return (None, None, 'Expected =')

            line = consume_spaces(line[1:])
            value = line[:-1]

            return (key, value, '\n')

        def expr(line):
            sec, newline = parse_section(line)
            if sec is not None:
                section['a'] = sec
            else:
                key, value, newline = parse_assignment(line)
                if key is not None:
                    if section['a'] != '':
                        options[section['a'] + '.' + key] = value
                    else:
                        options[key] = value
                else:
                    return (None, newline)

            return (newline, None)

        def parse_line(line, line_number):
            line = consume_spaces(line)
            if line == '\n':
                return

            newline, error = expr(line)
            if newline is None:
                raise ConfigParseError(
                    '{}: Expected newline got {}'.format(line_number, newline))

            newline = consume_spaces(newline)
            if newline != '\n':
                raise ConfigParseError(
                    '{}: Expected newline got {}'.format(line_number, newline))

        def strip_comments(line):
            i = 0
            for c in line:
                if c in ('#', '\n'):
                    break
                i += 1

            return line[:i] + '\n'

        with open(file_name, 'r') as f:
            i = 1
            while True:
                line = f.readline()
                if line == '':
                    break
                parse_line(strip_comments(line), i)
                i += 1
        return options

    def __getitem__(self, key):
        return self.options[key]


class ConfigParseError(Exception):
    pass
