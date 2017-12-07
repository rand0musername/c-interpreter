class Node(object):
    pass


class NoOp(Node):
    pass


class Num(Node):
    def __init__(self, token):
        self.token = token
        self.value = token.value


class String(Node):
    def __init__(self, token):
        self.token = token
        self.value = token.value


class Type(Node):
    def __init__(self, token):
        self.token = token
        self.value = token.value


class Var(Node):
    def __init__(self, token):
        self.token = token
        self.value = token.value


class BinOp(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


class UnOp(Node):
    def __init__(self, op, expr, prefix=True):
        self.token = self.op = op
        self.expr = expr
        self.prefix = prefix


class TerOp(Node):
    def __init__(self, condition, texpression, fexpression):
        self.condition = condition
        self.texpression = texpression
        self.fexpression = fexpression


class Assign(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


class Expression(Node):
    def __init__(self, children):
        self.children = children


class FunctionCall(Node):
    def __init__(self, name, args):
        self.name = name
        self.args = args            # a list of Param nodes


class IfStmt(Node):
    def __init__(self, condition, tbody, fbody=None):
        self.condition = condition
        self.tbody = tbody
        self.fbody = fbody


class WhileStmt(Node):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class DoWhileStmt(WhileStmt):
    pass


class ReturnStmt(Node):
    def __init__(self, expression):
        self.expression = expression


class BreakStmt(Node):
    pass


class ContinueStmt(Node):
    pass


class ForStmt(Node):
    def __init__(self, setup, condition, increment, body):
        self.setup = setup
        self.condition = condition
        self.increment = increment
        self.body = body


class CompoundStmt(Node):
    def __init__(self, children):
        self.children = children


class VarDecl(Node):
    def __init__(self, var_node, type_node):
        self.var_node = var_node
        self.type_node = type_node


class IncludeLibrary(Node):
    def __init__(self, library_name):
        self.library_name = library_name


class Param(Node):
    def __init__(self, type_node, var_node):
        self.var_node = var_node
        self.type_node = type_node


class FunctionDecl(Node):
    def __init__(self, type_node, func_name, params, body):
        self.type_node = type_node
        self.func_name = func_name
        self.params = params            # a list of Param nodes
        self.body = body


class Program(Node):
    def __init__(self, declarations):
        self.children = declarations


###############################################################################
#                                                                             #
#  AST visitors (walkers)                                                     #
#                                                                             #
###############################################################################

class NodeVisitor(object):
    def visit(self, node, *args, **kwargs):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, *args, **kwargs)

    def generic_visit(self, node, *args, **kwargs):
        raise Exception('No visit_{} method'.format(type(node).__name__))

