import asyncio
from machine import Pin
from threadsafe import ThreadSafeQueue
import uarray as array

from constants import MOSI, CS, CK, PIO_FREQ, CORRECTION, GATE_CYCLES, DISPLAY_INTENSITY
from display import Display
from reciprocal_counter import init_sm
from util import format_frequency

async def count():

  d = Display(MOSI, CS, CK)

  d.intensity(DISPLAY_INTENSITY)
  d.display_test(0.5)

  d.clear()
  d.enable()

  queue = ThreadSafeQueue(10)
  data = array.array("I", [0, 0])

  def counter_handler(sm):
    print("IRQ")
    data[0] = sm_clock.get() # clock count
    data[1] = sm_count.get() # pulse count
    print(data)
    queue.put_sync(data)

  sm_gate, sm_clock, sm_count = init_sm(PIO_FREQ, Pin(10, Pin.IN, Pin.PULL_UP), Pin(9, Pin.OUT), Pin(8, Pin.OUT))
  sm_gate.irq(counter_handler)

  # set gate cycle count to ~1/10 second (rather than 1 s)
  sm_gate.put(GATE_CYCLES)
  sm_gate.exec("pull()")

  print("Starting counter...")
  i = 0
  max_count = (1 << 32) - 1
  # prep the idle counter so we display idle faster when starting up
  idle_count = 20
  while True:
    if queue.empty():
      if idle_count > 30:
        d.display('-')
      await asyncio.sleep_ms(100)
      idle_count += 1
      continue
    idle_count = 0
    clock_raw, pulse_raw = queue.get_sync(block=False)
    print(clock_raw, pulse_raw)

  # async for clock_raw, pulse_raw in queue:
    clock_count = 2 * (max_count - clock_raw + 1)
    pulse_count = max_count - pulse_raw
    freq = pulse_count * (PIO_FREQ * CORRECTION / clock_count)
    print(i)
    print(">Clock count: {}".format(clock_count))
    print(">Input count: {}".format(pulse_count))
    print(">Frequency:   {}".format(freq))
    i += 1
    d.display(format_frequency(freq))

def main():
  '''Main entry point'''
  print("Hello.")
  # softspi()

  # display_test()
  asyncio.run(count())
