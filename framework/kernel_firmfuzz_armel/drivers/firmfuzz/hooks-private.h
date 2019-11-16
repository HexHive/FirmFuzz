#ifndef INCLUDE_PRIVATE_H
#define INCLUDE_PRIVATE_H

/* from net/bridge/br_private.h */
struct net_bridge {
	spinlock_t                      lock;
	struct list_head                port_list;
	struct net_device               *dev;
};

/* for fs/exec.c */
static int count(const char __user * const __user *argv, int max) {
	int i = 0;

	if (argv != NULL) {
		for (;;) {
			const char __user *p;

			if (get_user(p, argv))
				return -EFAULT;
			if (!p)
				break;
			argv++;
			if (i++ >= max)
				return -E2BIG;

			if (fatal_signal_pending(current))
				return -ERESTARTNOHAND;

			cond_resched();
		}
	}
	return i;
}


#endif
