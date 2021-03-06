import unittest
from interpreter.lexical_analysis.lexer import Lexer
from interpreter.syntax_analysis.parser import Parser
from interpreter.syntax_analysis.parser import SyntaxError
from interpreter.syntax_analysis.tree import *

class ParserTestCase(unittest.TestCase):

    def make_parser(self, text):
        lexer = Lexer(text)
        parser = Parser(lexer)
        return parser

    def test_libraries(self):
        parser = self.make_parser("""
            #include <stdio.h>
            #include <stdlib.h>
            #include <math.h>
        """)
        parser.parse()

    def test_functions(self):
        parser = self.make_parser("""
           int main(){
           
           }
           
           int test(int a, int b){
                
           }
            
        """)
        parser.parse()

    def test_declarations(self):
        parser = self.make_parser("""
            int a, b = 2;
            int main(){
                int a, b = 3, c = 1 - b ++;
                a = a ^ b | b - 1 * 5 / (double)c - a++;
            }
        """)
        parser.parse()

    def test_function_call(self):
        parser = self.make_parser("""
            int a, b = 2;
            int main(){
                int a = printf("%d %d", b, c);
            }
        """)
        parser.parse()

    def test_if_stmt(self):
        parser = self.make_parser("""
            int a, b = 2;
            int main(){
                if(a = b)
                    b = 1;
                if(c == d | v)
                    a = 1;
                else
                    b = 1;
                    
                if(a == 1){
                    b = 1;
                    c = 1;
                }else{
                    c = 2;
                    e = 1;
                }  
                
                if(a == 1)
                    b = 1;
                else if (b == 1)
                    c = 5;  
                    
            }
        """)
        parser.parse()

    def test_for_stmt(self):
        parser = self.make_parser("""
            int a, b = 2;
            int main(){
                for(i = 0; i < n; i ++){
                    a = 1;
                }
                
                for(i = 1, b = 2; i > 1; i --){
                    b - 1;
                }
                
                for( i = 1, b = 2, c = 1; i < 1; i --, b++)
                    for(j = 0; j < 5; j ++)
                        for(;;){
                        
                        }

            }
        """)
        parser.parse()

    def test_while_do_stmt(self):
        parser = self.make_parser("""
            int a, b = 2;
            int main(){
                while(i < 1){
                    b = 1;
                }
                
                while(a > b)
                    while(b == 1){
                        a = 1;
                    }
                    
                do{
                    a = 1 << 2 << 3;
                }while(a < 5);

            }
        """)
        parser.parse()

    def test_pointers(self):
        parser = self.make_parser("""
                    int main(){
                        int* a;
                        int b;
                        a = &b;
                        int* c = a;
                        *a = b;
                    }
                """)
        parser.parse()

    def test_pointers_error(self):
        with self.assertRaises(SyntaxError):
            parser = self.make_parser("""
                        int main(){
                            int* a;
                            int b;
                            a = &&b;
                            int* c = a;
                        }
                    """)
            parser.parse()

    def test_pointers_sem_err(self):
        parser = self.make_parser("""
                           int main(){
                               int* a;
                               int b = a;
                               a += b;
                               int* c = a;
                               c += c;
                           }
                       """)
        parser.parse()

    def test_more_pointers(self):
        parser = self.make_parser("""
                    int main() {
                        int* a;
                        int b;
                        *a = b;
                        int d = *a;
                        *a++;
                        (*a)++;
                        --a;
                        --(*a);
                    }
                """)
        parser.parse()



    def test_nested_control_flow(self):
        parser = self.make_parser("""
                    int main() {
                        int i, j = 0;
                        for(i=0; i<5; i++) {
                            int k = 0;
                            while (k < 5) {
                                j++;
                                k++;
                                if (k == i) {
                                    break;
                                }
                            }
                            j += i;
                            if (j == 6) {
                              break;
                            }
                        }
                    }
                """)
        parser.parse()

    def test_switch(self):
        parser = self.make_parser("""
                    int main() {
                        int i = 4;
                        switch (i+1) {
                            case 1:
                                 printf("1!");
                                 break;
                            case 2+2:
                                 printf("4!");
                            case 5:
                                 printf("Fallthrough!");
                                 break;
                            default:
                                 printf("Default");
                        }
                        return 0;
                    }
                """)
        parser.parse()

    def test_types(self):
        parser = self.make_parser("""
                    int main() {
                        unsigned short int i = 4;
                        long double f = 5;
                        int long long x = 9;
                    }
                """)
        parser.parse()

    def test_types_fail(self):
        with self.assertRaises(SyntaxError):
            parser = self.make_parser("""
                        int main() {
                        unsigned short int i = 4;
                        long double f = 5;
                        short unsigned int long long x = 9;
                    }
                    """)
            parser.parse()

    def test_types_fail_2(self):
        with self.assertRaises(SyntaxError):
            parser = self.make_parser("""
                        int main() {
                        unsigned i = 4;
                    }
                    """)
            parser.parse()

    def test_struct(self):
        parser = self.make_parser("""
                    struct s {
                        int a, b;
                        char c;
                    };
                    
                    int main() {
                        int x = 2;
                        int y;
                        struct s z;
                        z.a = 3;
                        struct s * ptr;
                        ptr = &z;
                        ptr->b = 4;
                        printf("%d %d %d\n", x, ptr->a, z.b);
                        return 0;
                    }
                """)
        parser.parse()


if __name__ == '__main__':
    unittest.main()
