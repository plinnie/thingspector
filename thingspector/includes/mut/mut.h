#ifndef _MUT_H_
#define _MUT_H_

#define __TOSTR(S)   #S
#define _TOSTR(S)    __TOSTR(S)

#define _ASSERT(V, FILE, LINE) \
    puts("$$ASSERT_BEGIN:" FILE ":" _TOSTR(LINE)); \
    if ((V)) { puts("$$ASSERT_END:OK"); } else { puts("$$ASSERT_END:FAILED"); };

#define ASSERT(V) _ASSERT(V, __FILE__, __LINE__)

#define ASSERT_EQ_STR(A, B) ASSERT(strcmp(A, B) == 0)

#endif
