# Written by Hunter Wilkins
# Followed Bob Nystrom's book: Crafting Interpreter
# https://craftinginterpreters.com/contents.html

import sys
from LoxErrors import GlobalErrors
from Lox.Parser import Parser
from Lox.Resolver import Resolver
from Lox.Interpreter import Interpreter
from Lox.Scanner import Scanner


interpreter = Interpreter()


def run(source):
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    parser = Parser(tokens)
    statements = parser.parse()

    if GlobalErrors.had_error or GlobalErrors.had_runtime_error or statements[0] is None:
        return
    else:
        resolver = Resolver(interpreter)
        resolver.resolve(statements)

        if GlobalErrors.had_error or GlobalErrors.had_runtime_error:
            return

        interpreter.interpret(statements)


def run_file(filename):
    with open(filename, 'r') as file:
        code = file.read()
        run(code)

        if GlobalErrors.had_error:
            sys.exit(65)
        elif GlobalErrors.had_runtime_error:
            sys.exit(70)


def run_prompt():
    while True:
        run(input('> '))
        GlobalErrors.had_error = False
        GlobalErrors.had_runtime_error = False


def main():
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        run_prompt()


if __name__ == '__main__':
    main()
