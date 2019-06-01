
import plex


class ParseError (Exception):
    # Represents a user-defined exception class
    pass


class Parser:
    # Encapsulates all parsing functionality for a particular grammar.

    def __init__(self):

        letter = plex.Range('azAz')
        digit = plex.Range('09')

        ID = letter + plex.Rep(letter | digit)

        BINARY = plex.Rep1(plex.Range('01'))

        AND = plex.Str('and')
        OR = plex.Str('or')
        XOR = plex.Str('xor')

        ASSIGN = plex.Str('=')

        LEFTPAR = plex.Str('(')
        RIGHTPAR = plex.Str(')')

        PRINT = plex.NoCase(plex.Str('PRINT'))

        self.lexicon = plex.Lexicon([

            (AND, 'AND'),
            (OR, 'OR'),
            (XOR, 'XOR'),
            (ASSIGN, 'ASSIGN'),
            (LEFTPAR, 'LEFTPAR'),
            (RIGHTPAR, 'RIGHTPAR'),
            (PRINT, 'PRINT'),
            (BINARY, 'BINARY'),
            (ID, 'ID'),
            (plex.Rep1(plex.Any(" \t\n")), plex.IGNORE)

        ])

    def position(self):
        # Utility function that returns position in text in case of errors.
        # Here it simply returns the scanner position.
        return self.scanner.position()

    def match(self, token):
        # Consumes (matches with current lookahead) an expected token.
        # Raises ParseError if anything else is found. Acquires new lookahead.
        if self.la == token:
            self.la, self.text = self.scanner.read()
        else:
            raise ParseError(
                'Expected valid expression, got {}'.format(self.text))

    def create_scanner(self, fp):
        # create and store the scanner object
        self.scanner = plex.Scanner(self.lexicon, fp)
        # get initial lookahead
        self.la, self.text = self.next_token()

    def next_token(self):
        # Returns tuple (next_token,matched-text).
        return self.scanner.read()

    def parse(self, fp):
        self.create_scanner(fp)
        # insert magic
        self.stmt_list()

        print('Parsed successfully')

    def stmt_list(self):
        if self.la == 'ID' or self.la == 'PRINT':
            self.stmt()
            self.stmt_list()
        # follow
        elif self.la is None:
            return
        else:
            raise ParseError(
                'Expected statement list, got {}'.format(self.text))
        return

    def stmt(self):
        if self.la == 'ID':
            self.match('ID')
            self.match('ASSIGN')
            self.expr()
        elif self.la == 'PRINT':
            self.match('PRINT')
            self.expr()
        else:
            raise ParseError('Expected statement, got {}'.format(self.text))
        return

    def expr(self):
        if self.la == 'LEFTPAR' or self.la == 'ID' or self.la == 'BINARY':
            self.term()
            self.term_tail()
        else:
            raise ParseError('Expected expression, got {}'.format(self.text))
        return

    def term_tail(self):
        if self.la == 'OR':
            self.match('OR')
            self.term()
            self.term_tail()
        elif (
            self.la == 'RIGHTPAR'
            or self.la == 'ID'
            or self.la == 'PRINT'
            or self.la is None
        ):
            return
        else:
            raise ParseError('Expected term tail, got {}'.format(self.text))
        return

    def term(self):
        if self.la == 'LEFTPAR' or self.la == 'ID' or self.la == 'BINARY':
            self.factor()
            self.factor_tail()
        else:
            raise ParseError('Expected term, got {}'.format(self.text))
        return

    def factor_tail(self):
        if self.la == 'XOR':
            self.match('XOR')
            self.factor()
            self.factor_tail()
        elif (
            self.la == 'RIGHTPAR'
            or self.la == 'OR'
            or self.la == 'ID'
            or self.la == 'PRINT'
            or self.la is None
        ):
            return
        else:
            raise ParseError('Expected factor tail, got {}'.format(self.text))
        return

    def factor(self):
        if self.la == 'LEFTPAR' or self.la == 'ID' or self.la == 'BINARY':
            self.atom()
            self.atom_tail()
        else:
            raise ParseError('Expected factor, got {}'.format(self.text))
        return

    def atom_tail(self):
        if self.la == 'AND':
            self.match('AND')
            self.atom()
            self.atom_tail()
        elif (
            self.la == 'RIGHTPAR'
            or self.la == 'XOR'
            or self.la == 'OR'
            or self.la == 'ID'
            or self.la == 'PRINT'
            or self.la is None
        ):
            return
        else:
            raise ParseError('Expected atom tail, got {}'.format(self.text))
        return

    def atom(self):
        if self.la == 'LEFTPAR':
            self.match('LEFTPAR')
            self.expr()
            self.match('RIGHTPAR')
        elif self.la == 'ID':
            self.match('ID')
        elif self.la == 'BINARY':
            self.match('BINARY')
        else:
            raise ParseError('Expected atom, got {}'.format(self.text))
        return


parser = Parser()

with open('data.in') as fp:
    parser.parse(fp)
