
from display import Display
from util import format_frequency, test_frequencies, test_raw_data
import time
import asyncio

def test_display(d):
  d.display_test(0.5)
  for f in test_frequencies:
    d.display(format_frequency(f))
    time.sleep(0.5)

async def test_queue(queue):
  for item in test_raw_data:
    print(f"Enqueue: {item}")
    queue.put_sync(item)
    await asyncio.sleep(0.5)

if __name__ == '__main__':
  from constants import MOSI, CS, CK
  d = Display(MOSI, CS, CK)
  test_display(d)
