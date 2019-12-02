from LoxErrors.Error import Error
from Lox.TokenType import TokenType


def keywords_init():
    keywords = {"and": TokenType.AND, "class": TokenType.CLASS, "else": TokenType.ELSE, "false": TokenType.FALSE,
                "for": TokenType.FOR, "fun": TokenType.FUN, "if": TokenType.IF, "nil": TokenType.NIL,
                "or": TokenType.OR, "print": TokenType.PRINT, "return": TokenType.RETURN, "super": TokenType.SUPER,
                "this": TokenType.THIS, "true": TokenType.TRUE, "var": TokenType.VAR, "while": TokenType.WHILE}
    return keywords


class Scanner:
    def __init__(self, source):
        self.source = source
        self.tokens = []
        self.keywords = keywords_init()
        self.start = 0
        self.current = 0
        self.line = 1

    def scan_tokens(self):
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def scan_token(self):
        c = self.advance()
        if c == '(':
            self.add_token(TokenType.LEFT_PAREN)
        elif c == ')':
            self.add_token(TokenType.RIGHT_PAREN)
        elif c == '{':
            self.add_token(TokenType.LEFT_BRACE)
        elif c == '}':
            self.add_token(TokenType.RIGHT_BRACE)
        elif c == ',':
            self.add_token(TokenType.COMMA)
        elif c == '.':
            self.add_token(TokenType.DOT)
        elif c == '-':
            self.add_token(TokenType.MINUS)
        elif c == '%':
            self.add_token(TokenType.MODULO)
        elif c == '+':
            self.add_token(TokenType.PLUS)
        elif c == ';':
            self.add_token(TokenType.SEMICOLON)
        elif c == '*':
            self.add_token(TokenType.STAR)
        elif c == '!':
            self.add_token(TokenType.BANG_EQUAL if self.match('=') else TokenType.BANG)
        elif c == '=':
            self.add_token(TokenType.EQUAL_EQUAL if self.match('=') else TokenType.EQUAL)
        elif c == '<':
            self.add_token(TokenType.LESS_EQUAL if self.match('=') else TokenType.LESS)
        elif c == '>':
            self.add_token(TokenType.GREATER_EQUAL if self.match('=') else TokenType.GREATER)
        elif c == '/':
            if self.match('/'):
                while (not self.peek() == '\n') and not self.is_at_end():
                    self.advance()
            else:
                self.add_token(TokenType.SLASH)
        elif c == ' ' or c == '\r' or c == '\t':
            return
        elif c == '"':
            self.string()
        elif c == '\n':
            self.line += 1
        else:
            if c.isdigit():
                self.number()
            elif c.isalpha() or c == '_':
                self.identifier()
            else:
                Error.error(self.line, "Unexpected character.")

    def is_at_end(self):
        return self.current >= len(self.source)

    def advance(self):
        self.current += 1
        return self.source[self.current - 1]

    def add_token(self, token_type, literal=None):
        text = self.source[self.start: self.current]
        self.tokens.append(Token(token_type, text, literal, self.line))

    def match(self, expected):
        if self.is_at_end():
            return False
        if not self.source[self.current] == expected:
            return False

        self.current += 1
        return True

    def peek(self):
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def string(self):
        while not self.peek() == '"' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
            self.advance()

        if self.is_at_end():
            Error.error(self.line, "Unterminated string.")
            return

        self.advance()

        value = self.source[self.start + 1:self.current - 1]
        self.add_token(TokenType.STRING, value)

    def number(self):
        while self.peek().isdigit():
            self.advance()

        if self.peek() == '.' and self.peek_next().isdigit():
            self.advance()

            while self.peek().isdigit():
                self.advance()

        self.add_token(TokenType.NUMBER, float(self.source[self.start:self.current]))

    def peek_next(self):
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def identifier(self):
        while self.is_alpha_numeric(self.peek()):
            self.advance()

        text = self.source[self.start: self.current]
        if self.keywords.__contains__(text):
            self.add_token(self.keywords[text])
        else:
            self.add_token(TokenType.IDENTIFIER)

    @staticmethod
    def is_alpha_numeric(c):
        return c.isdigit() or c.isalpha() or c == '_'


class Token:
    def __init__(self, token_type, lexem, literal, line):
        self.type = token_type
        self.lexem = lexem
        self.literal = literal
        self.line = line

    def __str__(self):
        return f'{self.type} {self.lexem} {self.literal}'
