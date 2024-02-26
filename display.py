
from machine import Pin, SoftSPI
import time

# SoftSPI forces us to set a MISO even though we are TX-only
# Pick an unused pin.
MISO = 20

DEFAULT_INTENSITY = 50  # %

# MAX7219 register addresses
NOOP = 0x0
DECODE_MODE = 0x9
INTENSITY = 0xa
SCAN_LIMIT = 0xb
SHUTDOWN = 0xc
DISPLAY_TEST = 0xf

CODE_B_ALPHABET = '0123456789-ehlp '
CODE_B_DP = 0x80
code_b = dict((char, index) for index, char in enumerate(CODE_B_ALPHABET))
code_b['.'] = CODE_B_DP

def next_default(it, default):
  '''
  Helper to call next() with a default value
  Since Micropython doesn't implement 2nd arg to next(). See
  https://docs.micropython.org/en/latest/genrst/modules.html
  '''
  try:
    return next(it)
  except StopIteration:
    return default


symbols = code_b
MISSING_SYMBOL_REPLACEMENT = ' '
BLANK_SYMBOL = symbols.get(' ')


class Display():
  '''Control a MAX7812 7-segment display'''
  dot_symbol = CODE_B_DP

  # n.b. miso is an unused pin, but SoftSPI forces us to set it
  def __init__(self, mosi, cs, ck, miso=MISO):
    self.cs = Pin(cs, Pin.OUT)
    self.spi = SoftSPI(
      baudrate=1000000,
      polarity=1,
      phase=0,
      sck=Pin(ck),
      mosi=Pin(mosi),
      miso=Pin(miso),
    )

    self._init_display()

  def _init_display(self):
    self.shutdown()

    self._stop_display_test()
    # self.spi_command(DECODE_MODE, 0x0)  # no code-b decode for all digits
    self.spi_command(DECODE_MODE, 0xff)  # code-b decode mode for all digits
    self.spi_command(SCAN_LIMIT, 0x7)  # scan all 8 digits
    self.intensity(DEFAULT_INTENSITY)

    self.clear()
    self.enable()

  def intensity(self, percent):
    '''
    Set the intensity of the display in percent
    '''
    intensity = max(0, min(percent, 100)) * 0xf // 100
    # print(f"{percent} % = intensity {intensity}")
    self.spi_command(INTENSITY, intensity)  # 0x0-0xf

  def shutdown(self):
    '''Set display to low power/no digits displayed. Data will be retained'''
    self.spi_command(SHUTDOWN, 0x0)

  def enable(self):
    '''Turn on display. Display will show existing stored data.'''
    self.spi_command(SHUTDOWN, 0x1)

  def clear(self):
    '''Clear the display'''
    # assume code-b mode
    # clear all digit data, Code B

    for digit, symbol in self.render(''):
      self.spi_command(digit, symbol)

  def display_test(self, seconds=1):
    '''Trigger MAX7218's internal all-segments display test for duration'''
    print("Running LED display test...")
    try:
      self._start_display_test()
      time.sleep(seconds)
    finally:
      self._stop_display_test()

  def _start_display_test(self):
    self.spi_command(DISPLAY_TEST, 0x1)

  def _stop_display_test(self):
    self.spi_command(DISPLAY_TEST, 0x0)

  def symbolize(self, text):
    '''Convert a string into an generator of symbol ints'''
    return self.merge_dots(
        symbols.get(char.lower(), symbols.get(MISSING_SYMBOL_REPLACEMENT, 0))
        for char in text)

  def merge_dots(self, symbols):
    '''
    Generator to merge dot ('.') symbols into the previous digit's
    symbol. Use for 8-segment displays with dedicated dot segments.

    Accepts an iterable of symbol ints and returns a generator of
    symbol ints.
    '''
    if self.dot_symbol == 0:
      # no dot symbol defined, skip this
      return symbols

    symbol = None
    it = iter(symbols)
    previous = next(it)
    for symbol in it:
      if symbol == self.dot_symbol:
        if previous & self.dot_symbol == 0:
          # only merge if previous wasn't another dot or dotted char!
          previous = previous | self.dot_symbol
          symbol = None
      if previous is not None:
        yield previous
      previous = symbol
    if previous is not None:
      yield previous

  def render_left_justified(self, symbols):
    '''Prepare 8 chars for display, left justified'''
    it = iter(symbols)
    # output left justified, blank padded
    for digit_addr in [8, 7, 6, 5, 4, 3, 2, 1]:
      yield digit_addr, next_default(it, BLANK_SYMBOL)

  def render(self, symbols):
    '''Prepare 8 chars for display, right justified'''
    # output right justified, blank padded
    digit_addrs = [8, 7, 6, 5, 4, 3, 2, 1]
    buffer = list(zip(digit_addrs, symbols))

    def helper():
      # pad from the left with blanks
      for i in range(len(digit_addrs) - len(buffer)):
        yield BLANK_SYMBOL
      for _, symbol in buffer:
        yield symbol

    return list(zip(digit_addrs, helper()))

  def display(self, string):
    '''Display a message'''
    symbols = self.symbolize(string)

    rendered = self.render(symbols)
    for addr, symbol in rendered:
      # print(f"{addr}, {symbol}")
      self.spi_command(addr, symbol)

  def display8(self, string):
    '''Display a message (max 8 chars)'''
    message = f"{string[:8]:>8}"
    print(f"requested '{string}'\ndisplaying '{message}'")
    for digit, char in enumerate(reversed(message)):
      encoded = code_b[char]

      self.spi_command(digit + 1, encoded)

  def spi_command(self, command, data):
    '''Send command to MAX7812'''
    try:
      self.cs.off()
      self.spi.write(bytearray([command & 0xff, data & 0xff]))
    finally:
      self.cs.on()


def display_test():
  d = Display(11, 12, 13)
  d.display_test()
  d.clear()
  d.enable()

  intensity = 0
  val = 0
  while True:
    d.intensity(intensity)
    d.display(f"{(val / 100):.3e}".replace('+', ''))
    time.sleep(.01)
    val += 1
    intensity = (intensity + 1) % 100

  while True:
    d.intensity(100)
    d.display8('12345678')
    time.sleep(1)

    d.intensity(0)
    d.display('1234')
    time.sleep(1)

    d.intensity(25)
    d.display(f"{12.34}")
    time.sleep(1)
