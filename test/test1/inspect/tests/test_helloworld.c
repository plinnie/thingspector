/*
    Module Under Test test-file for module helloworld
*/
#include "thingspector.h"
#include "helloworld.h"
#include <stdbool.h>

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



/*
    Test stub for function helloWorld.

    Function signature: TODO
*/
void case_helloWorld()
{
    ASSERT_EQ_STR(helloWorld(), "Hello world")
}



void case_fault()
{
    // Intentional fault
    *(int*)0 = 0;
}

/*
    Test stub for function helloWorldAgain.

    Function signature: TODO
*/
void case_helloWorldAgain()
{
    ASSERT_EQ_STR(helloWorldAgain(), "Hello world")
}
