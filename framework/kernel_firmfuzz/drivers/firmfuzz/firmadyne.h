#ifndef INCLUDE_FIRMADYNE_H
#define INCLUDE_FIRMADYNE_H
/* Network related operations; e.g. bind, accept, etc */
#define LEVEL_NETWORK (1 << 0)
/* System operations; e.g. reboot, mount, ioctl, execve, etc */
#define LEVEL_SYSTEM  (1 << 1)
/* Filesystem write operations; e.g. unlink, mknod, etc */
#define LEVEL_FS_W    (1 << 2)
/* Filesystem read operations; e.g. open, close, etc */
#define LEVEL_FS_R    (1 << 3)
/* Process execution operations; e.g. mmap, fork, etc */
#define LEVEL_EXEC    (1 << 4)


extern short devfs;
extern short execute;
extern short reboot;
extern short procfs;
extern short syscall;

#define MODULE_NAME "firmadyne"

#endif
