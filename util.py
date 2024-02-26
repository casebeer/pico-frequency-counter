import re

def format_frequency(f):
  '''Format frequency in Hz for display in 8 characters'''
  # - Allow display of one decimal place, but only under 10 kHz
  # - Limit to 6 sig figs scientific notation at or over 100 MHz (which the counter can't reach
  #   anyway) (we can fit 6 since we remove the '+' and leading '0' of the exponent.
  # - Shorten scientific notation display by removing the non-displayable '+' and the unused
  #   leading 0 of the exponent
  formatted = f"{round(f, 1):{'g' if f < 10000 else '.0f' if f < 1e8 else '.6g'}}"
  return re.sub(r'e\+?0', 'e', formatted)

test_frequencies = [.001, 0.1, 1.01, 1, 1.1, 10.264, 1000.0, 1000.1, 1000.01, 9.99801e6, 10.000e6, 1e8, 100123100, 1.1234567e8]

# TODO: convert to unit test
def test_format_frequency():
  return [(len(s), s) for s in
          [format_frequency(n) for n in test_frequencies]]

if __name__ == '__main__':
  from pprint import pprint
  pprint(test_format_frequency())
