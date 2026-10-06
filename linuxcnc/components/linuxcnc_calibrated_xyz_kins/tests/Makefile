CPPFLAGS += -DUNITY_INCLUDE_DOUBLE
CFLAGS ?= -O2 -Wall
LDLIBS += -lm

TESTS := test_linalg3 test_calibxyzlib

.PHONY: all check clean
all: $(TESTS)

check: all
	@for t in $(TESTS); do ./$$t || exit 1; done

test_linalg3: test_linalg3.c ../linalg3.c unity.c
test_calibxyzlib: test_calibxyzlib.c ../calibxyzlib.c ../linalg3.c unity.c

$(TESTS): ../calibxyzlib.h ../linalg3.h unity.h unity_internals.h
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ $(filter %.c,$^) $(LDLIBS)

clean:
	rm -f $(TESTS)