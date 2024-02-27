

run: force
	mpremote mount . run main.py

dev-env: force
	virtualenv venv
	venv/bin/pip install -r dev_requirements.txt

display-test: force
	mpremote mount . run test_display.py

install: main.py constants.py controller.py display.py reciprocal_counter.py util.py test_display.py
	mpremote cp $^ : + reset

install-deps: force
	mpremote mip install github:peterhinch/micropython-async/v3/primitives
	mpremote mip install github:peterhinch/micropython-async/v3/threadsafe

force:
