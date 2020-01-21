import unittest

from contextlib import redirect_stdout
import io

from pecan import program

class PralineTest(unittest.TestCase):
    def run_file(self, filename, expected_output):
        f = io.StringIO()
        with redirect_stdout(f):
            prog = program.load(filename, quiet=True)
            self.assertTrue(prog.evaluate().result.succeeded())
        self.assertEqual(f.getvalue().strip(), expected_output.strip())

    def test_praline_simple(self):
        self.run_file('examples/test_praline_simple.pn', '1\n16\n')

    def test_praline_list(self):
        self.run_file('examples/test_praline_list.pn', '[1,2,3,4]\n')

    def test_praline_match(self):
        self.run_file('examples/test_praline_match.pn', '4\n[1,4,9,16]\n-49\n')

    def test_praline_compose(self):
        self.run_file('examples/test_praline_compose.pn', '1\n0\n2\n')

    def test_praline_builtins(self):
        self.run_file('examples/test_praline_builtins.pn', '7\n')

    def test_praline_pecan_interop(self):
        self.run_file('examples/test_praline_pecan_interop.pn', 'false\ntrue\nfalse\n01101001100101101001011001101001100101100110100101101001100101101001011001101001011010011001011001101\n')

    def test_praline_do(self):
        self.run_file('examples/test_praline_do.pn', '1\n2\n')

    def test_praline_split(self):
        self.run_file('examples/test_praline_split.pn', '''
([1,2,3,4],[5,6,7,8,9,10])
[1,2,3,4]
[1,2,3,4,5,6,7,8,9,10]
''')

    def test_praline_accepting_word(self):
        self.run_file('examples/test_praline_accepting_word.pn', '''
[(x,([],[false]))]
[(x,([false,false,true,true,true,false,true],[false]))]
''')

    def test_praline_examples(self):
        self.run_file('examples/test_praline_examples.pn', '''
[(x,-2)]
''')

    def test_praline_operators(self):
        self.run_file('examples/test_praline_operators.pn', '''
false
false
false
true
false
true
true
true
[true,false]
[true,true]
''')

    def test_praline_graphing(self):
        self.run_file('examples/test_praline_graphing.pn', '''
[(-10,-20),(-9,-18),(-8,-16),(-7,-14),(-6,-12),(-5,-10),(-4,-8),(-3,-6),(-2,-4),(-1,-2),(0,0),(1,2),(2,4),(3,6),(4,8),(5,10),(6,12),(7,14),(8,16),(9,18),(10,20)]
''')

