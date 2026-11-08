#include <mach/mach_time.h>
#include <time.h>
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
static uint64_t ns(uint64_t ticks,mach_timebase_info_data_t b) {
    return (uint64_t)(((__uint128_t)ticks*b.numer)/b.denom);
}
int main(void) {
    mach_timebase_info_data_t b;
    if(mach_timebase_info(&b)!=0 || !b.numer || !b.denom) return 1;
    printf("continuous_before_ns,absolute_ns,raw_ns,uptime_raw_ns,continuous_after_ns,numer,denom\n");
    for(int i=0;i<20;i++) {
        uint64_t c0=ns(mach_continuous_time(),b);
        uint64_t a=ns(mach_absolute_time(),b);
        uint64_t r=clock_gettime_nsec_np(CLOCK_MONOTONIC_RAW);
        uint64_t u=clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
        uint64_t c1=ns(mach_continuous_time(),b);
        if(c1<c0 || r<c0 || r>c1 || a>c1 || u>c1) return 2;
        printf("%llu,%llu,%llu,%llu,%llu,%u,%u\n",c0,a,r,u,c1,b.numer,b.denom);
        usleep(10000);
    }
    return 0;
}
