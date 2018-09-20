#include <cstdio>

// gcc -o brute.so -shared -fPIC ld_preload_call.c -ldl
// LD_PRELOAD=./brute.so ./crackme 

// Note: System V AMD64 ABI specifies the following argument order:
// RDI, RSI, RDX, RCX, R8, R9 - remaining arguments on stack.

typedef unsigned int (* func)(unsigned int);

__attribute__((constructor)) void init(){
    unsigned int i;
	func f = (func)0x400c21;
	for(unsigned int i=0; i<(1<<31); i++){
		if(f(i) == 1){
			printf("%u\n", i);
		}
	}
}
