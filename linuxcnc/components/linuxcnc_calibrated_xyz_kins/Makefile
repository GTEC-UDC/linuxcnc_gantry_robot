obj-m += calibxyzkins.o
calibxyzkins-objs := calibxyzkins.o calibxyzkinsutils.o calibxyzlib.o linalg3.o
include /usr/share/linuxcnc/Makefile.modinc

EXTRA_CFLAGS += -O2

.PHONY: clean
clean:
	rm -rf *.o *.so *.ver *.tmp *.sym