/* SPDX-License-Identifier: GPL-2.0-only */
/* ARM EABI PID 1 for the original W103D 32-bit vendor kernel.
 * It only installs an MBR view and boot commands after checking the EPT and
 * both prepared filesystems. DDR, FIP, DTB and filesystem data are untouched.
 */
typedef unsigned int u32;
typedef unsigned char u8;
#define ENV_BYTES 65536u
#define ENV_OFF (180u * 1048576u)
#define BOOT_OFF (730u * 1048576u)
#define ROOT_OFF (1954u * 1048576u)
#define EMMC_SECTORS 60620800u
static u8 env[ENV_BYTES], next[ENV_BYTES], ept[4096], sector[1024];

static long sc(long n, long a, long b, long c, long d, long e) {
    register long r0 __asm__("r0")=a, r1 __asm__("r1")=b;
    register long r2 __asm__("r2")=c, r3 __asm__("r3")=d;
    register long r4 __asm__("r4")=e, r7 __asm__("r7")=n;
    __asm__ volatile("svc 0" : "+r"(r0) : "r"(r1),"r"(r2),"r"(r3),"r"(r4),"r"(r7) : "memory");
    return r0;
}
void *memcpy(void *d,const void *s,unsigned n) { u8 *a=d; const u8 *b=s; while(n--)*a++=*b++; return d; }
void *memset(void *d,int c,unsigned n) { u8 *a=d; while(n--)*a++=(u8)c; return d; }
void __aeabi_memcpy(void *d,const void *s,unsigned n) { memcpy(d,s,n); }
void __aeabi_memclr(void *d,unsigned n) { memset(d,0,n); }
static unsigned len(const char *s) { unsigned n=0;while(s[n])n++;return n; }
static int eq(const void *a,const void *b,unsigned n) { const u8 *x=a,*y=b;while(n--)if(*x++!=*y++)return 0;return 1; }
static void say(const char *s) { sc(4,1,(long)s,len(s),0,0); }
static void stop(const char *s) {
    say("W103D bootstrap: ");say(s);say("\n");
#ifdef TEST_HOST
    sc(1,1,0,0,0,0);
#endif
    for(;;)sc(29,0,0,0,0,0);
}
static u32 le32(const u8 *p) { return p[0]|(p[1]<<8)|(p[2]<<16)|((u32)p[3]<<24); }
static void put32(u8 *p,u32 v) { for(unsigned i=0;i<4;i++){p[i]=v;v>>=8;} }
static u32 crc32(const u8 *p,unsigned n) { u32 c=~0u;while(n--){c^=*p++;for(int i=0;i<8;i++)c=(c>>1)^((0u-(c&1))&0xedb88320u);}return ~c; }
static int openfile(const char *p,int flags) { return sc(5,(long)p,flags|32768,0600,0,0); }
static void at(int fd,u32 off,void *buf,unsigned n,int write) {
    if(sc(19,fd,off,0,0,0)!=(long)off)stop("seek failed");
    unsigned done=0;
    while(done<n) {
        long r=sc(write?4:3,fd,(long)((u8*)buf+done),n-done,0,0);
        if(r<=0)stop(write?"write failed":"read failed");
        done+=(unsigned)r;
    }
}
static void check_partition(const char *name,u32 off,u32 size,int large) {
    u32 count=le32(ept+16);
    for(u32 i=0;i<count;i++) {
        const u8 *p=ept+24+i*40;
        if(eq(p,name,len(name)+1)) {
            if(le32(p+24)!=off || le32(p+28))stop("unexpected EPT offset");
            if(!large && (le32(p+16)!=size || le32(p+20)))stop("unexpected EPT size");
            if(large && (le32(p+16)!=(EMMC_SECTORS-(ROOT_OFF/512u))*512u || le32(p+20)!=6u))
                stop("unexpected EPT root capacity");
            return;
        }
    }
    stop("required EPT partition missing");
}
static const char *changes[]={
    "bootcmd=run w103d_emmc; run start_usb_autoscript; run storeboot",
    "w103d_emmc=for devnum in 1 0 2; do if fatload mmc ${devnum}:1 0x1020000 emmc_autoscript; then autoscr 0x1020000; fi; done",
    "start_usb_autoscript=if usb start; then for usbdev in 0 1 2 3; do if fatload usb ${usbdev} 0x1020000 s905_autoscript; then autoscr 0x1020000; fi; done; fi",
    "upgrade_step=2", "w103d_burn_version=6.18.49-v1"
};
static int replaced(const u8 *p,unsigned n) {
    for(unsigned i=0;i<sizeof(changes)/sizeof(changes[0]);i++) {
        unsigned k=0;while(changes[i][k]!='=')k++;
        if(n>k && p[k]=='=' && eq(p,changes[i],k))return 1;
    }
    return 0;
}
static void provision(int fd) {
    at(fd,36u*1048576u,ept,sizeof(ept),0);
    if(!eq(ept,"MPT\0",4) || le32(ept+16)>32 || !le32(ept+16))stop("invalid EPT header");
    check_partition("env",ENV_OFF,8u*1048576u,0);
    check_partition("system",BOOT_OFF,1024u*1048576u,0);
    check_partition("data",ROOT_OFF,0,1);
    at(fd,BOOT_OFF,sector,512,0);
    if(!eq(sector+71,"W103D_BOOT ",11) || !eq(sector+82,"FAT32   ",8) || sector[510]!=0x55 || sector[511]!=0xaa)
        stop("BOOT filesystem signature mismatch");
    at(fd,ROOT_OFF+1024,sector,1024,0);
    if(sector[56]!=0x53 || sector[57]!=0xef || !eq(sector+120,"W103D_ROOT\0",11))stop("ROOTFS signature mismatch");
    at(fd,ENV_OFF,env,ENV_BYTES,0);
    if(le32(env)!=crc32(env+4,ENV_BYTES-4))stop("invalid U-Boot environment CRC");
    unsigned pos=4,dst=4;
    memset(next,0,sizeof(next));
    while(pos<ENV_BYTES && env[pos]) {
        unsigned end=pos;
        while(end<ENV_BYTES && env[end])end++;
        if(end==ENV_BYTES)stop("unterminated environment");
        if(!replaced(env+pos,end-pos)) {
            if(dst+end-pos+1>=ENV_BYTES)stop("environment overflow");
            memcpy(next+dst,env+pos,end-pos+1);dst+=end-pos+1;
        }
        pos=end+1;
    }
    if(pos>=ENV_BYTES)stop("missing environment terminator");
    for(unsigned i=0;i<sizeof(changes)/sizeof(changes[0]);i++) {
        unsigned n=len(changes[i])+1;
        if(dst+n>=ENV_BYTES)stop("new environment too large");
        memcpy(next+dst,changes[i],n);dst+=n;
    }
    put32(next,crc32(next+4,ENV_BYTES-4));
    /* Build only the 72-byte MBR tail. Leave all preceding bytes and FIP alone. */
    memset(sector,0,72);put32(sector,0x103d6181);
    for(unsigned i=0;i<2;i++) {
        u8 *p=sector+6+i*16;p[1]=p[5]=0xfe;p[2]=p[3]=p[6]=p[7]=0xff;
        p[4]=i?0x83:0x0c;
        put32(p+8,(i?ROOT_OFF:BOOT_OFF)/512u);
        put32(p+12,i?EMMC_SECTORS-ROOT_OFF/512u:2097152u);
    }
    sector[70]=0x55;sector[71]=0xaa;
    at(fd,440,sector,72,1);
    if(sc(118,fd,0,0,0,0))stop("MBR sync failed");
    u8 check[72];at(fd,440,check,72,0);
    if(!eq(check,sector,72))stop("MBR readback mismatch");
    at(fd,ENV_OFF,next,ENV_BYTES,1);
    if(sc(118,fd,0,0,0,0))stop("environment sync failed");
    at(fd,ENV_OFF,env,ENV_BYTES,0);
    if(!eq(env,next,ENV_BYTES))stop("environment readback mismatch");
    say("W103D bootstrap: boot entry installed and verified; starting Armbian\n");
}
static unsigned decimal(const char *s) { unsigned v=0;while(*s>='0'&&*s<='9')v=v*10+*s++-'0';return v; }
void entry(unsigned *stack) {
#ifdef TEST_HOST
    if(stack[0]!=2)stop("test requires an image path");
    int fd=openfile((char*)stack[2],2);
    if(fd<0)stop("cannot open test image");
    provision(fd);sc(6,fd,0,0,0,0);sc(1,0,0,0,0,0);
#else
    (void)stack;
    sc(39,(long)"/dev",0755,0,0,0);sc(39,(long)"/proc",0755,0,0,0);sc(39,(long)"/sys",0755,0,0,0);
    sc(21,(long)"proc",(long)"/proc",(long)"proc",0,0);
    sc(21,(long)"sysfs",(long)"/sys",(long)"sysfs",0,0);
    sc(21,(long)"devtmpfs",(long)"/dev",(long)"devtmpfs",0,0);
    int fd=-1;
    /* Wait for asynchronous MMC probing. Require eMMC boot0 and exact size. */
    for(unsigned attempt=0;attempt<30 && fd<0;attempt++) {
        for(char i='0';i<='3';i++) {
            char sizepath[]="/sys/class/block/mmcblk0/size";
            char bootpath[]="/sys/class/block/mmcblk0boot0/size";
            char devpath[]="/dev/mmcblk0";
            sizepath[23]=bootpath[23]=i;devpath[11]=i;
            int s=openfile(bootpath,0);if(s<0)continue;sc(6,s,0,0,0,0);
            s=openfile(sizepath,0);if(s<0)continue;
            char text[32]={0};long n=sc(3,s,(long)text,31,0,0);sc(6,s,0,0,0,0);
            if(n<=0 || decimal(text)!=EMMC_SECTORS)continue;
            char numberpath[]="/sys/class/block/mmcblk0/dev";
            numberpath[23]=i;
            s=openfile(numberpath,0);if(s<0)continue;
            memset(text,0,sizeof(text));n=sc(3,s,(long)text,31,0,0);sc(6,s,0,0,0,0);
            unsigned colon=0;while(colon<31 && text[colon] && text[colon]!=':')colon++;
            if(n<=0 || colon==31 || text[colon]!=':')continue;
            unsigned major=decimal(text),minor=decimal(text+colon+1);
            sc(14,(long)devpath,060600,(minor&255)|(major<<8)|((minor&~255u)<<12),0,0);
            fd=openfile(devpath,2);
            if(fd>=0)break;
        }
        if(fd<0) { long ts[2]={1,0};sc(162,(long)ts,0,0,0,0); }
    }
    if(fd<0)stop("expected eMMC not found; no writes performed");
    provision(fd);sc(6,fd,0,0,0,0);sc(36,0,0,0,0,0);
    sc(88,0xfee1dead,672274793,0x1234567,0,0);
#endif
    stop("reboot returned");
}
__asm__(".global _start\n_start:\nmov r0, sp\nbl entry\nb .\n");
