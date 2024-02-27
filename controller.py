import asyncio
from machine import Pin, reset
from rp2 import bootsel_button
from threadsafe import ThreadSafeQueue
import time
import uarray as array

from constants import MOSI, CS, CK, PIO_FREQ, GATE_CYCLES, DISPLAY_INTENSITY, \
  IDLE_THRESHOLD_MS, INIT_IDLE_THRESHOLD_MS, IDLE_SLEEP_MS
from display import Display
from reciprocal_counter import init_sm
from util import format_frequency, convert_clock_count, convert_pulse_count, calculate_frequency

# sanity check idle delay times
assert IDLE_SLEEP_MS < IDLE_THRESHOLD_MS
assert IDLE_SLEEP_MS < INIT_IDLE_THRESHOLD_MS

async def display_loop(disp, queue):
  print("Starting counter...")
  i = 0
  # preload the idle counter so we display idle faster when starting up
  idle_count = (IDLE_THRESHOLD_MS - INIT_IDLE_THRESHOLD_MS) // IDLE_SLEEP_MS
  idle_threshold = IDLE_THRESHOLD_MS // IDLE_SLEEP_MS
  while True:
    # polling queue rather than using `async for ...` so we can change behavior after timeout
    if queue.empty():
      # if we've been idle for 30 sleep cycles i.e. 3 seconds, revert display to '-'
      if idle_count > idle_threshold:
        disp.display('-')
      # TODO: put display and microcontroller to sleep after enough idle cycles
      await asyncio.sleep_ms(IDLE_SLEEP_MS)
      idle_count += 1
      continue
    idle_count = 0
    clock_raw, pulse_raw = queue.get_sync(block=False)
    freq = calculate_frequency(clock_raw, pulse_raw)

    print(f"Measurement {i}")
    print(f"  Raw data:    (clock {clock_raw}, pulse {pulse_raw})")
    print(f"  Clock count: {convert_clock_count(clock_raw)}")
    print(f"  Input count: {convert_pulse_count(pulse_raw)}")
    print(f"  Frequency:   {freq} Hz")
    i += 1
    disp.display(format_frequency(freq))

def init_counter(queue):
  '''
  Configure and start the counter PIO state machines
  Measurement data will be pushed onto the provided queue by the counter IRQ handler.
  '''
  data = array.array("I", [0, 0])

  def counter_handler(sm):
    '''
    IRQ handler
    Pulls data from the clock and counter PIO state machines when the gate SM signals a
    measurement is complete. Sends data into queue for consumption by display loop.
    '''
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

async def run_display_test(disp, queue):
  '''Excercise the display code by running a mock data producer'''
  import test_display
  display_task = asyncio.create_task(display_loop(disp, queue))
  await asyncio.create_task(test_display.test_queue(queue))
  print("Done running async display test.")
  display_task.cancel()

def main():
  '''Main entry point and controller'''
  print("Hello.")

  # configure the 7-segment LED display
  d = Display(MOSI, CS, CK)

  d.intensity(DISPLAY_INTENSITY)
  d.display_test(0.5)

  d.clear()
  d.enable()

  # create queue for passing data from counter state machine IRQ handler to display loop
  queue = ThreadSafeQueue(10)

  # read the BOOTSEL button (1 == LOW/pressed) once after the display self-test completes
  # n.b. this read momentarily disables interrupts
  if bootsel_button() == 1:
    # Hold the BOOTSEL button as soon as (but not before) you see the display self-test flash
    # to perform a test of formatting and displaying different frequencies, then reboot

    asyncio.run(run_display_test(d, queue))

    print("Resetting...")
    d.display("--------")

    time.sleep(2)
    reset()

  # configure and start counter state machines
  init_counter(queue)

  # start display loop
  asyncio.run(display_loop(d, queue))