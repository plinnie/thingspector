from thingspector.thingconfig import ThingConfig
from thingspector import testrunner as tr
import sys


def print_help():
    print("Thingspector - Embedded C test framework")
    print("Usage: ")
    print(" mut u [<module>[ <module> <etc..>]] - Update all or some module test sources")
    print(" mut t [<module>[ <module> <etc..>]] - Compile (if needed) and test one or more modules")


if __name__ == "__main__":

    if len(sys.argv) == 1:
        print_help();
        sys.exit(0)

    if sys.argv[1] == 'u':
        mf = ThingConfig()

        for test in mf.tests.values():
            tr.update_test(test)

    elif sys.argv[1] == 't':
        mf = ThingConfig()

        for test in mf.tests.values():
            tr.execute_test(test)
