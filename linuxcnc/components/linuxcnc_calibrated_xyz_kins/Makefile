obj-m += calibxyzkins.o
calibxyzkins-objs := calibxyzkins.o calibxyzkinsutils.o calibxyzlib.o linalg3.o
include /usr/share/linuxcnc/Makefile.modinc

EXTRA_CFLAGS += -O2 -Wall

calibxyzkins.o: calibxyzkinsutils.h calibxyzlib.h
calibxyzkinsutils.o: calibxyzkinsutils.h calibxyzlib.h
calibxyzlib.o: calibxyzlib.h linalg3.h
linalg3.o: linalg3.h

.PHONY: clean
clean:
	rm -rf *.o *.so *.ver *.tmp *.sym