from .memory import *
from .number import Number
from ..lexical_analysis.lexer import Lexer
from ..lexical_analysis.token_type import *
from ..syntax_analysis.parser import Parser
from ..syntax_analysis.tree import *
from ..semantic_analysis.analyzer import SemanticAnalyzer
from ..common.utils import get_functions, get_constants, MessageColor
from ..common.visitor import Visitor
from ..common.ctype import CType, StructCType


class ControlFlowFlag:
    def __init__(self, value):
        # BREAK or CONTINUE
        self.value = value


class Interpreter(Visitor):

    def __init__(self):
        """ Initializes the memory for this run """
        # we can use declare, memory[] for values, get_address, new/del_scope, new/del_frame
        # the Memory class takes care of the underlying logic
        self.memory = Memory()

    # Program and its children - interpreted before _init
    # these visits don't return anything

    def visit_Program(self, node):
        """
        Visits the AST root: forwards the call to children
        (IncludeLibrary, FunctionDecl, VarDecl+Assignment)
        """
        for child in node.children:
            assert(isinstance(child, (FunctionDecl, IncludeLibrary, VarDecl, StructDecl)))
            self.visit(child)

    def visit_IncludeLibrary(self, node):
        """ Maps function name to the actual python function """
        module_name = 'interpreter.__builtins__.{}'.format(
            node.library_name
        )
        functions = get_functions(module_name)
        for func in functions:
            self.memory.declare_fun(func.__name__)
            self.memory[func.__name__] = func

        consts = get_constants(module_name)
        for name, value in consts:
            self.memory.declare_constant(name, value)

    def visit_FunctionDecl(self, node):
        """ Maps function name to FunctionDecl node """
        self.memory.declare_fun(node.func_name)
        self.memory[node.func_name] = node

    def visit_VarDecl(self, node):
        """ Declares a new variable """
        c_type = node.type_node.c_type
        if isinstance(c_type, StructCType):
            # declare a struct var
            self.memory.declare_struct_var(node.type_node.c_type, node.var_node.value)
        else:
            self.memory.declare_num(node.type_node.c_type, node.var_node.value)

    def visit_StructDecl(self, node):
        """ Declares a new struct """
        self.memory.declare_struct(node.name)
        self.memory[node.name] = node

    # functions
    # these visits return function return value (as a Number)
    memory_modifying_fns = ['scanf', 'malloc', 'free']

    def visit_FunctionCall(self, node):
        # Evaluate argument expressions
        args = [self.visit(arg) for arg in node.args]

        """
               FunctionDecl functions can access the memory since they are evaluated in the 
               context of the current interpreter. However, python library functions that need
               to work with memory have no way of accessing it. One way of doing this is having
               a singleton memory, but that is considered bad practice, so for now we will send 
               an additional memory argument to all functions that need it.
        """
        if node.name in Interpreter.memory_modifying_fns:
            args.append(self.memory)

        """
        Since our library functions are just pure python functions we have
        to treat them as black boxes - they are never parsed so we can't 
        simulate their behaviour, in this case we just return the value
        """
        func = self.memory[node.name]
        if callable(func):

            # pass regular numbers to python functions
            for i in range(len(args)):
                val = args[i]
                if isinstance(val, Number):
                    args[i] = val.value

            ret = func(*args)
            if ret is None:
                return ret
            return Number(CType.from_string(func.return_type), ret)

        # Otherwise, func is a FunctionDecl AstNode, we can properly simulate

        # Create a new frame
        self.memory.new_frame(func.func_name)

        """
            Declare params in the new frame
             
            Note: In reality param values just get pushed on the stack and the new frame
            works with them using an offset from the frame start. Since we just simulate 
            frames and there is no notion of memory addresses it is acceptable to just declare
            param variables in the new frame. Doing parameter passing on a lower level than the
            whole memory is not very useful and it would also break some design decisions.
        """
        for idx, arg in enumerate(args):
            param = func.params[idx]
            self.memory.declare_num(param.type_node.c_type, param.var_node.value)
            self.memory[param.var_node.value] = arg

        # Visit the function body and cast the return value to the appropriate type
        raw_ret_val = self.visit(func.body)
        if raw_ret_val is None:
            return raw_ret_val
        ret_val = Number(func.type_node.c_type, raw_ret_val.value)
        # Delete the frame and return
        self.memory.del_frame()
        return ret_val

    def visit_FunctionBody(self, node):
        for child in node.children:
            if isinstance(child, ReturnStmt):
                return self.visit(child)
            self.visit(child)
        return None

    # statements
    # loops return nothing
    # "ReturnStmt" returns function return value
    # "ContinueStmt BreakStmt" return a cf flag
    # other statements just propagate return values
    # [cf flags are guaranteed to be return inside a loop scope]

    def visit_CompoundStmt(self, node):
        self.memory.new_scope()
        for child in node.children:
            ret = self.visit(child)
            # catch the cf flag and propagate up
            # break will break the outer loop
            # continue can be ignored by the loop but it will break compound statements
            if isinstance(ret, ControlFlowFlag):
                self.memory.del_scope()
                return ret
        self.memory.del_scope()
        return None

    def visit_ReturnStmt(self, node):
        return self.visit(node.expression)

    def visit_BreakStmt(self, node):
        return ControlFlowFlag("BREAK")

    def visit_ContinueStmt(self, node):
        return ControlFlowFlag("CONTINUE")

    def visit_SwitchStmt(self, node):
        expr = self.visit(node.expr)
        # Find a case that matches
        do_execute = False
        for child in node.children:
            if not do_execute:
                if isinstance(child, SwitchCaseLabel):
                    case_expr = self.visit(child.expr)
                    if case_expr == expr:
                        do_execute = True
                elif isinstance(child, SwitchDefaultLabel):
                    do_execute = True
            else:
                # execute!
                if not isinstance(child, SwitchCaseLabel) and not isinstance(child, SwitchDefaultLabel):
                    ret = self.visit(child)
                    if isinstance(ret, ControlFlowFlag) and ret.value == "BREAK":
                        break

    def visit_IfStmt(self, node):
        if self.visit(node.condition):
            return self.visit(node.true_body)
        else:
            return self.visit(node.false_body)

    # loops

    def visit_WhileStmt(self, node):
        while self.visit(node.condition):
            ret = self.visit(node.body)
            if isinstance(ret, ControlFlowFlag) and ret.value == "BREAK":
                break


    def visit_DoWhileStmt(self, node):
        while True:
            ret = self.visit(node.body)
            if isinstance(ret, ControlFlowFlag) and ret.value == "BREAK":
                break
            if not self.visit(node.condition):
                break

    def visit_ForStmt(self, node):
        self.visit(node.setup)
        while self.visit(node.condition):
            ret = self.visit(node.body)
            if isinstance(ret, ControlFlowFlag) and ret.value == "BREAK":
                break
            self.visit(node.increment)

    # expressions
    # these visits return expression value

    def visit_Expression(self, node):
        expr = None
        for child in node.children:
            expr = self.visit(child)
        # return the last comma-delimited child
        return expr

    def get_lvalue_address(self, lvalue_node):
        if isinstance(lvalue_node, Var):
            var_name = lvalue_node.value
            return self.memory.get_value_in_scope(var_name)
        elif isinstance(lvalue_node, UnOp):  # UnOp(*, Ptr)
            ptr_name = lvalue_node.expr.value
            return self.memory[ptr_name].value
        elif isinstance(lvalue_node, FieldAccess):  # FieldAccess
            if lvalue_node.op_type == ARROW:
                var_addr = self.memory[lvalue_node.var.value].value
                return self.memory.get_at_address(var_addr)[lvalue_node.field.value]
            else:
                return self.memory[lvalue_node.var.value][lvalue_node.field.value]
        elif isinstance(lvalue_node, BinOp): # Var a -> Var b
            return self.memory[lvalue_node.left.value][lvalue_node.right.value]
        else:
            raise RuntimeError("Can't get lvalue address")

    def visit_Assignment(self, node):
        # node.left is lvalue - Var/UnOp(*, Var)/FieldAccess
        address = self.get_lvalue_address(node.left)

        # get two operands
        val_self = self.memory.get_at_address(address)
        val_right = self.visit(node.right)

        # combine the operands
        if node.token.type == ADD_ASSIGN:
            val_result = Number(val_self.c_type, val_self+val_right)
        elif node.token.type == SUB_ASSIGN:
            val_result = Number(val_self.c_type, val_self-val_right)
        elif node.token.type == MUL_ASSIGN:
            val_result = Number(val_self.c_type, val_self*val_right)
        elif node.token.type == DIV_ASSIGN:
            val_result = Number(val_self.c_type, val_self/val_right)
        elif node.token.type == ASSIGN:
            val_result = Number(val_self.c_type, val_right)
        else:
            raise RuntimeError("Unknown assignment op: {}".format(node.token.type))

        # perform the assignment
        self.memory.set_at_address(address, val_result)
        return val_result

    def visit_UnOp(self, node):
        if node.prefix:
            if isinstance(node.token, Type):
                # Cast
                # there is a to do for this to be refactored but node.token is an AstNode in this case
                return Number(node.token.c_type, self.visit(node.expr))
            elif node.token.type == AMPERSAND:
                # reference - return variable address
                # node.expr is a Var node
                return Number(CType(type_spec='int'), self.memory.get_value_in_scope(node.expr.value))
            elif node.token.type == ASTERISK:
                # dereference - return variable at the pointed address
                # node.expr is anything but a pointer type
                res = self.visit(node.expr)
                return self.memory.get_at_address(res.value)
            elif node.token.type == INC_OP:
                # node.expr is an LValue
                address = self.get_lvalue_address(node.expr)
                val_self = self.memory.get_at_address(address)
                val_result = Number(val_self.c_type, val_self+Number(CType(type_spec='int'), 1))
                self.memory.set_at_address(address, val_result)
                return val_result
            elif node.token.type == DEC_OP:
                # node.expr is an LValue
                address = self.get_lvalue_address(node.expr)
                val_self = self.memory.get_at_address(address)
                val_result = Number(val_self.c_type, val_self-Number(CType(type_spec='int'), 1))
                self.memory.set_at_address(address, val_result)
                return val_result
            elif node.token.type == MINUS:
                return Number(CType(type_spec='int'), -1) * self.visit(node.expr)
            elif node.token.type == PLUS:
                return self.visit(node.expr)
            elif node.token.type == LOG_NEG:
                res = self.visit(node.expr)
                return res.log_neg()
            else:
                raise RuntimeError("Unknown prefix operator, earlier stages should catch this")
        else:
            if node.token.type == INC_OP:
                # node.expr is an LValue
                address = self.get_lvalue_address(node.expr)
                val_self = self.memory.get_at_address(address)
                val_result = Number(val_self.c_type, val_self+Number(CType(type_spec='int'), 1))
                self.memory.set_at_address(address, val_result)
                return val_self
            elif node.token.type == DEC_OP:
                # node.expr is an LValue
                address = self.get_lvalue_address(node.expr)
                val_self = self.memory.get_at_address(address)
                val_result = Number(val_self.c_type, val_self-Number(CType(type_spec='int'), 1))
                self.memory.set_at_address(address, val_result)
                return val_self
            else:
                raise RuntimeError("Unknown postfix operator, earlier stages should catch this")

    def visit_BinOp(self, node):
        if node.token.type == PLUS:
            return self.visit(node.left) + self.visit(node.right)
        elif node.token.type == MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.token.type == ASTERISK:
            return self.visit(node.left) * self.visit(node.right)
        elif node.token.type == DIV_OP:
            return self.visit(node.left) / self.visit(node.right)
        elif node.token.type == MOD_OP:
            return self.visit(node.left) % self.visit(node.right)
        elif node.token.type == LT_OP:
            return self.visit(node.left) < self.visit(node.right)
        elif node.token.type == GT_OP:
            return self.visit(node.left) > self.visit(node.right)
        elif node.token.type == LE_OP:
            return self.visit(node.left) <= self.visit(node.right)
        elif node.token.type == GE_OP:
            return self.visit(node.left) >= self.visit(node.right)
        elif node.token.type == EQ_OP:
            return self.visit(node.left) == self.visit(node.right)
        elif node.token.type == NE_OP:
            return self.visit(node.left) != self.visit(node.right)
        elif node.token.type == LOG_AND_OP:
            return self.visit(node.left) and self.visit(node.right)
        elif node.token.type == LOG_OR_OP:
            return self.visit(node.left) or self.visit(node.right)
        elif node.token.type == AMPERSAND:
            return self.visit(node.left) & self.visit(node.right)
        elif node.token.type == OR_OP:
            return self.visit(node.left) | self.visit(node.right)
        elif node.token.type == XOR_OP:
            return self.visit(node.left) ^ self.visit(node.right)
        elif node.token.type == ARROW:
            self.memory.get_at_address(self.memory[node.left.value][node.right.value])

    def visit_FieldAccess(self, node):
        if node.op_type == ARROW:
            var_addr = self.memory[node.var.value].value
            addr = self.memory.get_at_address(var_addr)[node.field.value]
        else:
            addr = self.memory[node.var.value][node.field.value]
        return self.memory.get_at_address(addr)

    def visit_Num(self, node):
        if node.token.type == INTEGER_CONST:
            return Number(CType(type_spec='int'), node.value)
        elif node.token.type == CHAR_CONST:
            return Number(CType(type_spec='char'), node.value)
        elif node.token.type == REAL_CONST:
            return Number(CType(type_spec='double'), node.value)
        else:
            raise RuntimeError("Unknown num const, earlier stages should catch this")

    def visit_Var(self, node):
        return self.memory[node.value]

    def visit_String(self, node):
        return node.value

    def visit_NoOp(self, node):
        pass

    def interpret(self, tree):
        """ Interprets a C program from its AST """
        # Visit the AST root (Program) - this will prepare the memory by:
        # loading functions from included libraries, loading local functions and loading global variables
        self.visit(tree)

        # Create a new stack frame and trigger _init that calls main
        self.memory.new_frame('main')
        _init = FunctionCall(
            name='main',
            args=[],
            line=0
        )
        ret_val = self.visit(_init)
        self.memory.del_frame()
        return ret_val.value

    @staticmethod
    def run(program):
        lexer = Lexer(program)
        parser = Parser(lexer)
        tree = parser.parse()
        SemanticAnalyzer.analyze(tree)
        status = Interpreter().interpret(tree)
        print()
        print(MessageColor.OKBLUE + "Process terminated with status {}".format(status) + MessageColor.ENDC)
        return status


