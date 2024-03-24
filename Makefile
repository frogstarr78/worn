.PHONY: test coverage
all:
	echo all

test:
	bin/python3 -m unittest discover -vv

coverage:
	-bin/coverage run --source=lib --omit=lib/python3.11/** --module unittest discover -vv
	bin/coverage report -m
