clear:
	-rm -fRv build data dist docs libs *.egg-info
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

dist: clear
	python setup.py rotate --match=.tar.gz --keep=3
	python setup.py sdist -v --dist-dir=build --formats=gztar,zip
	-rm -fRv *.egg-info
