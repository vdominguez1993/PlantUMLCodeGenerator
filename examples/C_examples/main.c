#include "stdio.h"
#include "example.h"

int main(void)
{

    example_initialize();
    while(1){
        example_task();
    }

    return 0;
}
