from constants import MAX_COUNT, PIO_FREQ, CORRECTION
import re

def format_frequency(f):
  '''Format frequency in Hz for display in 8 characters'''
  # - Allow display of one decimal place, but only under 10 kHz
  # - Limit to 6 sig figs scientific notation at or over 100 MHz (which the counter can't reach
  #   anyway) (we can fit 6 since we remove the '+' and leading '0' of the exponent.
  # - Shorten scientific notation display by removing the non-displayable '+' and the unused
  #   leading 0 of the exponent
  formatted = f"{round(f, 1):{'.1f' if f < 10000 else '.0f' if f < 1e8 else '.6g'}}"
  return re.sub(r'e\+?0', 'e', formatted)

def convert_pulse_count(pulse_raw):
  return MAX_COUNT - pulse_raw
def convert_clock_count(clock_raw):
  return 2 * (MAX_COUNT - clock_raw + 1)
def calculate_frequency(clock_raw, pulse_raw):
  return PIO_FREQ * CORRECTION * convert_pulse_count(pulse_raw) / convert_clock_count(clock_raw)

def unconvert_pulse_count(pulse_count):
  '''Helper for tests'''
  return MAX_COUNT - pulse_count
def unconvert_clock_count(clock_count):
  '''Helper for tests'''
  return MAX_COUNT - clock_count / 2 - 1

test_frequencies = [.001, 0.1, 1.01, 1, 1.1, 10.264, 1000.0, 1000.1, 1000.01, 9.99801e6, 10.000e6, 1e8, 100123100, 1.1234567e8]
test_raw_data = [(unconvert_clock_count(PIO_FREQ * CORRECTION), unconvert_pulse_count(int(f))) for f in test_frequencies]

# TODO: convert to unit test
def test_format_frequency():
  return [(len(s), s) for s in
          [format_frequency(n) for n in test_frequencies]]

def test_calculate_frequencies():
  for (clock, pulse), f in zip(test_raw_data, test_frequencies):
    delta = calculate_frequency(clock, pulse) - f
    ppm = delta / f * 1e6
    print(f"{f} Hz, error {delta:.3g} Hz ({ppm:.2f} ppm)")
    assert delta < 1 or ppm < 10

if __name__ == '__main__':
  from pprint import pprint
  pprint(test_format_frequency())
  test_calculate_frequencies()
