from Lox.Stmt import StmtVisitor
from Lox.SyntaxTree import ExprVisitor
from enum import Enum
from LoxErrors.Error import Error
from collections import deque


class Function(Enum):
    none = 1
    function = 2
    initializer = 3
    method = 4


class ClassType(Enum):
    NONE = 1,
    CLASS = 2,
    SUBCLASS = 3


class Resolver(StmtVisitor, ExprVisitor):
    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.scopes = deque()
        self.current_function = Function.none
        self.current_class = ClassType.NONE

    def visit_block_stmt(self, stmt):
        self.begin_scope()
        self.resolve(stmt.statements)
        self.end_scope()
        return None

    def visit_class_stmt(self, stmt):
        enclosing_class = self.current_class
        self.current_class = ClassType.CLASS

        self.declare(stmt.name)
        self.define(stmt.name)

        if stmt.superclass is not None:
            if stmt.name.lexem == stmt.superclass.name.lexem:
                Error.error(stmt.superclass.name, "A class cannot inherit from itself.")
            else:
                self.current_class = ClassType.SUBCLASS
                self.resolve(stmt.superclass)
                self.begin_scope()
                self.scopes[-1]["super"] = True

        self.begin_scope()
        self.scopes[-1]["this"] = True

        for method in stmt.methods:
            declaration = Function.method
            if method.name.lexem == "init":
                declaration = Function.initializer
            self.resolve_function(method, declaration)

        self.end_scope()

        if stmt.superclass is not None:
            self.end_scope()

        self.current_class = enclosing_class
        return None

    def visit_expression_stmt(self, stmt):
        self.resolve(stmt.expression)
        return None

    def visit_if_stmt(self, stmt):
        self.resolve(stmt.condition)
        self.resolve(stmt.then_branch)

        if stmt.else_branch is not None:
            self.resolve(stmt.else_branch)

        return None

    def visit_print_stmt(self, stmt):
        self.resolve(stmt.expression)
        return None

    def visit_return_stmt(self, stmt):
        if self.current_function == Function.none:
            Error.error(stmt.keyword, "Cannot return from top-level code")

        if stmt.value is not None:
            if self.current_function == Function.initializer:
                Error.error(stmt.keyword, "Cannot return from an initializer.")
            self.resolve(stmt.value)

        return None

    def visit_while_stmt(self, stmt):
        self.resolve(stmt.condition)
        self.resolve(stmt.body)
        return None

    def visit_binary_expr(self, expr):
        self.resolve(expr.left)
        self.resolve(expr.right)
        return None

    def visit_call_expr(self, expr):
        self.resolve(expr.callee)
        for argument in expr.arguments:
            self.resolve(argument)

        return None

    def visit_get_expr(self, expr):
        self.resolve(expr.object)
        return None

    def visit_grouping_expr(self, expr):
        self.resolve(expr.expression)
        return None

    def visit_literal_expr(self, expr):
        return None

    def visit_logic_expr(self, expr):
        self.resolve(expr.left)
        self.resolve(expr.right)
        return None

    def visit_set_expr(self, expr):
        self.resolve(expr.value)
        self.resolve(expr.object)
        return None

    def visit_super_expr(self, expr):
        if self.current_class == ClassType.NONE:
            Error.error(expr.keyword, "Cannot use 'super' outside of a class.")
        elif self.current_class != ClassType.SUBCLASS:
            Error.error(expr.keyword, "Cannot use 'super' in a class without a super class.")
        self.resolve_local(expr, expr.keyword)
        return None

    def visit_this_expr(self, expr):
        if self.current_class == ClassType.NONE:
            Error.error(expr.keyword, "Cannot use 'this' outside of a class.")
            return None

        self.resolve_local(expr, expr.keyword)
        return None

    def visit_unary_expr(self, expr):
        self.resolve(expr.right)
        return None

    def visit_function_stmt(self, stmt):
        self.declare(stmt.name)
        self.define(stmt.name)
        self.resolve_function(stmt, Function.function)
        return None

    def visit_var_stmt(self, stmt):
        self.declare(stmt.name)
        if stmt.initializer is not None:
            self.resolve(stmt.initializer)
        self.define(stmt.name)
        return None

    def visit_assign_expr(self, expr):
        self.resolve(expr.value)
        self.resolve_local(expr, expr.name)
        return None

    def visit_variable_expr(self, expr):
        if not len(self.scopes) == 0 and self.scopes[-1].keys().__contains__(expr.name.lexem) and \
                not self.scopes[-1][expr.name.lexem]:
            Error.error(expr.name, "Cannot read local variable in its own initializer.")

        self.resolve_local(expr, expr.name)
        return None

    def resolve(self, statements):
        if not type(statements) is list:
            statements.accept(self)
        else:
            for statement in statements:
                statement.accept(self)

    def resolve_function(self, function, token_type):
        enclosing_function = self.current_function
        self.current_function = token_type
        self.begin_scope()
        for param in function.params:
            self.declare(param)
            self.define(param)

        self.resolve(function.body)
        self.end_scope()
        self.current_function = enclosing_function

    def begin_scope(self):
        # Dict<string, bool>
        self.scopes.append({})

    def end_scope(self):
        self.scopes.pop()

    def declare(self, name):
        if len(self.scopes) == 0:
            return

        scope = self.scopes[-1]
        if scope.keys().__contains__(name.lexem):
            Error.error(name, "Variable with this name already declared in this scope.")

        scope[name.lexem] = False

    def define(self, name):
        if len(self.scopes) == 0:
            return

        scope = self.scopes[-1]
        scope[name.lexem] = True

    def resolve_local(self, expr, name):
        for i in range(len(self.scopes) - 1, -1, -1):
            if self.scopes[i].keys().__contains__(name.lexem):
                self.interpreter.resolve(expr, len(self.scopes) - 1 - i)
                return
