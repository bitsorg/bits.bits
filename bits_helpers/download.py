try:
    from md5 import new as md5adder
except ImportError:
    from hashlib import md5 as md5adder
from os.path import abspath, join, exists, dirname, basename
from os import rename, unlink
import re
from tempfile import mkdtemp
from subprocess import getstatusoutput
from urllib.request import urlopen, Request
from urllib.error import URLError
import base64
from time import time
from types import SimpleNamespace
from bits_helpers.log import error, warning, debug

urlRe = re.compile(r".*:.*/.*")
urlAuthRe = re.compile(r'^(http(s|)://)([^:]+:[^@]+)@(.+)$')

def format(s, **kwds):
    return s % kwds

def executeWithErrorCheck(command, errorMessage):
    debug(command)
    error, output = getstatusoutput(command)
    if error:
        warning(errorMessage + ":")
        warning("")
        warning(command)
        warning("")
        warning("resulted in:")
        warning(output)
        return False
    debug(output)
    return True


def packCheckout(tempdir, dest, *exports):
    """ Use this helper method when download protocol is like cvs/svn/git
        where the code is checked out in a temporary directory and then tarred
        up.
    """
    export = " ".join(['"%s"' % x for x in exports])
    packCommand = """cd %(tempdir)s; tar -zcf "%(dest)s" %(export)s """
    packCommand = packCommand % locals()
    errorMessage = "Error while creating a tar archive for checked out area"
    return executeWithErrorCheck(packCommand, errorMessage)

# We have our own version rather than using the one from os
# because the latter does not work seem to be thread safe.
def makedirs(path):
    returncode, out = getstatusoutput("mkdir -p %s" % (path,))
    if returncode != 0:
        raise OSError("makedirs() failed (return: %s):\n%s" % (returncode, out))

def downloadUrllib2(source, destDir, work_dir):
    try:
        dest = "/".join([destDir.rstrip("/"), basename(source)])
        headers={"Cache-Control": "no-cache"}
        m = urlAuthRe.match(source)
        if m:
            source = m.group(1)+m.group(4)
            headers['Authorization'] = "Basic %s" % base64.b64encode(m.group(3))
        req = Request(source, headers=headers)
        s = urlopen(req)
        tmpfile = "%s.%f.tmp" % (dest, time())
        f = open(tmpfile, "wb")
        # Read in blocks to avoid using too much memory.
        block_sz = 8192 * 16
        while True:
            buffer = s.read(block_sz)
            if not buffer:
                break
            f.write(buffer)
        f.close()
        if not exists(dest):
            rename(tmpfile, dest)
        else:
            unlink(tmpfile)
    except URLError as e:
        debug("Error while downloading %s: %s" % (source, e))
        return False
    except Exception as e:
        debug("Error while downloading %s: %s" % (source, e))
        return False
    return True

# Download a files from a git url.  We do not clone the remote reposiotory, but
# we simply pull the branch we are interested in and then we drop all the git
# information while creating a tarball.  The syntax to define a repository is
# the following:
#
# git:/local/repository?obj=BRANCH/TAG
# git://remote-repository?obj=BRANCH/TAG
# git+https://remote-repository-over-http/foo.git?obj=BRANCH/TAG
#
# If "obj" does not contain a "/", it's value will be considered a branch and TAG will be "HEAD".
# If "obj" is not specified, it will be "master/HEAD" by default.
# By default export is the <basename of the url without ".git">-TAG unless it is HEAD,
# in which case it will be  <basename of the url without .git>-BRANCH.
# One can specify an additional parameter
#
#     filter=<some-path>
#
# which will be used to pack only a subset of the checkout.

def downloadGit(source, dest, work_dir):
    protocol, gitroot, args = parseGitUrl(source)
    tempdir = createTempDir(work_dir, "tmp")

    exportpath = join(tempdir, args["export"])
    if protocol=="git": protocol="https"
    if protocol:
        protocol += "://"
    if not protocol and not gitroot.endswith(".git"):
        gitroot = join(gitroot, ".git")

    dest = join(dest, args["output"].lstrip("/"))
    args.update({"protocol": protocol, "tempdir": tempdir,
                 "gitroot": gitroot, "dest": dest,
                 "exportpath": exportpath})
    makedirs(exportpath)
    if "submodules" in args:
        args["submodules"] = " git submodule update --recursive --init &&"
    else:
        args["submodules"] = ""
    command = format("cd %(exportpath)s &&"
                     "git init &&"
                     "git pull --tags %(protocol)s%(gitroot)s refs/heads/%(branch)s &&"
                     "git reset --hard %(tag)s && %(submodules)s"
                     "find . ! -path '%(filter)s' -delete &&"
                     "rm -rf .git .gitattributes .gitignore", **args)
    error, output = getstatusoutput(command % args)
    if error:
        warning("Error while downloading sources from %s using git.\n\n"
            "%s\n\n"
            "resulted in:\n%s" % (gitroot, command % args, output))
        return False
    return packCheckout(args["tempdir"], args["dest"], args["export"])


def parseGitUrl(url):
    protocol, gitroot, args = parseUrl(url, requestedKind="git",
                                       defaults={"obj": "master/HEAD"})
    parts = args["obj"].rsplit("/", 1)
    if len(parts) != 2:
        parts += ["HEAD"]
    args["branch"], args["tag"] = parts

    if not "export" in args:
        args["export"] = basename(re.sub(r"\.git$", "", re.sub(r"[?].*", "", gitroot)))
        if args["tag"] != "HEAD":
            args["export"] += args["tag"]
        else:
            args["export"] += args["branch"]

    if not "output" in args:
        args["output"] = args["export"] + ".tar.gz"
        args["gitroot"] = gitroot
    if not "filter" in args:
        args["filter"] = "*"
    args["filter"] = sanitize(args["filter"])
    return protocol, gitroot, args


downloadHandlers = {
                    'http': downloadUrllib2,
                    'https': downloadUrllib2,
                    'ftp': downloadUrllib2,
                    'ftps': downloadUrllib2,
                    'git': downloadGit}



def createTempDir(workDir, subDir):
    tempdir = join(workDir, subDir)
    if not exists(tempdir):
        makedirs(tempdir)
    tempdir = mkdtemp(dir=tempdir)
    return tempdir

# Minimal string sanitization.
def sanitize(s):
    return re.sub(r"[^a-zA-Z_0-9*./-]", "", s)

def getUrlChecksum(s):
    m = md5adder(fixUrl(s).encode())
    return m.hexdigest()

def parseUrl(url, requestedKind=None, defaults={}, required=[]):
    match = re.match("([^+:]*)([^:]*)://([^?]*)(.*)", url)
    if not match:
        raise MalformedUrl(url)
    parts = match.groups()
    protocol, deliveryProtocol, server, arguments = match.groups()
    arguments = arguments.strip("?")
    # In case of urls of the kind:
    # git+https://some.web.git.repository.net
    # we consider "https" the actual protocol and
    # "git" merely the request kind.
    if requestedKind and not protocol == requestedKind:
        raise MalformedUrl(url)
    if deliveryProtocol:
        protocol = deliveryProtocol.strip("+")
    arguments.replace("&amp;", "&")
    args = list(defaults.items())
    parsedArgs = re.split("&", arguments)
    parsedArgs = [x.split("=") for x in parsedArgs]
    parsedArgs = [(len(x) != 2 and [x[0], True]) or x for x in parsedArgs]
    args.extend(parsedArgs)
    argsDict = dict(args)
    missingArgs = [arg for arg in required if arg not in argsDict]
    if missingArgs:
        raise MalformedUrl(url, missingArgs)
    return protocol, server, argsDict

def fixUrl(s):
    for x in ['no-cmssdt-cache=1', 'cmdist-generated=1']:
        if x in s:
            s = s.replace(x,'').replace("&&","&").replace("?&","?")
            if s.endswith('&'): s=s[:-1]
            if s.endswith('?'): s=s[:-1]
    return s

def download(source, dest, work_dir):
    noCmssdtCache = True if 'no-cmssdt-cache=1' in source else False
    isCmsdistGenerated = True if 'cmdist-generated=1' in source else False
    source = fixUrl(source)
    checksum = getUrlChecksum(source)

    # Syntactic sugar to allow the following urls for tag collector:
    #
    # cmstc:[base.]release[.tagset[.tagset[...]]]/src.tar.gz
    #
    # in place of:
    #
    # cmstc://?tag=release&baserel=base&extratag=tagset1,tagset2,..&module=CMSSW&export=src&output=/src.tar.gz
    if source.startswith("cmstc:") and not source.startswith("cmstc://"):
        url = source.split(":", 1)[1]
        desc, output = url.rsplit("/", 1)
        parts = desc.split(".")
        releases = [x for x in parts if not x.isdigit()]
        extratags = [x for x in parts if x.isdigit()]
        if extratags:
            extratags = "&extratags=" + ",".join(extratags)
        if len(releases) == 1:
            baserel = ""
            release = "tag=" + releases[0]
        elif len(releases) == 2:
            baserel = "&baserel=" + releases[0]
            release = releases[1]
        else:
            raise MalformedUrl(source)
        source = "cmstc://?%s%s%s&module=CMSSW&export=src&output=/%s" % (release, baserel, extratags, output)

    cacheDir = abspath(join(work_dir, "SOURCES/cache"))
    urlTypeRe = re.compile(r"([^:+]*)([^:]*)://.*")
    match = urlTypeRe.match(source)
    if not urlTypeRe.match(source):
        raise MalformedUrl(source)
    downloadHandler = downloadHandlers[match.group(1)]
    filename = source.rsplit("/", 1)[1]
    downloadDir = join(cacheDir, checksum[0:2], checksum)
    try:
        makedirs(downloadDir)
    except OSError as e:
        if not exists(downloadDir):
            raise downloadDir

    realFile = join(downloadDir, filename)
    if not exists(realFile):
        debug ("Trying to fetch source file: %s" % source)
        downloadHandler(source, downloadDir, work_dir)

    if exists(realFile):
        executeWithErrorCheck("mkdir -p {dest}; cp {src} {dest}/".format(dest=dest, src=realFile), "Failed to move source")
    else:
        raise downloadDir
    return
