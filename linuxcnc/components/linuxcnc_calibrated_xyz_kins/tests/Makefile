CFLAGS := -DUNITY_INCLUDE_DOUBLE -O2

test_linalg3: test_linalg3.c ../linalg3.c unity.c
	$(CC) -o $@ $^ $(CFLAGS)

test_calibxyzlib: test_calibxyzlib.c ../calibxyzlib.c ../linalg3.c unity.c
	$(CC) -o $@ $^ -lm $(CFLAGS)

.PHONY: all clean
all: test_linalg3 test_calibxyzlib

clean:
	rm -rf test_linalg3 test_calibxyzlib