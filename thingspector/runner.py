import os
from thingspector import builder
import pycparser as cp
from thingspector import templates as tpl
from thingspector.utils import log, exec2str, exec4iter
import subprocess


def show_attrs(obj):
    print("object %s" % obj)
    for d in dir(obj):
        print("* %s=%s" % (d, getattr(obj, d)))


_compilers = None
_path = os.path.dirname(__file__)


class Tester:

    def __init__(self, test_desc):
        self.desc = test_desc
        self.modpath = None
        # Test cases as found in the module under test
        self.mod_cases = []
        # Test cases as found in the test file
        self.cases = None
        self.builder = builder.Build(self.desc.testbin, self.desc.p.workdir)

    def __populate_builder(self):
        self.builder.add_src(self.modpath, self.desc.testsrc, self.desc.runnersrc)
        self.builder.add_inc_path(*self.desc.incdirs)


    # ===============================================================================================================
    #  Section related to updating the test
    # ===============================================================================================================

    def __find_module(self):
        if self.modpath is not None:
            return

        for srcdir in self.desc.srcdirs:
            mpc = srcdir + self.desc.target
            if mpc.is_file():
                self.modpath = mpc
                return
        raise RuntimeError("Could not find module " + self.desc.target)

    def __index_mod_file(self):
        """
            Finds test cases by analyzing the modules C file
        """
        ast = self.builder.parse(self.modpath)

        predeclares = []

        # find all functions
        for a in ast.ext:
            # print(a.show())
            if isinstance(a, cp.c_ast.Decl):
                if isinstance(a.type, cp.c_ast.FuncDecl):
                    predeclares.append(a.name)

            if isinstance(a, cp.c_ast.FuncDef):
                decl = a.decl

                is_predeclared = decl.name in predeclares
                is_static = 'static' in decl.storage
                is_inline = 'inline' in decl.funcspec

                if is_static and is_inline and decl.name in self.desc.static_inline:
                    pass
                elif is_static or is_inline or not is_predeclared:
                    continue

                self.mod_cases.append(decl)

    def __create_test_file(self):
        """
            One time action per module to generate the test-case file.
        """
        with open(self.desc.testsrc.abs_str(), "w") as stream:

            includes = (tpl.C_TEST_HEADER_INCLUDE % h for h in self.desc.headers)

            t_params = {
                "module": self.desc.name,
                "includes": "\n".join(includes)
            }

            stream.write(tpl.C_TEST_HEADER % t_params)

            for testfunc in self.mod_cases:
                t_params = {
                    "case": testfunc.name,
                    "signature": "TODO"
                }

                stream.write(tpl.C_TEST_CASE % t_params)

    def __append_test_file(self, new_cases):
        """
            One time action per module to generate the test-case file.
        """
        with open(self.desc.testsrc.abs_str(), "a") as stream:
            for testfunc in new_cases:
                t_params = {
                    "case": testfunc.name,
                    "signature": "TODO"
                }
                stream.write(tpl.C_TEST_CASE % t_params)

    def __index_test_cases(self):
        """
            this looks at the test file to find case_<func> functions
        """

        found_cases = []


        ast = self.builder.parse(self.desc.testsrc)

        has_setup = False
        has_teardown = False

        for a in ast.ext:
            # print(a.show())

            if isinstance(a, cp.c_ast.FuncDef):
                decl = a.decl

                is_static = 'static' in decl.storage
                is_inline = 'inline' in decl.funcspec

                if is_static or is_inline:
                    continue

                if decl.name.startswith("case_"):
                    found_cases.append(decl.name[len("case_"):])
                elif decl.name == "test_setup":
                    has_setup = True
                elif decl.name == "test_teardown":
                    has_teardown = True

        if not has_setup or not has_teardown:
            raise RuntimeError("Test file invalid, no test_setup() and/or test_teardown()")

        self.cases = found_cases

    def __create_or_update_test_file(self):
        """
            Checks whether or not a test file exists:
            - If not, it will create one
            - If so, it will index it, and create test functions if they do not exist
            - Returns True if the test runner has to be regenerated
        """

        if self.desc.testsrc.is_file():

            self.__index_test_cases()
            new_cases = [decl for decl in self.mod_cases if decl.name not in self.cases]

            # found new functions to add
            if len(new_cases) > 0:
                self.__append_test_file(new_cases)
                self.cases += [decl.name for decl in new_cases]
                return True
            return False
        else:
            self.__create_test_file()
            # in this case we know the generated cases equal the ones from the module
            self.cases =\
                [decl.name for decl in self.mod_cases]
            return True

    def __update_runner(self):
        """
            Updates the test runner (actually just creates it)
        """
        if self.desc.runnersrc.is_file() and self.desc.runnersrc.is_newer(self.desc.testsrc):
            return

        if self.cases is None:
            self.__index_test_cases();

        with open(self.desc.runnersrc.abs_str(), "w") as stream:

            casefuncstr = []
            casestmtsstr = []

            for idx, case in zip(range(len(self.cases)), self.cases):
                casefuncstr.append(tpl.C_TEST_RUNNER_CASEFUNCS % case)
                t_params = {
                    "idx": idx,
                    "casename": case
                }
                casestmtsstr.append(tpl.C_TEST_RUNNER_CASESTMTS % t_params)

            t_params = {
                "casesn": len(self.cases),
                "casefuncs": "\n".join(casefuncstr),
                "casestmts": "\n".join(casestmtsstr)
            }

            stream.write(tpl.C_TEST_RUNNER % t_params)


    def update(self):
        # check mut dir
        self.__find_module()
        # create the builder definition
        self.__populate_builder()
        # parse C file
        self.__index_mod_file()
        # generate/update test file
        self.__create_or_update_test_file()

    # ===============================================================================================================
    #  Section related to running the test
    # ===============================================================================================================
    def __compile_module(self):


        if self.desc.testbin.is_file() and self.desc.testbin.is_newer(self.desc.testsrc, self.modpath,
           self.desc.runnersrc):
            log.trace("No need to recompile runner")
            # return

        self.builder.compile_all()


    def __execute_test(self, *params):
        assert_file = None
        assert_line = -1
        case = "<unknown>"
        assert_count = 0
        assert_failed = 0
        fatal = False
        try:
            for line in exec4iter(self.desc.testbin.abs_str(), *params):
                line = line.strip()

                if len(line) == 0:
                    continue

                # Console output
                if not line.startswith("$$"):
                    log.warning("   Console output: %(output)s", output=line)
                    continue

                p = line.split("|")
                cmd = p[0][2:]
                par = p[1:]

                if cmd == "CASE" and len(par) == 1:
                    case = par[0]
                    log.verbose(" Case %(case)s", case=case)
                elif cmd == "ASSERT_BEGIN" and len(par) == 2:
                    assert_file = par[0]
                    assert_line = int(par[1])
                    assert_count += 1
                elif cmd == "ASSERT_END" and len(par) >= 1:
                    if par[0] != "OK":
                        log.warning("  Assertion at %(file)s:%(line)d failed: %(cause)s",
                                    file=assert_file, line=assert_line, cause="|".join(par))
                        assert_failed += 1
                    else:
                        log.trace("  Assertion at %(file)s:%(line)d success",
                                  file=assert_file, line=assert_line)

                    assert_file = None
                else:
                    log.severe("  Unexpected command sequence: %(seq)s", seq=line)

        except subprocess.CalledProcessError as e:
            fatal = True
            if assert_file is not None:
                log.severe("  Assertion at %(file)s:%(line)d exited with code 0x%(code)x",
                                 file=assert_file, line=assert_line, code=e.returncode)
            else:
                log.severe("  Test case %(case)s exited with code 0x%(code)x",
                                 case=case,  code=e.returncode)

        log.info("  Completed %(case)s assertions=%(assert_count)d failed=%(assert_failed)d ",
                       case=case, assert_count=assert_count, assert_failed=assert_failed)

        return assert_count, assert_failed, fatal

    def __run_test(self):
        """
            Run a test script.
        """
        capture, rv = exec2str(self.desc.testbin.abs_str())
        capture = capture.split()
        if len(capture) != 1:
            raise RuntimeError("Failed to run test, unexpected reply")
        no_of_tests = int(capture[0])

        log.verbose("Starting test %(name)s", name=self.desc.name)

        assert_count = 0
        assert_failed = 0
        cases_fatal = 0

        for i in range(no_of_tests):
            a_c, a_f, fatal = self.__execute_test(str(i))
            assert_count += a_c
            assert_failed += a_f
            if fatal:
                cases_fatal += 1

        log.info(" Test %(name)s completed, cases=%(casen)d (fatal=%(fatal)d), " +
                 "Assertions total=%(assert_count)d, of which %(assert_failed)d failed",
                 name=self.desc.name, casen=no_of_tests, fatal=cases_fatal,
                 assert_count=assert_count, assert_failed=assert_failed)

    def test(self):
        """
            Run the tests on this object.
        """
        # Should be optimized away
        self.__find_module()

        # populate the builder
        self.__populate_builder()

        self.__update_runner()

        # Compile it
        self.__compile_module()
        # Run the tests
        self.__run_test()

class Mocker:
    """
        Generates mock object files.
    """
    def __init__(self, test_desc):
        self.desc = test_desc

    def update(self):
        self.__check_dirs()


def check_dirs(config):
    if not config.testdir.is_dir():
        config.testdir.mkdirs()

    if not config.workdir.is_dir():
        config.workdir.mkdirs()

    if not config.mockdir.is_dir():
        config.mockdir.mkdirs()


def update_test(test):
    check_dirs(test.p)
    tester = Tester(test)
    tester.update()

def update_mock(mock):
    check_dirs(mock.p)
    mocker = Mocker(mock)
    mocker.update()

def execute_test(test):
    check_dirs(test.p)
    tester = Tester(test)
    tester.test()


