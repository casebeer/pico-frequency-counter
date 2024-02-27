# LED Display config
MOSI = 11
CS = 12
CK = 13

DISPLAY_INTENSITY = 50  # %

# Frequency counter config
PIO_FREQ = 125_000_000
# TODO: Add temperature compensation per RP2040 internal temp sensor
# read 9998082 @ correction == 1, oscope reads 9.9985 MHz
# (9998082./9998500)**-1 = 1.000041808018778
CORRECTION = 1.00004
GATE_CYCLES = PIO_FREQ // 10  # i.e. 100 ms gate time
MAX_COUNT = (1 << 32) - 1

# Program behavior
IDLE_THRESHOLD_MS = 3000 # stop displaying last freq after delay w/no detected freq
INIT_IDLE_THRESHOLD_MS = 1000  # shorter idle time when booting up
IDLE_SLEEP_MS = 100 # time to sleep when no freq detected
