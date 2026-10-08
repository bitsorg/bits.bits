package: bits
description: bits build and environment tool, with its own Python and Environment Modules
version: "0.6"
source: https://github.com/bitsorg/bits
# Build-only: their files are copied into runtime/ (below), so loading bits must
# not load them, nor put their bin and lib on PATH and LD_LIBRARY_PATH.
build_requires:
  - bits-recipe-tools
  - bits-python
  - Tcl
  - environment-modules
license: GPL-3.0-or-later
---
#!/bin/bash -e
##############################
. $(bits-include BitsRecipe)
##############################
MODULE_OPTIONS=""
##############################
# The install is the runtime part of a git checkout (the README's "clone and put
# it on PATH"): the scripts with bits_helpers/, keys/ and templates/ beside them,
# which bits finds relative to its own directory. It goes to libexec/bits, not
# bin/, so a merged view links the directory whole.
#
# runtime/ beside the scripts holds bits' own Python with its modules, Tcl and
# modulecmd, copied from those packages. bits finds it there and runs them by
# path, so it needs nothing on PATH, LD_LIBRARY_PATH or PYTHONPATH and adds
# nothing to the environment of what it builds or loads.
function MakeInstall() {
  local dest="$INSTALLROOT/libexec/bits" d
  mkdir -p "$dest/runtime"
  # No .git in the install: bits_helpers/version.py reads the version of an
  # installed package from _version.py.
  rsync -a --exclude '/.*' --exclude /tests --exclude /docs --exclude /console-backend \
        --exclude /debian --exclude /tools --exclude '/*.egg-info' --exclude __pycache__ \
        ./ "$dest/" &&
    printf 'version = "%s"\n' "$PKGVERSION" > "$dest/bits_helpers/_version.py" &&
    for d in "${BITS_PYTHON_ROOT:?}"/{bin,lib} "${TCL_ROOT:?}"/{bin,lib} "${ENVIRONMENT_MODULES_ROOT:?}"/{bin,libexec}; do
      mkdir -p "$dest/runtime/${d##*/}" && cp -a "$d/." "$dest/runtime/${d##*/}/" || return
    done &&
    [ -x "$dest/runtime/bin/python3" ] && [ -x "$dest/runtime/bin/modulecmd" ]
}

function PostInstall() {
  # `module load bits`: the scripts' directory on PATH.
  echo 'prepend-path PATH $PKG_ROOT/libexec/bits' >> "$MODULEFILE"
}
