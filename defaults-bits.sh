package: defaults-bits
version: v1
# bits group overlay — compose with:  --defaults bits::gcc15::opt
# Inherits the shared build env, compiler profiles and package_family from
# stacks.bits (-> lcg.bits recipe pool). The release comes from the command line
# (--set release=LCG_110); `main` is only the default.
variables:
  release: "main"

requires:
  - stacks.bits

overrides:
  lcg.bits:
    tag: "%(release)s"
  stacks.bits:
    tag: "%(release)s"

# bits CVMFS namespace + layout (system: is NOT hashed). Same layout as the other
# groups: packages once per build arch, modulefiles beside them, and per release
# a merged view, which is what the bits entry point (entry/bits) runs from:
#   /cvmfs/bits.cern.ch/bits/views/<release>/<arch>/libexec/bits
system:
  prefix:                     "/cvmfs/bits.cern.ch/bits"
  cvmfs_user_prefix:          "{prefix}/user"
  cvmfs_packages_template:    "{prefix}/{arch}/Packages/{pkg}/{tag}"
  cvmfs_modules_template:     "{prefix}/{arch}/Modules/modulefiles/{pkg}"
  cvmfs_shared_path_template: "{prefix}/noarch/{pkg}/{tag}"
  cvmfs_releases_template:    "{prefix}/releases/{release}/{family}{pkg}/{version}/{arch}"
  cvmfs_views_template:       "{prefix}/views/{release}/{arch}"
  # The view holds bits alone: its runtime is copied into it (bits.sh), and the
  # build-only packages have no place there.
  cvmfs_view_exclude:         [GCC-Toolchain, bits-recipe-tools, bits-python, Tcl, environment-modules]
---
