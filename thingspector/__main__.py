from thingspector.suiteconfig import SuiteConfig
from thingspector import testrunner as tr
import sys

def print_help():
    print("MUT - Module Under Test")
    print("Usage: ")
    print(" mut u [<module>[ <module> <etc..>]] - Update all or some modules")

if __name__ == "__main__":


    if len(sys.argv) == 1:
        print_help();
        sys.exit(0)

    if sys.argv[1] == 'u':
        mf = SuiteConfig()

        for test in mf.tests.values():
            tr.update_test(test)

    if sys.argv[1] == 't':
        mf = SuiteConfig()

        for test in mf.tests.values():
            tr.execute_test(test)
