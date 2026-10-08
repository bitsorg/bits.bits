package: bits-python
description: The Python bits runs on, with the modules bits imports, as one relocatable prefix
version: "3.13.11"
sources:
  - https://www.python.org/ftp/python/%(version)s/Python-%(version)s.tgz,sha256:03cfedbe06ce21bc44ce09245e091a77f2fee9ec9be5c52069048a181300b202
license: Python-2.0
sandbox_network: off   # pip install of bits' modules
---
#!/bin/bash -e
# Static, without libpython.so: the interpreter finds its standard library from
# its own location, so the prefix works wherever it is copied, with nothing on
# LD_LIBRARY_PATH or PYTHONPATH. bits runs it by path (see bits.sh).
"$SOURCEDIR/configure" --prefix="$INSTALLROOT" --disable-shared --with-ensurepip=install
make ${JOBS:+-j$JOBS}
make install
py="$INSTALLROOT/bin/python3"
# bits' modules (pyproject.toml) with everything they pull in, pinned, binary
# wheels only; pip check proves the set complete and consistent, and the import
# check that no standard module bits needs was skipped for a missing header.
"$py" -m pip install --no-cache-dir --only-binary=:all: --no-deps \
  PyYAML==6.0.2 requests==2.32.3 distro==1.9.0 Jinja2==3.1.6 boto3==1.35.48 \
  cryptography==46.0.3 qrcode==7.4.2 \
  botocore==1.35.48 s3transfer==0.10.3 jmespath==1.0.1 python-dateutil==2.9.0.post0 six==1.17.0 \
  urllib3==2.7.0 idna==3.18 certifi==2024.8.30 charset_normalizer==3.4.0 MarkupSafe==3.0.2 \
  cffi==2.0.0 pycparser==2.22 pypng==0.20220715.0 typing_extensions==4.16.0
"$py" -m pip check
"$py" -c 'import ssl, sqlite3, zlib, bz2, lzma, ctypes, uuid, yaml, boto3, cryptography'
# What bits never uses goes, as bits.sh copies the whole prefix.
rm -rf "$INSTALLROOT"/lib/libpython*.a "$INSTALLROOT"/lib/python3*/config-*/libpython*.a \
       "$INSTALLROOT"/lib/python3*/{test,idlelib,tkinter,turtledemo,ensurepip}
strip "$INSTALLROOT"/bin/python3.*[0-9]
