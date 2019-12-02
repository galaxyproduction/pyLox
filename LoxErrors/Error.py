from LoxErrors import GlobalErrors
from Lox.TokenType import TokenType


class Error:
    @classmethod
    def report(cls, line, position, message):
        GlobalErrors.had_error = True
        print(f'[line {line}] Error{position}: {message}')

    @classmethod
    def error(cls, token, message):
        if token.type == TokenType.EOF:
            cls.report(token.line, " at end", message)
        else:
            cls.report(token.line, f" at '{token.lexem}'", message)

    @classmethod
    def runtime_error(cls, error):
        GlobalErrors.had_runtime_error = True
        print(f'{error.__str__()}\n[line {error.token.line}]')
