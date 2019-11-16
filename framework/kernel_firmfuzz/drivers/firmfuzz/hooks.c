#include <linux/binfmts.h>
#include <linux/capability.h>
#include <linux/fs.h>
#include <linux/kmod.h>
#include <linux/kprobes.h>
#include <linux/mman.h>
#include <linux/if_vlan.h>
#include <linux/inetdevice.h>
#include <linux/net.h>
#include <linux/netlink.h>
#include <linux/reboot.h>
#include <linux/security.h>
#include <linux/socket.h>
#include <net/inet_sock.h>

#include "firmadyne.h"
#include "hooks.h"
#include "hooks-private.h"

#define SYSCALL_HOOKS \
	/* Hook network binds */ \
	HOOK("inet_bind", bind_hook, bind_probe) \
	/* Hook accepts */ \
	HOOK("inet_accept", accept_hook, accept_probe) \
	/* Hook VLAN creation */ \
	HOOK("register_vlan_dev", vlan_hook, vlan_probe) \
	/* Hook assignments of IP addresses to network interfaces */ \
	HOOK("__inet_insert_ifa", inet_hook, inet_probe) \
	/* Hook adding of interfaces to bridges */ \
	HOOK("br_add_if", br_hook, br_probe) \
	/* Hook socket calls */ \
	HOOK("sys_socket", socket_hook, socket_probe) \
	/* Hook changes in socket options */ \
	HOOK("sys_setsockopt", setsockopt_hook, setsockopt_probe) \
\
	/* Hook mounting of file systems */ \
	HOOK("do_mount", mount_hook, mount_probe) \
	/* Hook creation of device nodes */ \
	HOOK("vfs_mknod", mknod_hook, mknod_probe) \
	/* Hook deletion of files */ \
	HOOK("vfs_unlink", unlink_hook, unlink_probe) \
	/* Hook IOCTL's on files */ \
	HOOK("do_vfs_ioctl", ioctl_hook, ioctl_probe) \
	/* Hook system reboot */ \
	HOOK("sys_reboot", reboot_hook, reboot_probe) \
\
	/* Hook opening of file descriptors */ \
	HOOK("do_sys_open", open_hook, open_probe) \
	HOOK_RET("do_sys_open", NULL, open_ret_hook, open_ret_probe)  \
	/* Hook closing of file descriptors */ \
	HOOK("sys_close", close_hook, close_probe) \
\
	/* Hook execution of programs */ \
	HOOK("do_execve", execve_hook, execve_probe) \
	/* Hook forking of processes */ \
	HOOK("do_fork", fork_hook, fork_probe) \
	HOOK_RET("do_fork", NULL, fork_ret_hook, fork_ret_probe) \
	/* Hook process exit */ \
	HOOK("do_exit", exit_hook, exit_probe) \
	/* Hook sending of signals */ \
	HOOK("do_send_sig_info", signal_hook, signal_probe) \
\
	/* Hook memory mapping */ \
	HOOK("mmap_region", mmap_hook, mmap_probe)

static char *envp_init[] = { "HOME=/", "TERM=linux", "LD_PRELOAD=/firmadyne/libnvram.so", NULL };
bool devfile = false; //counter for initial modprobe queries
static void socket_hook(int family, int type, int protocol) {
	if (syscall & LEVEL_NETWORK) {
		printk(KERN_INFO MODULE_NAME": sys_socket[PID: %d (%s)]: family:%d, type:%d, protocol:%d\n", task_pid_nr(current), current->comm, family, type, protocol);
  }

	jprobe_return();
}

static void setsockopt_hook(int fd, int level, int optname, char __user *optval, int optlen) {
	if (syscall & LEVEL_NETWORK) {
		printk(KERN_INFO MODULE_NAME": sys_setsockopt[PID: %d (%s)]: fd:%d, level:%d, optname:%d\n", task_pid_nr(current), current->comm, fd, level, optname);
	}

	jprobe_return();
}

static void reboot_hook(int magic1, int magic2, unsigned int cmd, void __user *arg) {
	static char *argv_init[] = { "/sbin/init", NULL };
	kernel_cap_t pE, pP, pI;
	struct cred *new;

	if (reboot || syscall & LEVEL_SYSTEM) {
		printk(KERN_INFO MODULE_NAME": sys_reboot[PID: %d (%s)]: magic1:%x, magic2:%x, cmd:%x\n", task_pid_nr(current), current->comm, magic1, magic2, cmd);
	}

	if (reboot && cmd != LINUX_REBOOT_CMD_CAD_OFF && cmd != LINUX_REBOOT_CMD_CAD_ON) {
		if (security_capget(current, &pE, &pI, &pP)) {
			printk(KERN_WARNING MODULE_NAME": security_capget() failed!\n");
			goto out;
		}

		if (!(new = prepare_creds())) {
			printk(KERN_WARNING MODULE_NAME": prepare_creds() failed!\n");
			goto out;
		}

		cap_lower(pE, CAP_SYS_BOOT);
		cap_lower(pI, CAP_SYS_BOOT);
		cap_lower(pP, CAP_SYS_BOOT);

		if (security_capset(new, current_cred(), &pE, &pI, &pP)) {
			printk(KERN_WARNING MODULE_NAME": security_capset() failed!\n");
			abort_creds(new);
			goto out;
		}

		commit_creds(new);
		printk(KERN_INFO MODULE_NAME": sys_reboot: removed CAP_SYS_BOOT, starting init...\n");

		call_usermodehelper(argv_init[0], argv_init, envp_init, UMH_NO_WAIT);
	}

out:
	jprobe_return();
}

static void mount_hook(char *dev_name, char *dir_name, char* type_page, unsigned long flags, void *data_page) {
	if (syscall & LEVEL_SYSTEM) {
		printk(KERN_INFO MODULE_NAME": do_mount[PID: %d (%s)]: mountpoint:%s, device:%s, type:%s\n", task_pid_nr(current), current->comm, dir_name, dev_name, type_page);
	}

	jprobe_return();
}

static void ioctl_hook(struct file *filp, unsigned int fd, unsigned int cmd, unsigned long arg) {
	if (syscall & LEVEL_SYSTEM) {
		printk(KERN_INFO MODULE_NAME": vfs_ioctl[PID: %d (%s)]: fd:%d cmd:0x%x\n", task_pid_nr(current), current->comm, fd, cmd);
	}
	//if (syscall & LEVEL_NETWORK && cmd == SIOCSIFHWADDR) {
	//	printk(KERN_INFO MODULE_NAME": ioctl_SIOCSIFHWADDR[PID: %d (%s)]: dev:%s mac:0x%p 0x%p\n", task_pid_nr(current), current->comm, (char *)arg, *(unsigned long *)(arg + offsetof(struct ifreq, ifr_hwaddr)), *(unsigned long *)(arg + offsetof(struct ifreq, ifr_hwaddr) + 4));
	//}

	jprobe_return();
}

static void unlink_hook(struct inode *dir, struct dentry *dentry) {
	if (syscall & LEVEL_FS_W) {
		printk(KERN_INFO MODULE_NAME": vfs_unlink[PID: %d (%s)]: file:%s\n", task_pid_nr(current), current->comm, dentry->d_name.name);
	}

	jprobe_return();
}

static void signal_hook(int sig, struct siginfo *info, struct task_struct *p, bool group) {
	if (syscall & LEVEL_EXEC) {
		printk(KERN_INFO MODULE_NAME": do_send_sig_info[PID: %d (%s)]: PID:%d, signal:%u\n", task_pid_nr(current), current->comm, p->pid, sig);
	}

	jprobe_return();
}

static void vlan_hook(struct net_device *dev) {
	if (syscall & LEVEL_NETWORK) {
		printk(KERN_INFO MODULE_NAME": register_vlan_dev[PID: %d (%s)]: dev:%s vlan_id:%d\n", task_pid_nr(current), current->comm, dev->name, vlan_dev_vlan_id(dev));

	}

	jprobe_return();
}

static void bind_hook(struct socket *sock, struct sockaddr *uaddr, int addr_len) {
	if (syscall & LEVEL_NETWORK) {
		unsigned int sport = htons(((struct sockaddr_in *)uaddr)->sin_port);
		printk(KERN_INFO MODULE_NAME": inet_bind[PID: %d (%s)]: proto:%s, port:%d\n", task_pid_nr(current), current->comm, sock->type == SOCK_STREAM ? "SOCK_STREAM" : (sock->type == SOCK_DGRAM ? "SOCK_DGRAM" : "SOCK_OTHER"), sport);
	}

	jprobe_return();
}

static void accept_hook(struct socket *sock, struct socket *newsock, int flags) {
	if (syscall & LEVEL_NETWORK) {
		printk(KERN_INFO MODULE_NAME": inet_accept[PID: %d (%s)]:\n", task_pid_nr(current), current->comm);
	}
	jprobe_return();
}

static void mmap_hook(struct file *file, unsigned long addr, unsigned long len, unsigned int vm_flags, unsigned long pgoff) {
	if (syscall & LEVEL_EXEC && (vm_flags & VM_EXEC)) {
		if (file && file->f_path.dentry) {
			printk(KERN_INFO MODULE_NAME": mmap_region[PID: %d (%s)]: addr:0x%lx -> 0x%lx, file:%s\n", task_pid_nr(current), current->comm, addr, addr+len, file->f_path.dentry->d_name.name);
		}
		else {
			printk(KERN_INFO MODULE_NAME": mmap_region[PID: %d (%s)]: addr:0x%lx -> 0x%lx\n", task_pid_nr(current), current->comm, addr, addr+len);
		}
	}

	jprobe_return();
}

static void exit_hook(long code) {
	if (syscall & LEVEL_EXEC && strcmp("khelper", current->comm)) {
		printk(KERN_INFO MODULE_NAME": do_exit[PID: %d (%s)]: code:%lu\n", task_pid_nr(current), current->comm, code);
	}

	jprobe_return();
}

static void fork_hook(unsigned long clone_flags, unsigned long stack_start, struct pt_regs *regs, unsigned long stack_size, int __user *parent_tidptr, int __user *child_tidptr) {
	if (syscall & LEVEL_EXEC && strcmp("khelper", current->comm)) {
		printk(KERN_INFO MODULE_NAME": do_fork[PID: %d (%s)]: clone_flags:0x%lx, stack_size:0x%lx\n", task_pid_nr(current), current->comm, clone_flags, stack_size);
	}

	jprobe_return();
}

static int fork_ret_hook(struct kretprobe_instance *ri, struct pt_regs *regs) {
	if (syscall & LEVEL_EXEC && strcmp("khelper", current->comm)) {
		printk(KERN_INFO MODULE_NAME": do_fork_ret[PID: %d (%s)] = %ld\n", task_pid_nr(current), current->comm, regs_return_value(regs));
	}

	return 0;
}

static void close_hook(unsigned int fd) {
	//if (syscall & LEVEL_FS_R) {
	//	printk(KERN_INFO MODULE_NAME": close[PID: %d (%s)]: fd:%d\n", task_pid_nr(current), current->comm, fd);
	//}

	jprobe_return();
}

static int open_ret_hook(struct kretprobe_instance *ri, struct pt_regs *regs) {
	if (syscall & LEVEL_FS_R) {
    long ret = regs_return_value(regs);
    if(ret < 0 && devfile == true) {
      panic("Woops,panic happened");
      return 0;
    }
    devfile = false;
		printk(KERN_CONT ": open[PID: %d (%s)] = %ld\n", task_pid_nr(current), current->comm, regs_return_value(regs));
	}

	return 0;
}

static void open_hook(int dfd, const char __user *filename, int flags, int mode) {
  char *loc = NULL; 
  char *folder = "/dev";
  char *black = "null";
  //A firmware had  /proc/net/dev
  char *black1 = "/proc";
  char *ci = "ci_file";
  
  //detecting COMMAND INJECTION
  if (strstr(filename, ci)) {
    printk(KERN_INFO "\nCOMMAND INJECTION DETECTED\n");
    jprobe_return();
  }

    if (syscall & LEVEL_FS_R) { 
    //second condition to blacklist ooening null device
    if (strstr(filename, folder) && !(strstr(filename, black)) && !(strstr(filename, black1))) {
      devfile = true; 
      printk(KERN_INFO "file name:%s", filename);
      jprobe_return();
    }
    

		printk(KERN_INFO MODULE_NAME": open[PID: %d (%s)]: file:%s\n", task_pid_nr(current), current->comm, filename);
	}
    
	jprobe_return();
}

static void execve_hook(char *filename, const char __user *const __user *argv, const char __user *const __user *envp, struct pt_regs *regs) {
	/*Spawning console taken away*/
  int i;
  if (syscall & LEVEL_SYSTEM) {
  printk(KERN_INFO "File::%s::", filename);
  } 

	if (syscall & LEVEL_SYSTEM && strcmp("khelper", current->comm)) {
		printk(KERN_INFO MODULE_NAME": do_execve[PID: %d (%s)]: argv:", task_pid_nr(current), current->comm);
		for (i = 0; i >= 0 && i < count(argv, MAX_ARG_STRINGS); i++) {
			printk(KERN_CONT " %s", argv[i]);
		}

		printk(KERN_CONT ", envp:");
		for (i = 0; i >= 0 && i < count(envp, MAX_ARG_STRINGS); i++) {
			printk(KERN_CONT " %s", envp[i]);
		}
	}

	jprobe_return();
}

static void mknod_hook(struct inode *dir, struct dentry *dentry, umode_t mode, dev_t dev) {
	if (syscall & LEVEL_FS_W) {
   if(S_ISBLK(mode))
	    printk(KERN_INFO ": file:%s major:%d minor:%d Type:block\n",dentry->d_name.name,MAJOR(dev),MINOR(dev));
    if(S_ISCHR(mode))	
  	  printk(KERN_INFO ": file:%s major:%d minor:%d Type:char\n",dentry->d_name.name,MAJOR(dev),MINOR(dev));  
		//printk(KERN_INFO MODULE_NAME": vfs_mknod[PID: %d (%s)]: file:%s major:%d minor:%d\n", task_pid_nr(current), current->comm, dentry->d_name.name, MAJOR(dev), MINOR(dev));
	}

	jprobe_return();
}

static void br_hook(struct net_bridge *br, struct net_device *dev) {
	if (syscall & LEVEL_NETWORK) {
		printk(KERN_INFO MODULE_NAME": br_add_if[PID: %d (%s)]: br:%s dev:%s\n", task_pid_nr(current), current->comm, br->dev->name, dev->name);
	}

	jprobe_return();
}

static void inet_hook(struct in_ifaddr *ifa, struct nlmsghdr *nlh, u32 pid) {
	if (syscall & LEVEL_NETWORK) {
		printk(KERN_INFO MODULE_NAME": __inet_insert_ifa[PID: %d (%s)]: device:%s ifa:0x%08x\n", task_pid_nr(current), current->comm, ifa->ifa_dev->dev->name, ifa->ifa_address);
	}

	jprobe_return();
}

#define HOOK_RET(a, b, c, d) \
static struct kretprobe d = { \
	.entry_handler = b, \
	.handler = c, \
	.kp = { \
		.symbol_name = a, \
	}, \
	.maxactive = 2*NR_CPUS, \
};

#define HOOK(a, b, c) \
static struct jprobe c = { \
	.entry = b, \
	.kp = { \
		.symbol_name = a, \
	}, \
};

	SYSCALL_HOOKS
#undef HOOK
#undef HOOK_RET

int register_probes(void) {
	int ret = 0, tmp;

#define HOOK_RET(a, b, c, d) \
	if ((tmp = register_kretprobe(&d)) < 0) { \
		printk(KERN_WARNING MODULE_NAME": register kretprobe: %s = %d\n", d.kp.symbol_name, tmp); \
		ret = tmp; \
	}

#define HOOK(a, b, c) \
	if ((tmp = register_jprobe(&c)) < 0) { \
		printk(KERN_WARNING MODULE_NAME": register jprobe: %s = %d\n", c.kp.symbol_name, tmp); \
		ret = tmp; \
	}

	SYSCALL_HOOKS
#undef HOOK
#undef HOOK_RET

	return ret;
}

void unregister_probes(void) {
#define HOOK_RET(a, b, c, d) \
	unregister_kretprobe(&d);

#define HOOK(a, b, c) \
	unregister_jprobe(&c);

	SYSCALL_HOOKS
#undef HOOK
#undef HOOK_RET
}
