# by horuable at https://forums.raspberrypi.com/viewtopic.php?t=306250#p1832034
from rp2 import PIO, asm_pio, StateMachine
from constants import MAX_COUNT, PIO_FREQ

CORRECTED_PIO_FREQ = 125000208.6

@asm_pio(sideset_init=PIO.OUT_HIGH)
def gate():
    """
    PIO to generate gate signal.

    Pin requirements:

    - inputs: input_pin
    - sideset: gate_pin
    """
    mov(x, osr)                                            # load gate time (in clock pulses) from osr
    wait(0, pin, 0)                                        # wait for input to go low
    wait(1, pin, 0)                                        # wait for input to go high - effectively giving us rising edge detection
    label("loopstart")
    jmp(x_dec, "loopstart") .side(0)                       # keep gate low for time programmed by setting x reg
    wait(0, pin, 0)                                        # wait for input to go low
    wait(1, pin, 0) .side(1)                               # set gate to high on rising edge
    irq(block, 0)                                          # set interrupt 0 flag and wait for system handler to service interrupt
    wait(1, irq, 4)                                        # wait for irq from clock counting state machine
    wait(1, irq, 5)                                        # wait for irq from pulse counting state machine

@asm_pio()
def clock_count():
    """
    PIO for counting clock pulses during gate low.

    Pin requirements:

    - inputs: gate_pin
    - jmp_pin: pulse_fin_pin
    """
    mov(x, osr)                                            # load x scratch with max value (2^32-1)
    wait(1, pin, 0)                                        # detect falling edge
    wait(0, pin, 0)                                        # of gate signal
    label("counter")
    jmp(pin, "output")                                     # as long as gate is low //
    jmp(x_dec, "counter")                                  # decrement x reg (counting every other clock cycle - have to multiply output value by 2)
    label("output")
    mov(isr, x)                                            # move clock count value to isr
    push()                                                 # send data to FIFO
    irq(block, 4)                                          # set irq and wait for gate PIO to acknowledge

@asm_pio(sideset_init=PIO.OUT_HIGH)
def pulse_count():
    """
    PIO for counting incoming pulses during gate low.

    Pin requirements:

    - inputs: (gate_pin, input_pin)
    - jmp_pin: gate_pin
    - sideset: pulse_fin_pin

    n.b. uses both gate and input pulse pins as inputs, so input_pin must be gate_pin + 1
    """
    mov(x, osr)                                            # load x scratch with max value (2^32-1)
    wait(1, pin, 0)
    wait(0, pin, 0) .side(0)                               # detect falling edge of gate
    label("counter")
    wait(0, pin, 1)                                        # wait for rising
    wait(1, pin, 1)                                        # edge of input signal
    jmp(pin, "output")                                     # as long as gate is low //
    jmp(x_dec, "counter")                                  # decrement x req counting incoming pulses (probably will count one pulse less than it should - to be checked later)
    label("output")
    mov(isr, x) .side(1)                                   # move pulse count value to isr and set pin to high to tell clock counting sm to stop counting
    push()                                                 # send data to FIFO
    irq(block, 5)                                          # set irq and wait for gate PIO to acknowledge


def init_sm(freq, input_pin, gate_pin, pulse_fin_pin, gate_cycles=None):
    """
    Starts state machines.

    n.b. pulse_count SM uses both gate and input pulse pins as inputs,
         so input_pin must be gate_pin + 1.
    """
    if gate_cycles is None:
      gate_cycles = freq  # default gate to one second

    gate_pin.value(1)
    pulse_fin_pin.value(1)

    print(f"MAX_COUNT = {MAX_COUNT:08x}")

    sm0 = StateMachine(0, gate, freq=freq, in_base=input_pin, sideset_base=gate_pin)
    sm0.put(gate_cycles)
    sm0.exec("pull()")

    sm1 = StateMachine(1, clock_count, freq=freq, in_base=gate_pin, jmp_pin=pulse_fin_pin)
    sm1.put(MAX_COUNT)
    sm1.exec("pull()")

    sm2 = StateMachine(2, pulse_count, freq=freq, in_base=gate_pin, sideset_base=pulse_fin_pin, jmp_pin=gate_pin)
    sm2.put(MAX_COUNT - 1)
    sm2.exec("pull()")

    sm1.active(1)
    sm2.active(1)
    sm0.active(1)

    return sm0, sm1, sm2

def main():
    from machine import Pin
    import uarray as array

    update_flag = [False]
    data = array.array("I", [0, 0])

    def counter_handler(sm):
        print("IRQ")
        if not update_flag[0]:
            # sm0.put(125_000)
            # sm0.exec("pull()")
            data[0] = sm1.get() # clock count
            data[1] = sm2.get() # pulse count
            update_flag[0] = True

    sm0, sm1, sm2 = init_sm(PIO_FREQ, Pin(15, Pin.IN, Pin.PULL_UP), Pin(14, Pin.OUT), Pin(13, Pin.OUT))
    sm0.irq(counter_handler)

    print("Starting test")
    i = 0
    while True:
        if update_flag[0]:
            clock_count = 2 * (MAX_COUNT - data[0]+1)
            pulse_count = MAX_COUNT - data[1]
            freq = pulse_count * (CORRECTED_PIO_FREQ / clock_count)
            print(i)
            print("Clock count: {}".format(clock_count))
            print("Input count: {}".format(pulse_count))
            print("Frequency:   {}".format(freq))
            i += 1
            update_flag[0] = False

if __name__ == "__main__":
  main()
