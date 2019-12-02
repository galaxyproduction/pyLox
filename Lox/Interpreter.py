from Lox.Stmt import StmtVisitor
from Lox.SyntaxTree import ExprVisitor
from Lox.TokenType import TokenType
from Lox.LoxFunction import LoxFunction
from Lox.LoxInstance import LoxInstance
from Lox.LoxCallable import LoxCallable, Clock, Read, Float
from Lox.LoxClass import LoxClass
from Lox.Enviorment import Environment
from LoxErrors.Error import Error
from LoxErrors.RuntimeException import RuntimeException
from LoxErrors.ReturnException import Return


class Interpreter(ExprVisitor, StmtVisitor):
    def __init__(self):
        self.globals = Environment()

        self.globals.define("clock", Clock())
        self.globals.define("read", Read())
        self.globals.define("float", Float())
        self.environment = self.globals
        self.locals = {}

    def interpret(self, statements):
        try:
            for statement in statements:
                if statement is not None:
                    self.execute(statement)
        except RuntimeException as error:
            Error.runtime_error(error)

    def visit_expression_stmt(self, stmt):
        self.evaluate(stmt.expression)
        return None

    def visit_function_stmt(self, stmt):
        function = LoxFunction(stmt, self.environment, False)
        self.environment.define(stmt.name.lexem, function)
        return None

    def visit_if_stmt(self, stmt):
        if self.is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            self.execute(stmt.else_branch)
        else:
            return None

    def visit_return_stmt(self, stmt):
        value = None
        if stmt.value is not None:
            value = self.evaluate(stmt.value)

        raise Return(value)

    def visit_print_stmt(self, stmt):
        value = self.evaluate(stmt.expression)
        print(self.stringify(value))
        return None

    def visit_var_stmt(self, stmt):
        value = None
        if stmt.initializer is not None:
            value = self.evaluate(stmt.initializer)

        self.environment.define(stmt.name.lexem, value)
        return None

    def visit_while_stmt(self, stmt):
        while self.is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.body)
        return None

    def visit_assign_expr(self, expr):
        value = self.evaluate(expr.value)

        if self.locals.keys().__contains__(expr):
            distance = self.locals[expr]
            self.environment.assign_at(distance, expr.name, value)
        else:
            self.globals.assign(expr.name, value)

        return value

    def visit_binary_expr(self, expr):
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)

        operator_type = expr.operator.type
        if operator_type == TokenType.MINUS:
            self.check_number_operands(expr.operator, left, right)
            return left - right
        elif operator_type == TokenType.SLASH:
            self.check_number_operands(expr.operator, left, right)
            return left / right
        elif operator_type == TokenType.STAR:
            self.check_number_operands(expr.operator, left, right)
            return left * right
        elif operator_type == TokenType.MODULO:
            self.check_number_operands(expr.operator, left, right)
            return left % right
        elif operator_type == TokenType.PLUS:
            if type(left) == float and type(right) == float:
                return left + right
            elif (type(left) == str or type(left) == float) and (type(right) == str or type(right) == float):
                return str(left) + str(right)
            else:
                raise RuntimeException(expr.operator, "Operators must be two numbers or strings.")
        elif operator_type == TokenType.GREATER:
            self.check_number_operands(expr.operator, left, right)
            return left > right
        elif operator_type == TokenType.GREATER_EQUAL:
            self.check_number_operands(expr.operator, left, right)
            return left >= right
        elif operator_type == TokenType.LESS:
            self.check_number_operands(expr.operator, left, right)
            return left < right
        elif operator_type == TokenType.LESS_EQUAL:
            self.check_number_operands(expr.operator, left, right)
            return left <= right
        elif operator_type == TokenType.EQUAL_EQUAL:
            return self.is_equal(left, right)
        elif operator_type == TokenType.BANG_EQUAL:
            return not self.is_equal(left, right)

    def visit_call_expr(self, expr):
        callee = self.evaluate(expr.callee)
        arguments = []
        for argument in expr.arguments:
            arguments.append(self.evaluate(argument))

        if not isinstance(callee, LoxCallable):
            raise RuntimeException(expr.paren, "Can only call functions and classes.")

        function = callee
        if not len(arguments) == function.arity():
            raise RuntimeException(expr.paren, f"Expected {function.arity()} arguments but got {len(arguments)}.")

        return function.call(self, arguments)

    def visit_get_expr(self, expr):
        object = self.evaluate(expr.object)
        if type(object) is LoxInstance:
            return object.get(expr.name)
        else:
            raise RuntimeException(expr.name, "Only instances have properties.")

    def visit_grouping_expr(self, expr):
        return self.evaluate(expr.expression)

    def visit_literal_expr(self, expr):
        return expr.value

    def visit_logic_expr(self, expr):
        left = self.evaluate(expr.left)

        if expr.operator.type == TokenType.OR:
            if self.is_truthy(left):
                return left
        else:
            if not self.is_truthy(left):
                return left

        return self.evaluate(expr.right)

    def visit_set_expr(self, expr):
        object = self.evaluate(expr.object)

        if not type(object) is LoxInstance:
            raise RuntimeException(expr.name, "Only instances have fields.")

        value = self.evaluate(expr.value)
        object.set(expr.name, value)
        return value

    def visit_super_expr(self, expr):
        distance = self.locals[expr]
        superclass = self.environment.get_at(distance, "super")
        object = self.environment.get_at(distance - 1, "this")

        method = superclass.find_method(expr.method.lexem)
        if method is None:
            raise RuntimeException(expr.method, f"Undefined property {expr.method.lexem}.")

        return method.bind(object)

    def visit_this_expr(self, expr):
        return self.look_up_variable(expr.keyword, expr)

    def visit_unary_expr(self, expr):
        right = self.evaluate(expr.right)
        operator_type = expr.operator.type
        if operator_type == TokenType.MINUS:
            self.check_number_operand(expr.operator, right)
            return -right
        elif operator_type == TokenType.BANG:
            return not self.is_truthy(right)

    def visit_variable_expr(self, expr):
        return self.look_up_variable(expr.name, expr)

    def look_up_variable(self, name, expr):
        if self.locals.keys().__contains__(expr):
            distance = self.locals[expr]
            return self.environment.get_at(distance, name.lexem)
        else:
            return self.globals.get(name)

    @staticmethod
    def check_number_operand(operator, operand):
        if type(operand) == float:
            return
        else:
            raise RuntimeException(operator, "Operand must be a number.")

    @staticmethod
    def check_number_operands(operator, left, right):
        if type(left) == float and type(right) == float:
            return
        else:
            raise RuntimeException(operator, "Operands must be a number.")

    def evaluate(self, expr):
        return expr.accept(self)

    def execute(self, stmt):
        stmt.accept(self)

    def resolve(self, expr, depth):
        self.locals[expr] = depth

    def execute_block(self, statements, environment):
        previous = self.environment

        try:
            self.environment = environment

            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def visit_block_stmt(self, stmt):
        self.execute_block(stmt.statements, Environment(self.environment))
        return None

    def visit_class_stmt(self, stmt):
        superclass = None
        if stmt.superclass is not None:
            superclass = self.evaluate(stmt.superclass)
            if not type(superclass) == LoxClass:
                raise RuntimeException(stmt.superclass.name, "Superclass must be a class.")

        self.environment.define(stmt.name.lexem, None)

        if stmt.superclass is not None:
            self.environment = Environment(self.environment)
            self.environment.define("super", superclass)

        methods = {}

        for method in stmt.methods:
            function = LoxFunction(method, self.environment, method.name.lexem == "init")
            methods[method.name.lexem] = function

        klass = LoxClass(stmt.name.lexem, superclass, methods)

        if stmt.superclass is not None:
            self.environment = self.environment.enclosing

        self.environment.assign(stmt.name, klass)
        return None

    @staticmethod
    def is_truthy(object):
        if object is None:
            return False
        elif type(object) == bool:
            return object
        else:
            return True

    @staticmethod
    def is_equal(a, b):
        if a is None and b is None:
            return True
        elif a is None:
            return False
        else:
            return a == b

    @staticmethod
    def stringify(object):
        if object is None:
            return 'Nil'
        else:
            return object.__str__()
