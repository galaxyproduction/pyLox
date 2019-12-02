from Lox import Stmt, SyntaxTree
from LoxErrors.Error import Error
from Lox.TokenType import TokenType


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        statements = []

        try:
            while not self.is_at_end():
                statements.append(self.declaration())

            return statements
        except ParseError:
            print("Parse error")
            return None

    def expression(self):
        return self.assignment()

    def declaration(self):
        try:
            if self.match(TokenType.CLASS):
                return self.class_declaration()
            if self.match(TokenType.FUN):
                return self.function("function")
            if self.match(TokenType.VAR):
                return self.var_declaration()
            return self.statement()
        except ParseError:
            self.synchronize()
            return None

    def class_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, "Expected class name.")

        superclass = None
        if self.match(TokenType.LESS):
            self.consume(TokenType.IDENTIFIER, "Expected superclass name.")
            superclass = SyntaxTree.Variable(self.previous())
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before class body.")
        methods = []

        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            methods.append(self.function("method"))

        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after class body.")
        return Stmt.Class(name, superclass, methods)

    def statement(self):
        if self.match(TokenType.FOR):
            return self.for_statement()
        elif self.match(TokenType.IF):
            return self.if_statement()
        elif self.match(TokenType.PRINT):
            return self.print_statement()
        elif self.match(TokenType.RETURN):
            return self.return_statement()
        elif self.match(TokenType.WHILE):
            return self.while_statement()
        elif self.match(TokenType.LEFT_BRACE):
            return Stmt.Block(self.block())
        else:
            return self.expression_statement()

    def for_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")
        # initializer = None
        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.match(TokenType.VAR):
            initializer = self.var_declaration()
        else:
            initializer = self.expression_statement()

        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        increment = None
        if not self.check(TokenType.RIGHT_PAREN):
            increment = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        body = self.statement()
        if increment is not None:
            body = Stmt.Block([body, Stmt.Expression(increment)])

        condition = SyntaxTree.Literal(True) if condition is None else condition
        body = Stmt.While(condition, body)

        if initializer is not None:
            body = Stmt.Block([initializer, body])

        return body

    def if_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")
        then_branch = self.statement()
        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.statement()
        return Stmt.If(condition, then_branch, else_branch)

    def print_statement(self):
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after value.")
        return Stmt.Print(value)

    def return_statement(self):
        keyword = self.previous()
        value = None

        if not self.check(TokenType.SEMICOLON):
            value = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return Stmt.Return(keyword, value)

    def var_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, "Expect variable name.")
        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()

        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration")
        return Stmt.Var(name, initializer)

    def while_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after condition.")

        body = self.statement()

        return Stmt.While(condition, body)

    def expression_statement(self):
        expression = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after expression.")
        return Stmt.Expression(expression)

    def function(self, kind):
        name = self.consume(TokenType.IDENTIFIER, f"Expect {kind} name.")
        self.consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        parameters = []

        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                if len(parameters) >= 255:
                    self.error(self.peek(), "Cannot have more than 255 parameters.")

                parameters.append(self.consume(TokenType.IDENTIFIER, "Expected parameter name."))
                if not self.match(TokenType.COMMA):
                    break

        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")
        self.consume(TokenType.LEFT_BRACE, "Expect '{' before " + kind + " body.")
        body = self.block()

        return Stmt.Function(name, parameters, body)

    def block(self):
        statements = []

        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def assignment(self):
        expr = self.OR()

        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()

            if type(expr) == SyntaxTree.Variable:
                name = expr.name
                return SyntaxTree.Assign(name, value)
            elif type(expr) is SyntaxTree.Get:
                return SyntaxTree.Set(expr.object, expr.name, value)

            self.error(equals, "Invalid assignment target.")
        return expr

    def OR(self):
        expr = self.AND()

        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.AND()
            expr = SyntaxTree.Logic(expr, operator, right)

        return expr

    def AND(self):
        expr = self.equality()

        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.equality()
            expr = SyntaxTree.Logic(expr, operator, right)

        return expr

    def equality(self):
        expr = self.comparision()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self.previous()
            right = self.comparision()
            expr = SyntaxTree.Binary(expr, operator, right)

        return expr

    def comparision(self):
        expr = self.addition()

        while self.match(TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS,
                         TokenType.LESS_EQUAL):
            operator = self.previous()
            right = self.addition()
            expr = SyntaxTree.Binary(expr, operator, right)

        return expr

    def addition(self):
        expr = self.multiplication()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous()
            right = self.multiplication()
            expr = SyntaxTree.Binary(expr, operator, right)

        return expr

    def multiplication(self):
        expr = self.modulo()

        while self.match(TokenType.STAR, TokenType.SLASH):
            operator = self.previous()
            right = self.modulo()
            expr = SyntaxTree.Binary(expr, operator, right)

        return expr

    def modulo(self):
        expr = self.unary()

        while self.match(TokenType.MODULO):
            operator = self.previous()
            right = self.unary()
            expr = SyntaxTree.Binary(expr, operator, right)

        return expr

    def unary(self):
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return SyntaxTree.Unary(operator, right)
        else:
            return self.call()

    def finish_call(self, callee):
        arguments = []

        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                if len(arguments) >= 255:
                    self.error(self.peek(), "Cannot have more than 255 arguments.")

                arguments.append(self.expression())

                if not self.match(TokenType.COMMA):
                    break

        paren = self.consume(TokenType.RIGHT_PAREN, "Expect ')' after argument.")

        return SyntaxTree.Call(callee, paren, arguments)

    def call(self):
        expr = self.primary()

        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.DOT):
                name = self.consume(TokenType.IDENTIFIER, "Expected property name after '.'.")
                expr = SyntaxTree.Get(expr, name)
            else:
                break

        return expr

    def primary(self):
        if self.match(TokenType.FALSE):
            return SyntaxTree.Literal(False)
        if self.match(TokenType.TRUE):
            return SyntaxTree.Literal(True)
        if self.match(TokenType.NIL):
            return SyntaxTree.Literal(None)

        if self.match(TokenType.STRING, TokenType.NUMBER):
            return SyntaxTree.Literal(self.previous().literal)

        if self.match(TokenType.SUPER):
            keyword = self.previous()
            self.consume(TokenType.DOT, "Expect '.' after 'super'.")
            method = self.consume(TokenType.IDENTIFIER, "Expect superclass method name.")
            return SyntaxTree.Super(keyword, method)

        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, 'Expected \')\' after expression.')
            return SyntaxTree.Grouping(expr)

        if self.match(TokenType.THIS):
            return SyntaxTree.This(self.previous())

        if self.match(TokenType.IDENTIFIER):
            return SyntaxTree.Variable(self.previous())

        self.error(self.peek(), 'Expected expression')

    def consume(self, token_type, message):
        if self.check(token_type):
            return self.advance()
        else:
            self.error(self.peek(), message)

    def match(self, *args):
        for token_type in args:
            if self.check(token_type):
                self.advance()
                return True

        return False

    def check(self, token_type):
        if self.is_at_end():
            return False
        else:
            return self.peek().type == token_type

    def advance(self):
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self):
        return self.peek().type == TokenType.EOF

    def peek(self):
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    @staticmethod
    def error(token, message):
        Error.error(token, message)
        raise ParseError()

    def synchronize(self):
        self.advance()

        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return

            peek_type = self.peek().type

            if (peek_type == TokenType.CLASS or
                    peek_type == TokenType.FUN or
                    peek_type == TokenType.VAR or
                    peek_type == TokenType.FOR or
                    peek_type == TokenType.IF or
                    peek_type == TokenType.WHILE or
                    peek_type == TokenType.PRINT or
                    peek_type == TokenType.RETURN):
                return

            self.advance()
