
from machine import Pin, SoftSPI
from display import Display, \
  DISPLAY_TEST, DECODE_MODE, SHUTDOWN, INTENSITY, SCAN_LIMIT, \
  code_b, CODE_B_DP
from constants import MOSI, CS, CK
import time

def spi_init(mosi, csp, ck, miso=None):
    cs = Pin(csp)
    spi = SoftSPI(
      baudrate=400000,
      polarity=1,
      phase=0,
      sck=Pin(ck),
      mosi=Pin(mosi),
      miso=Pin(miso),
    )
    return cs, spi

def spi_command(spi, cs, command, data):
  '''Send command to MAX7812'''
  try:
    cs(0)
    spi.write(bytearray([command, data]))
  finally:
    cs(1)

def softspi():
  '''Use Software SPI'''
  d = Display(11, 12, 13)
  d.spi_command(DISPLAY_TEST, 0x1)
  time.sleep(30)
  return

  cs, spi = spi_init(11, 12, 13)

  spi_command(spi, cs, DISPLAY_TEST, 0x1)
  time.sleep(30)
  return
  d = Display(MOSI, CS, CK)
  d.spi_command(DISPLAY_TEST, 0x1)
  time.sleep(5)
  d.spi_command(DISPLAY_TEST, 0x0)

  d.spi_command(DECODE_MODE, 0x0)  # no code-b font decode for all digits
  d.spi_command(INTENSITY, 0xf)  # 0x0-0xf
  d.spi_command(SCAN_LIMIT, 0x7)  # scan all 8 digits

  # clear all digit data
  for digit in range(1, 9, 1):
    d.spi_command(digit, 0x0)

  d.spi_command(SHUTDOWN, 0x1)  # enter normal mode

  for digit in range(1, 9, 1):
    data = 0xaa
    print(digit, data)
    d.spi_command(digit, data)
    time.sleep(.25)

  d.spi_command(DECODE_MODE, 0xff)  # Code-B decoding for all digits
  # clear all digit data, Code B
  for digit in range(1, 9, 1):
    d.spi_command(digit, code_b[' '])

  digit = 0
  for char in "0123456789-ehlp ":
    d.spi_command(digit + 1, code_b[char] | (CODE_B_DP if digit % 2 else 0))
    digit = (digit + 1) % 8
    time.sleep(.25)

  # d.spi_command(SHUTDOWN, 0x0)  # enter shutdown mode
