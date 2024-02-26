
from display import Display
from constants import MOSI, CS, CK
from util import format_frequency, test_frequencies
import time

def test_display():
  d = Display(MOSI, CS, CK)
  d.display_test(0.5)
  for f in test_frequencies:
    d.display(format_frequency(f))
    time.sleep(0.5)

if __name__ == '__main__':
  test_display()
