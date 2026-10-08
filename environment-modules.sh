package: environment-modules
description: Environment Modules (modulecmd), which bits uses for q/enter/load
version: "5.6.2"
sources:
  - https://github.com/envmodules/modules/releases/download/v%(version)s/modules-%(version)s.tar.gz,sha256:a06dd0001aef2722564bba3ec7ff62bc52fb560565af8522728ac8296f98fd69
requires:
  - Tcl
build_requires:
  - bits-recipe-tools
license: GPL-2.0-or-later
---
#!/bin/bash -e
##############################
. $(bits-include AutoToolsRecipe)
##############################
MODULE_OPTIONS="--bin"
##############################
# Pure Tcl: no C extension library, no documentation tree, no example modulefiles
# (bitsenv sets MODULEPATH itself). The release tarball carries pre-built man
# pages, so no Sphinx is needed. configure looks for tclsh only in the system
# directories, so it is given ours.
function Configure() {
  ./configure --prefix="$INSTALLROOT" --with-tclsh="$TCL_ROOT/bin/tclsh8.6" \
              --disable-libtclenvmodules --disable-doc-install --disable-example-modulefiles
}
function PostInstall() {
  # The installed bin/modulecmd execs modulecmd.tcl by its absolute build path,
  # with the tclsh of the build. Replace it with one that locates itself and runs
  # the tclsh8.6 beside it in a merged view, else the one on PATH (Tcl's module),
  # so the package works wherever it is published.
  cat > "$INSTALLROOT/bin/modulecmd" <<'EOF'
#!/bin/sh
t=$(dirname "$0")/tclsh8.6
[ -x "$t" ] || t=tclsh8.6
exec "$t" "$(dirname "$(readlink -f "$0")")/../libexec/modulecmd.tcl" "$@"
EOF
  chmod 755 "$INSTALLROOT/bin/modulecmd"
}
