package: Tcl
description: Tcl interpreter (tclsh and libtcl), the runtime of Environment Modules
version: "8.6.18"
sources:
  - https://downloads.sourceforge.net/project/tcl/Tcl/%(version)s/tcl%(version)s-src.tar.gz,sha256:14f9af32b1767ff718477a8f974ad03c34341097e6b43f4ce54644ee974e268e
license: TCL
---
#!/bin/bash -e
# Only the interpreter, the library and its script library (init.tcl, …): no
# bundled extensions, no manual pages. tclsh and libtcl find libtcl through
# $ORIGIN, set in Tcl's own rpath slots (empty with --disable-rpath), so tclsh
# runs without LD_LIBRARY_PATH wherever it is copied; Tcl finds its script
# library relative to the executable.
"$SOURCEDIR/unix/configure" --prefix="$INSTALLROOT" --enable-shared --disable-rpath
make ${JOBS:+-j$JOBS} binaries libraries \
  'CC_SEARCH_FLAGS=-Wl,-rpath,\$$ORIGIN/../lib' 'LD_SEARCH_FLAGS=-Wl,-rpath,\$$ORIGIN/../lib'
make install-binaries install-libraries install-headers
ln -nfs "tclsh${PKGVERSION%.*}" "$INSTALLROOT/bin/tclsh"
