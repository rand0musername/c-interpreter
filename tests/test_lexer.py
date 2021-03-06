import unittest

from interpreter.lexical_analysis.token_type import *
from interpreter.lexical_analysis.lexer import Lexer, LexicalError

class LexerTestCase(unittest.TestCase):

    def check_list(self, *args, lexer=None):
        for token_type in args:
            token = lexer.get_next_token
            self.assertEqual(token.type, token_type)
        token = lexer.get_next_token
        self.assertEqual(token.type, EOF)

    def test_arithmetic_ops(self):
        lexer = Lexer('+ - / * %')
        self.check_list(
            PLUS, MINUS, DIV_OP, ASTERISK, MOD_OP,
            lexer=lexer
        )

    def test_bit_ops(self):
        lexer = Lexer('^ | & << >>')
        self.check_list(
            XOR_OP, OR_OP, AMPERSAND, LEFT_OP, RIGHT_OP,
            lexer=lexer
        )

    def test_compare_ops(self):
        lexer = Lexer('< > <= >= == !=')
        self.check_list(
            LT_OP, GT_OP, LE_OP, GE_OP, EQ_OP, NE_OP,
            lexer=lexer
        )

    def test_logical_ops(self):
        lexer = Lexer('&& || !')
        self.check_list(
            LOG_AND_OP, LOG_OR_OP, LOG_NEG,
            lexer=lexer
        )

    def test_inc_dec(self):
        lexer = Lexer('++ --')
        self.check_list(
            INC_OP, DEC_OP,
            lexer=lexer
        )

    def test_assign_ops(self):
        lexer = Lexer('= += -= *= /= >>= <<= &= |= ^=')
        self.check_list(
            ASSIGN, ADD_ASSIGN, SUB_ASSIGN, MUL_ASSIGN, DIV_ASSIGN,
            RIGHT_ASSIGN, LEFT_ASSIGN, AND_ASSIGN, OR_ASSIGN, XOR_ASSIGN,
            lexer=lexer
        )

    def test_types(self):
        lexer = Lexer('int float double')
        self.check_list(
            INT, FLOAT, DOUBLE,
            lexer=lexer
        )

    def test_ids(self):
        lexer = Lexer('a a5a a1a newaaa')
        self.check_list(
            ID, ID, ID, ID,
            lexer=lexer
        )

    def test_reserved_words(self):
        lexer = Lexer('if else for while')
        self.check_list(
            IF, ELSE, FOR, WHILE,
            lexer=lexer
        )

    def test_numbers(self):
        lexer = Lexer('123 12.2 0.23 123')
        self.check_list(
            INTEGER_CONST, REAL_CONST, REAL_CONST, INTEGER_CONST,
            lexer=lexer
        )

    def test_strings(self):
        lexer = Lexer('"ovo je novi string"')
        self.check_list(
            STRING,
            lexer=lexer
        )

    def test_pointers(self):
        lexer = Lexer('char* a;')
        self.check_list(
            CHAR, ASTERISK, ID, SEMICOLON,
            lexer=lexer
        )

    def test_reference(self):
        lexer = Lexer('char* a = &b;')
        self.check_list(
            CHAR, ASTERISK, ID, ASSIGN, AMPERSAND, ID, SEMICOLON,
            lexer=lexer
        )

    def test_control_flow(self):
        lexer = Lexer('break continue return')
        self.check_list(
            BREAK, CONTINUE, RETURN,
            lexer=lexer
        )

    def test_switch(self):
        lexer = Lexer('switch ( a ) { case 1 : break; default: break; }')
        self.check_list(
            SWITCH, LPAREN, ID, RPAREN, LBRACKET, CASE, INTEGER_CONST, COLON,
            BREAK, SEMICOLON, DEFAULT, COLON, BREAK, SEMICOLON, RBRACKET,
            lexer=lexer
        )

    def test_types(self):
        lexer = Lexer('short long unsigned signed int char float double')
        self.check_list(
            SHORT, LONG, UNSIGNED, SIGNED, INT, CHAR, FLOAT, DOUBLE,
            lexer=lexer
        )

    def test_struct(self):
        lexer = Lexer('struct s { } ; a->b')
        self.check_list(
            STRUCT, ID, LBRACKET, RBRACKET, SEMICOLON, ID, ARROW, ID,
            lexer=lexer
        )

    
if __name__ == '__main__':
    unittest.main()


