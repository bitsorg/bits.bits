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
BITS_ORGANISATION=LHCB /cvmfs/bits.cern.ch/bits/bin/bits build Gaudi
```

The repository stands alone. It needs no other recipe repository, no compiler
package and no LCG release: `defaults-release.sh` holds the CVMFS layout, and the
four recipes (`bits-python`, `Tcl`, `environment-modules`, `bits`) are plain
shell that builds with the compiler of the build host or builder image. Their
sources come from python.org, SourceForge (Tcl), GitHub (Environment Modules,
bits) and PyPI (bits' Python modules). A compiler profile, if one is ever wanted,
is another `defaults-<name>.sh` here.

Without this install, nothing changes: a bits checkout or pip install has no
`runtime/` and uses `python3` and `modulecmd` from PATH as before, and the entry
point exists only on CVMFS.

## Recipes

- **`bits`** installs the runtime part of a bits checkout (the scripts with
  `bits_helpers/`, `keys/` and `templates/` beside them) under `libexec/bits`, and
  copies the three packages below, which it needs only to build, into
  `libexec/bits/runtime`. bits finds `runtime/bin/python3` and
  `runtime/bin/modulecmd` beside itself and runs them by path, the Python with
  `-E -s` so that the PYTHON* variables of an entered environment do not reach it.
  Its modulefile, written by the recipe, puts only bits on PATH. The recipe
  builds bits `main`.
- **`bits-python`** is a static CPython with bits' modules installed into it,
  pinned with everything they pull in, without what bits never uses (test suite,
  IDLE, Tk). It finds its standard library from its own location, so it needs
  nothing on LD_LIBRARY_PATH or PYTHONPATH.
- **`Tcl`** builds only `tclsh`, `libtcl` and the Tcl script library. They find
  `libtcl` through `$ORIGIN`, so `tclsh` needs no LD_LIBRARY_PATH.
- **`environment-modules`** is the pure-Tcl `modulecmd`. Its `bin/modulecmd` locates
  itself and runs the `tclsh8.6` beside it, else the one on PATH, so it works
  wherever it is copied.

## Building and publishing

```bash
git clone https://github.com/bitsorg/bits.bits && cd bits.bits
bits build bits                                   # this host
bits build --docker --architecture x86_64-el9 bits   # another Linux, in its builder image
```

The build host or image needs a C compiler, make, rsync and the development
headers CPython uses (OpenSSL, zlib, bzip2, xz, libffi, SQLite, libuuid);
`bits-python` stops if one of those modules is missing. The build architecture
is the platform itself (`x86_64-el9`, `ubuntu2404_x86-64`, …).

For CVMFS, build in the bits-console **Bits** community
(`communities/Bits` in bits-console, `cvmfs_prefix: /cvmfs/bits.cern.ch/bits`):
package `bits`, no defaults or extra arguments, the platforms ticked in the
matrix, with **Publish to CVMFS** and **Create release view**. The packages go to
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

1. It picks the view for the host, `views/current/<arch>`, the one whose name
   holds the host's CPU and OS (`x86_64` and `el9`, say). It
   recognises EL hosts (from `PLATFORM_ID`) and Ubuntu.
   `BITS_RUNTIME_VIEW=<path of a view>` runs another view, e.g. a new one before it
   is announced.
2. It works out the community, in this order:
   - the link name `bits-<community>`;
   - `$BITS_ORGANISATION`, the variable bits itself already uses for the
     community's recipes;
   - the CVMFS repository the link is in, from the `repositories` column of
     `etc/communities`.

   It exports the result as `BITS_ORGANISATION`, in upper case.
3. For a community listed in `etc/communities`, it sets `BITS_REUSE_FROM=cvmfs`
   unless the variable is already set. That is the default of `bits build
   --reuse-from` (bits' opt-in reuse of deployed components): a build reuses what
   the community published on CVMFS, by exact content hash under the default
   `strict` policy, and builds the rest. An explicit `--reuse-from`, also from a
   `bits use` profile, wins; `BITS_REUSE_FROM=` turns it off. Recipes without a
   CVMFS layout, or with nothing deployed for the architecture, build without
   reuse, with a warning.
4. It runs bits. Every command, the module commands included, works on the
   user's own work directory, so local builds are always seen; to look at the
   CVMFS tree itself, `bits cvmfs show` and `bits cvmfs summary` read it directly.

The entry point sets no PATH, LD_LIBRARY_PATH or PYTHONPATH: bits uses its own
runtime.

The entry point uses bash and GNU coreutils (`realpath -s`, `readlink -f`), so
Linux only. Absolute links from another repository work on clients that mount
`/cvmfs/bits.cern.ch` too. A container that bind-mounts only some repositories
must include it.

## Open points

- **bits needs two changes.** The `runtime/` lookup (in `bits`, `bitsenv` and
  `bitsStore`) and the `$BITS_REUSE_FROM` default of `--reuse-from` must be in the
  bits release that `bits.sh` builds.
- **Reuse reads the community's CVMFS modules tree** at the start of every build
  in its recipes, a cost that the opt-in flag paid only when asked for.
- **The community table is written by hand.** Reuse does not work yet for
  `alice` and `cms`: bits cannot expand the `{install_dir}` in alice.bits' modules
  template, and cms.bits declares no CVMFS layout, so their builds skip it with
  the warning. Generating the table from the bits-console
  `ui-config.yaml` files would keep it in step.
- **No bits-providers entry yet.** Without `bits.bits.sh` and a `registry.json`
  entry in bits-providers, `bits init bits.bits` and `BITS_ORGANISATION=BITS` do not
  work. A plain clone does.
- **`version: "0.6"` while the recipe builds `main`.** `bits --version` says 0.6
  whichever commit it was built from; set the version (and `tag:`) to a release
  once there is one.
- **`bits-python` pins its modules by hand.** Update the list with bits'
  `pyproject.toml`. The wheels come from PyPI without hash checking.
