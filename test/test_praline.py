import unittest

from contextlib import redirect_stdout
import io

from pecan import program

class PralineTest(unittest.TestCase):
    def run_file(self, filename, expected_output, run_quiet=True):
        f = io.StringIO()
        with redirect_stdout(f):
            prog = program.load(filename, quiet=run_quiet)
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
        self.run_file('examples/test_praline_pecan_interop.pn', 'False\nTrue\nFalse\n01101001100101101001011001101001100101100110100101101001100101101001011001101001011010011001011001101\n')

    def test_praline_do(self):
        self.run_file('examples/test_praline_do.pn', '1\n2\n')

    def test_praline_emit(self):
        self.run_file('examples/test_praline_emit.pn', '[INFO] Checking if self_equals_tautology is true.\nself_equals_tautology is true.\n', run_quiet=False)


