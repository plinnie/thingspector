# This file contains all templates, to have them not inside the module code. Kind of clutters things

# =====================================================================================================================
#  Test file templates
# =====================================================================================================================

# Test C file, header.
#
# Parameters:
#  * module  : Module name
#  * includes: formatter string of include statements
#
C_TEST_HEADER = """\
/*
    Thingspector test-file for module %(module)s
*/
#include "thingspector.h"
%(includes)s

/*
  This function will be invoked before each test is run. 
*/ 
void test_setup()
{
}

/*
  This function will be invoked after each test has run.
*/ 
void test_teardown()
{
}

"""
# ---------------------------------------------------------------------------------------------------------------------

# Test C file include statement
#
#   Parameter (positional):
#    * header file
C_TEST_HEADER_INCLUDE = "#include \"%s\""

# ---------------------------------------------------------------------------------------------------------------------

# Test C file, case:
#
# Parameters:
#  * case     : Case name
#  * signature: Function signature
#
C_TEST_CASE = """
/*
    Test stub for function %(case)s.
    
    Function signature: %(signature)s
*/
void case_%(case)s()
{
    /* Your test code here. Remove EXPECT(false) below. */
    EXPECT(false, "Case not implemented yet")
}
"""

# =====================================================================================================================
#  Test file runner templates
# =====================================================================================================================

# Test runner C file:
#
# Parameters:
#  * casen    : Number of cases
#  * casefuncs: formatted string of predefined case-function signatures (see below)
#  * casestmts: formatted string of case statements (see below)
#
C_TEST_RUNNER = """\
/*
    Main module for test runner. 
    
    Do not modify this file! It is automatically generated and will be overwritten on changes.
*/
#include <stdio.h>

void test_setup();
void test_teardown();
%(casefuncs)s

int main( int argc, const char* argv[] )
{
    if (argc == 1) {
        puts("%(casesn)d");
    } else {
        test_setup();
        switch (atoi(argv[1]))
        {
%(casestmts)s
        }
        test_teardown();
    }
    return 0;
}
"""

# ---------------------------------------------------------------------------------------------------------------------

# Test C test runner function pre-declaration
#
#   Parameter (positional):
#    * test case function (i.e. void case_<function>(); ), only the <function> part.
C_TEST_RUNNER_CASEFUNCS = "void case_%s();"

# Test runner C case statement:
#
# Parameters:
#  * idx      : Case index
#  * casename : Case name
#
C_TEST_RUNNER_CASESTMTS = """\
        case %(idx)d:
            puts("$$CASE|%(casename)s");
            fflush(stdout);
            case_%(casename)s();
            break;"""

