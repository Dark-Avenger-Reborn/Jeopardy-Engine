obj-m += intel_fw_update.o

KDIR := /lib/modules/$(shell uname -r)/build
PWD  := $(shell pwd)

all:
        $(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
        $(MAKE) -C $(KDIR) M=$(PWD) clean