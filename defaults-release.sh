package: defaults-release
version: v1
# bits.bits stands alone: no other recipe repository, no compiler package. The
# packages build with the compiler of the build host or builder image, and the
# build architecture is just the platform (x86_64-el9, …), so plain
# `bits build bits` works. A compiler profile, if one is ever wanted, is another
# defaults-<name>.sh here (--defaults <name>).
variables:
  # The {release} of the merged view the entry point runs from:
  # /cvmfs/bits.cern.ch/bits/views/current/<arch>. A new bits replaces it
  # (replace_on_conflict in the Bits community).
  release: "current"

# The CVMFS namespace and layout are in cvmfs.yaml.
---
