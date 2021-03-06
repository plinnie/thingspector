from thingspector.thingconfig import ThingConfig
from thingspector import runner as tr
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

    try:
        if sys.argv[1] == 'u':
            mf = ThingConfig()

            for mock in mf.mocks.values():
                tr.update_mock(mock)

            for test in mf.tests.values():
                tr.update_test(test)

        elif sys.argv[1] == 't':
            mf = ThingConfig()

            for test in mf.tests.values():

                tr.execute_test(test)
    except RuntimeError as e:
        print("Error: %s" % e)
        sys.exit(1)
