.PHONY: test coverage
all:
	echo all

test:
	bin/python3 -m unittest -v test/test_args.py test/test_db.py test/test_lib.py test/test_project.py test/test_report.py

coverage:
	-bin/coverage run --source=lib --omit=lib/python3.11/** --module unittest -v test/test_args.py test/test_db.py test/test_lib.py test/test_project.py test/test_report.py
	bin/coverage report -m
