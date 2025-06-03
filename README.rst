
bits
========

Bits is a tool to build, install and package large software stacks. It originates from the aliBuild 
tool, originally developed to simplify building and installing ALICE / ALFA software and attempts to
 make it more general and usable for other communities that share similar problems and have overlapp
ing dependencies.

Instant gratification with::

    pip install bits
     or
    git clone git@github.com:bitsorg/bits.git; cd bits; export PATH=$PWD:$PATH; cd ..
    git clone git@github.com:bitsorg/general.bits.git
    bits init -c general 
    bits build ROOT
    bits enter ROOT/latest
    root -b

Full documentation at:

Pre-requisites
==============

If you are using bits directly from git clone, you should make sure
you have the dependencies installed. The easiest way to do this is to run::

    pip install -e .


For developers
==========

If you want to contribute to bits, you can run the tests with::

    pip install -e .[test] # Only needed once
    tox

The test suite only runs fully on a Linux system, but there is a reduced suite for macOS, runnable with::

    tox -e darwin

You can also run only the unit tests (it's a lot faster than the full suite) with::

    pytest

To run the documentation locally, you can use::

    pip install -e .[docs]
    cd docs
    mkdocs serve
