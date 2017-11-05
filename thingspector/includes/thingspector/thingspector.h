#ifndef _THINGSPECTOR_H_
#define _THINGSPECTOR_H_
/*
    Thingspector include header file for tests.
 */
#include <stdlib.h>
#include <stdio.h>

#define __TOSTR(S)   #S
#define _TOSTR(S)    __TOSTR(S)

#define _ASSERT(V, FILE, LINE, FAILMSG, ...) \
    puts("$$ASSERT_BEGIN|" FILE "|" _TOSTR(LINE)); \
    if ((V)) { puts("$$ASSERT_END|OK"); } else { printf("$$ASSERT_END|" FAILMSG "\n", ## __VA_ARGS__); };

#define EXPECT(V, FAILMSG, ...) _ASSERT(V, __FILE__, __LINE__, FAILMSG, ## __VA_ARGS__)

#define EXPECT_STR(W, E)    EXPECT(strcmp(W, E) == 0, "Expected " _TOSTR(W) " to return \"%s\" but was \"%s\"", E, W)
#define EXPECT_ULONG(W, E)  EXPECT(W == E, "Expected " _TOSTR(W) " to return %lu but was %lu", E, W)
#define EXPECT_INT(W, E)    EXPECT(W == E, "Expected " _TOSTR(W) " to return %d but was %d", E, W)
#define EXPECT_LONG(W, E)   EXPECT(W == E, "Expected " _TOSTR(W) " to return %ld but was %ld", E, W)
#define EXPECT_UINT(W, E)   EXPECT(W == E, "Expected " _TOSTR(W) " to return %u but was %u", E, W)

#endif  // _THINGSPECTOR_H_
