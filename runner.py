
import plex


class ParseError(Exception):
    # Parse errors
    pass


class RuntimeError(Exception):
    # Runtime errors
    pass


class Runner:
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

        self.stack = {}

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
                'expected ID = ( Expr ), got {}'.format(self.text))

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
            identifier = self.text
            self.match('ID')
            self.match('ASSIGN')
            self.stack[identifier] = self.expr()
        elif self.la == 'PRINT':
            self.match('PRINT')
            print("{:b}".format(self.expr()))
        else:
            raise ParseError('Expected statement, got {}'.format(self.text))
        return

    def expr(self):
        if self.la == 'LEFTPAR' or self.la == 'ID' or self.la == 'BINARY':
            term = self.term()
            tail = self.term_tail()
            if tail is None:
                return term
            if tail[0] == "OR":
                return self.do_or(term, tail[1])
        else:
            raise ParseError('Expected expression, got {}'.format(self.text))
        return

    def term_tail(self):
        if self.la == 'OR':
            self.or_op()
            term = self.term()
            tail = self.term_tail()
            if tail is None:
                return 'OR', term
            if tail[0] == "OR":
                return 'OR', self.do_or(term, tail[1])
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
            factor = self.factor()
            tail = self.factor_tail()
            if tail is None:
                return factor
            if tail[0] == "XOR":
                return self.do_xor(factor, tail[1])
        else:
            raise ParseError('Expected term, got {}'.format(self.text))
        return

    def factor_tail(self):
        if self.la == 'XOR':
            self.xor_op()
            factor = self.factor()
            tail = self.factor_tail()
            if tail is None:
                return 'XOR', factor
            if tail[0] == "XOR":
                return 'XOR', self.do_xor(factor, tail[1])
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
            factor = self.atom()
            tail = self.atom_tail()
            if tail is None:
                return factor
            if tail[0] == "AND":
                return self.do_and(factor, tail[1])
        else:
            raise ParseError('Expected factor, got {}'.format(self.text))
        return

    def atom_tail(self):
        if self.la == 'AND':
            self.and_op()
            atom = self.atom()
            tail = self.atom_tail()
            if tail is None:
                return 'AND', atom
            if tail[0] == "AND":
                return 'AND', self.do_and(atom, tail[1])
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
            expr = self.expr()
            self.match('RIGHTPAR')
            return expr
        elif self.la == 'ID':
            identifier = self.text
            self.match('ID')
            if identifier in self.stack:
                return self.stack[identifier]
            else:
                raise RuntimeError(
                    'Variable {} doesn\'t exi-\n'.format(identifier))
        elif self.la == 'BINARY':
            binary = self.text
            self.match('BINARY')
            return int(binary, 2)
        else:
            raise ParseError('Expected atom, got {}'.format(self.text))
        return

    def and_op(self):
        if self.la == 'AND':
            self.match('AND')
            return 'AND'
        else:
            raise ParseError(
                'Expected bitwise AND operator, got "{}"'.format(self.text))

    def xor_op(self):
        if self.la == 'XOR':
            self.match('XOR')
            return 'XOR'
        else:
            raise ParseError(
                'Expected bitwise XOR operator, got "{}"'.format(self.text))

    def or_op(self):
        if self.la == 'OR':
            self.match('OR')
            return 'OR'
        else:
            raise ParseError(
                'Expected bitwise OR operator, got "{}"'.format(self.text))

    def do_and(self, a, b):
        return a & b

    def do_xor(self, a, b):
        return a ^ b

    def do_or(self, a, b):
        return a | b


parser = Runner()

with open('data.in') as fp:
    try:
        parser.parse(fp)
    except plex.errors.PlexError:
        _, line, char = parser.position()
        print("Plex Error: at line {} char {}".format(line, char + 1))
    except ParseError as err:
        _, line, char = parser.position()
        print("Parse Error: {} at line {} char {}".format(
            err, line, char + 1))
