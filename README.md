# bits.bits

bits for users, published on CVMFS so that nothing has to be installed. The
repository builds `bits` itself together with its own runtime: Python with the
modules bits imports, Tcl, and Environment Modules (`modulecmd`). bits runs them
by path, so it changes nothing in the environment of what it builds or loads. A
small entry point, `/cvmfs/bits.cern.ch/bits/bin/bits`, runs it on any supported
platform. Given a community, it builds with that community's recipes and reuses
what the community has published on CVMFS:

```bash
/cvmfs/bits.cern.ch/bits/bin/bits q                        # plain bits (your sw/ dir)
ln -s /cvmfs/bits.cern.ch/bits/bin/bits ~/bin/bits-key4hep
cd key4hep.bits
bits-key4hep build key4hep         # reuses what is on CVMFS, builds the rest in sw/
bits-key4hep enter key4hep/latest  # from sw/: local builds first, then reused ones
BITS_COMMUNITY=LHCB /cvmfs/bits.cern.ch/bits/bin/bits build Gaudi
```

The repository stands alone. It needs no other recipe repository, no compiler
package and no LCG release: `defaults-release.sh` holds the CVMFS layout, and the
recipes are plain shell that builds with the compiler of the build host or
builder image. Their sources come from the projects' own release downloads and
from PyPI (bits' Python modules), at versions chosen here, not by a software
stack. A compiler profile, if one is ever wanted, is another
`defaults-<name>.sh` here.

Without this install, nothing changes: a bits checkout or pip install has no
`runtime/` and uses `python3` and `modulecmd` from PATH as before, and the entry
point exists only on CVMFS.

## Recipes

- **`bits`** installs the runtime part of a bits checkout (the scripts with
  `bits_helpers/`, `keys/` and `templates/` beside them) under `libexec/bits`, and
  copies the three packages below, which it needs only to build, into
  `libexec/bits/runtime`, and checks that nothing in it loads a library from the
host other than the C library (and `libgcc_s`), or through a search path that
is not `$ORIGIN`-relative. bits finds `runtime/bin/python3` and
  `runtime/bin/modulecmd` beside itself and runs them by path, the Python with
  `-E -s` so that the PYTHON* variables of an entered environment do not reach it.
  Its modulefile, written by the recipe, puts only bits on PATH. The recipe
  builds bits `main`.
- **`bits-python`** is a static CPython with bits' modules installed into it,
  pinned with everything they pull in, without what bits never uses (test suite,
  IDLE, Tk, curses, readline, dbm, and pip, so nothing can be installed into it
  later). It finds its standard library from its own location, so it needs
  nothing on LD_LIBRARY_PATH or PYTHONPATH. Its extension modules link the
  libraries below statically. Its OpenSSL does not know where the host keeps its
  CA certificates, so `ssl` (urllib) and certifi (requests, botocore) use the
  host's bundle (the EL, Debian/Ubuntu and openSUSE locations), else certifi's
  own: bits trusts what the host trusts, a site CA included. For `ssl`,
  `SSL_CERT_FILE` and `SSL_CERT_DIR` still take precedence.
- **`OpenSSL`** (the 3.5 LTS), **`zlib`**, **`bzip2`**, **`xz`** (liblzma),
  **`sqlite`** and **`libffi`** are built as static, position-independent
  libraries only, for `bits-python` (and zlib for Tcl). OpenSSL reads no
  configuration of the host: its `OPENSSLDIR` does not exist.
- **`Tcl`** builds only a static `tclsh` and the Tcl script library.
- **`environment-modules`** is the pure-Tcl `modulecmd`. Its `bin/modulecmd`
  locates itself and runs the `tclsh8.6` beside it, else the one on PATH, so it
  works wherever it is copied.

## Building and publishing

```bash
git clone https://github.com/bitsorg/bits.bits && cd bits.bits
bits build bits                                     # this host
bits build --docker --architecture x86_64-el8 bits  # el8, in its builder image
```

The build host or image needs a C compiler with the C library headers, make,
perl with its core modules (`perl-core` on EL, for OpenSSL's Configure), rsync
and binutils. It needs no development packages, as every library comes from a
recipe here, and is better without them. `bits-python` stops if a standard
module bits needs was not built, and `bits` if the runtime would need a host
library. The build architecture is the platform itself (`x86_64-el8`,
`ubuntu2404_x86-64`, …).

Build once per CPU, on the oldest platform the CI builds for it: `x86_64-el8`
and `aarch64-el9`. The runtime needs nothing of the host but the C library, so
a build on the oldest glibc runs on every newer glibc Linux (not musl, e.g.
Alpine): el8 (glibc 2.28) and later on x86_64, el9 (2.34) and later on
aarch64, and current Ubuntu on both. The wheels are pinned at versions that
ship for the same glibc (`manylinux_2_28` and older). If bits' wheels ever stop
shipping for glibc 2.28, `bits-python` fails at its pip install, and the x86_64
build moves to el9.

For CVMFS, build in the bits-console **Bits** community
(`communities/Bits` in bits-console, `cvmfs_prefix: /cvmfs/bits.cern.ch/bits`):
package `bits`, no defaults or extra arguments, the platforms ticked in the
matrix (`x86_64-el8` and `aarch64-el9`), with **Publish to CVMFS** and
**Create release view**. The packages go to
`/cvmfs/bits.cern.ch/bits/<arch>/Packages`, and the merged view, which the entry
point runs from, to `/cvmfs/bits.cern.ch/bits/views/current/<arch>`. The view
holds `bits` alone, its runtime included. Every build of a new bits `main`
replaces the view (the community's `replace_on_conflict`, which the prepub
daemon must allow too); an unchanged one is skipped.

## The entry point

`entry/bits` and `entry/communities` are published by hand, once and whenever they
change, as `/cvmfs/bits.cern.ch/bits/bin/bits` (mode 755) and
`/cvmfs/bits.cern.ch/bits/etc/communities`. They are the only files outside the
build's layout.

The entry point does the following:

1. It picks the view for the host, `views/current/<arch>`: the one for the
   host's CPU (`x86_64`, `aarch64`). If there are several for the CPU, one per
   OS, it takes the one for the host's OS (`el9`, say; it recognises EL hosts,
   from `PLATFORM_ID`, and Ubuntu), and finds none on another OS. So publish
   one view per CPU, as above.
   `BITS_RUNTIME_VIEW=<path of a view>` runs another view, e.g. a new one before it
   is announced.
2. It works out the community, in this order:
   - the link name `bits-<community>`;
   - `$BITS_COMMUNITY` (or `$BITS_ORGANISATION`, its former name), the variable
     bits itself uses for the community's recipes;
   - the CVMFS repository the link is in, from the `repositories` column of
     `etc/communities`.

   It exports the result as `BITS_COMMUNITY`, in upper case.
3. For a community listed in `etc/communities`, it sets `BITS_REUSE_FROM=cvmfs`
   unless the variable is already set. That is the default of `bits build
   --reuse-from` (bits' opt-in reuse of deployed components): a build reuses what
   the community published on CVMFS, by exact content hash under the default
   `strict` policy, and builds the rest. An explicit `--reuse-from`, also from a
   `bits use` profile, wins; `BITS_REUSE_FROM=` turns it off. Recipes without a
   CVMFS layout, or with nothing deployed for the architecture, build without
   reuse, with a warning.
4. For such a community with a `prefix` in `etc/communities`, it also sets
   `BITS_CVMFS_PREFIX` to it, unless the variable is already set (empty turns it
   off). `bits q`, `enter`, `load`, `printenv`, `unload` and `setenv` then also
   use the modules the community published under
   `<prefix>/<arch>/Modules/modulefiles`, for the architecture (`-a` or the
   detected one), the same without its `-opt`/`-dbg` (the toolchain) and with
   the other one, after the local ones: local builds always come first.
5. It runs bits on the user's own work directory. `bits cvmfs show` and
   `bits cvmfs summary` read the CVMFS tree itself.

The entry point sets no PATH, LD_LIBRARY_PATH or PYTHONPATH: bits uses its own
runtime.

The entry point uses bash and GNU coreutils (`realpath -s`, `readlink -f`), so
Linux only. Absolute links from another repository work on clients that mount
`/cvmfs/bits.cern.ch` too. A container that bind-mounts only some repositories
must include it.

## Open points

- **bits needs three changes.** The `runtime/` lookup (in `bits`, `bitsenv` and
  `bitsStore`), the `$BITS_REUSE_FROM` default of `--reuse-from` and the
  `$BITS_CVMFS_PREFIX` module trees must be in the bits release that `bits.sh`
  builds.
- **Reuse reads the community's CVMFS modules tree** at the start of every build
  in its recipes, a cost that the opt-in flag paid only when asked for.
- **The community table is written by hand,** prefixes included (each the
  `system: prefix` of the community's recipes). Reuse does not work yet for
  `alice` and `cms`, nor do their CVMFS modules (no prefix): bits cannot expand
  the `{install_dir}` in alice.bits' modules template, and cms.bits declares no
  CVMFS layout, so their builds skip reuse with the warning. Generating the table from the bits-console
  `ui-config.yaml` files would keep it in step.
- **No bits-providers entry yet.** Without `bits.bits.sh` and a `registry.json`
  entry in bits-providers, `bits init bits.bits` and `BITS_COMMUNITY=BITS` do not
  work. A plain clone does.
- **`version: "0.6"` while the recipe builds `main`.** `bits --version` says 0.6
  whichever commit it was built from; set the version (and `tag:`) to a release
  once there is one.
- **Versions are kept up to date by hand.** The C libraries, Python and the
  pinned wheels (update the list with bits' `pyproject.toml`) are bumped here,
  a security fix included; a new bits view follows. The wheels come from PyPI
  without hash checking.
