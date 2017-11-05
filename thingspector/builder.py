import os
from thingspector import utils
from thingspector.utils import log
from thingspector.utils import Path
from thingspector.utils import log
import yaml
import uuid

import pycparser as cp
try:
    import pycparserext.ext_c_parser as ecp
    PARSER = ecp.GnuCParser
except _:
    PARSER = cp.CParser


IS_WINDOWS = os.name == 'nt'

EXEC_EXTENSION = ".exe" if IS_WINDOWS else ""
INCLUDE_ROOT = Path(os.path.dirname(__file__), "includes")
INCLUDE_FAKE_LIB_C = INCLUDE_ROOT + "fake_libc"
INCLUDE_TS = INCLUDE_ROOT + "thingspector"

class Compiler:
    """
        Class responsible for executing a compiler.
    """
    def __init__(self, executable, version):
        self.executable = executable
        self.version = version

    @staticmethod
    def check_create(path):
        """
        Checks and creates (if it is), a new Compiler instance.
        :param path:    The path
        :return:        A compiler instance, if it is.
        """
        raise NotImplemented()

    def get_type(self):
        raise NotImplemented()

    def compile_all(self, outfile, *srcfiles, includepaths=None):
        raise NotImplemented()

    def __str__(self):
        return "%s %s (%s)" % (self.get_type(), self.version, self.executable)


class GccCompiler(Compiler):

    ENDS_WIDTH = "gcc" + EXEC_EXTENSION

    def __init__(self, executable, version):
        super(GccCompiler, self).__init__(executable, version)

    @staticmethod
    def check_create(path):
        # GCC compiler always ends with gcc[.exe]

        if not path.endswith(GccCompiler.ENDS_WIDTH):
            return None

        # TODO: Check if it is not a cross-compiler
        try:
            version, _ = utils.exec2str(path, "--version")
            version = version.split("\n")[0]
            i = version.rfind(' ')
            if i > 0:
                version = version[i+1:]
        except Exception as e:
            print(e)
            return None

        if version is None:
            return None

        return GccCompiler(path, version)

    def get_type(self):
        return "GCC"

    def compile_all(self, outfile, *srcfiles, includepaths=[]):
        log.verbose("Compiling %(outfile)s from %(sources)s", outfile=outfile, sources=srcfiles)
        path_items = [self.executable]

        path_items.append("-o%s" % outfile)
        for incpath in includepaths:
            path_items.append("-I%s" % incpath)
        path_items += Path.to_strings(srcfiles)
        output, _ = utils.exec2str(*path_items)

    def __make_path_items(self, flags=[], infiles=[], outfile=None, include_path=[], symbols={}):
        path_items = [self.executable]

        for incpath in include_path:
            path_items.append("-I%s" % incpath)

        for symbol, value in symbols.items():
            if value is not None:
                path_items.append("-D%s=%s" % (symbol, value))
            else:
                path_items.append("-D%s" % symbol)

        if outfile:
            path_items.append("-o")
            path_items.append(outfile.abs_str())

        for flag in flags:
            path_items.append(flag)

        for infile in infiles:
            path_items.append(infile.abs_str())

        # print("Executing: " + " ".join(path_items))
        return path_items

    def compile(self, srcfile, outfile, include_path=[], symbols={}):
        log.verbose("Compiling %(outfile)s from %(srcfile)s", outfile=outfile, srcfile=srcfile)
        path_items = self.__make_path_items(["-c"], [srcfile], outfile, include_path, symbols)
        output, _ = utils.exec2str(*path_items)

    def link(self, binfile, *objfiles):
        log.verbose("Linking %(binfile)s from %(objfiles)s", binfile=binfile, objfiles=", ".join(str(x) for x in objfiles))
        path_items = self.__make_path_items(infiles=objfiles, outfile=binfile)
        output, _ = utils.exec2str(*path_items)

    def dependencies(self, srcfile, include_path=[], symbols={}):
        log.verbose("Dependencies for %(srcfile)s", srcfile=srcfile)

        path_items = self.__make_path_items(flags=['-E', '-Wp,-MM'], infiles=[srcfile], include_path=include_path, symbols=symbols)

        output, _ = utils.exec2str(*path_items)
        deps = " ".join([l[0:-1].strip() if l.endswith("\\") else l.strip() for l in output.split("\n")[1:]]).split()
        deps = [Path(dep) for dep in deps]
        return deps

    def preprocess(self, srcfile, outfile, include_path=[], symbols={}):
        log.verbose("Preprocessing for %(srcfile)s", srcfile=srcfile)
        path_items = self.__make_path_items(["-E"], [srcfile], outfile, include_path, symbols)
        output, _ = utils.exec2str(*path_items)


COMPILER_DISCOVERY = [
    GccCompiler.check_create
]


def find_compilers():
    """
        Finds compilers on path.
    """

    found_compilers = []

    for p in os.environ['PATH'].split(os.pathsep):
        if len(p.strip()) == 0:
            continue
        for f in os.listdir(p):
            fp = os.path.join(p, f)

            for c in COMPILER_DISCOVERY:
                e = c(fp)
                if e is not None:
                    found_compilers.append(e)

    return found_compilers

FOUND_COMPILERS = find_compilers()




class Build:
    """
        The builder keeps track of builds. It produces the said binary file.
    """

    def __init__(self, binfile, workdir, compiler=None):
        self.binfile = binfile
        self.cachefile = binfile.extend(".cache")
        self.srcfiles = set()
        self.workdir = workdir

        if compiler is None:
            if len(FOUND_COMPILERS) == 0:
                raise RuntimeError("No compiler!")
            compiler = FOUND_COMPILERS[0]

        self.compiler = compiler

        self.src2id = {}
        self.src2deps = {}
        self.symbols = {}
        self.incpath = set()
        self.__load_cache()

    def add_inc_path(self, *incpath):
        self.incpath.update(incpath)

    def add_symbol(self, name, value=None):
        self.symbols[name] = value

    def add_src(self, *srcfiles):

        for srcfile in srcfiles:
            self.srcfiles.add(srcfile)

            # Since we do not trust filenames, we'll just use UUIDs for all temporary products.
            if srcfile not in self.src2id:
                self.src2id[srcfile] = uuid.uuid4().hex
                self.src2deps[srcfile] = None

        self.__save_cache()

    def __save_cache(self):
        cache = {
            "ids": self.src2id,
            "deps": self.src2deps
        }

        with self.cachefile.open("w") as stream:
            yaml.dump(cache, stream, default_flow_style=False)


    def __load_cache(self):
        if not self.cachefile.is_file():
            return

        with self.cachefile.open("r") as stream:
            cache = yaml.load(stream)

        self.src2id = cache['ids']
        self.src2deps = cache['deps']

    def __get_tmp_file(self, srcfile, ext):
        uid = self.src2id[srcfile]
        return self.workdir + ("%s.%s" % (uid, ext))

    def __get_deps(self, src):
        return self.compiler.dependencies(src, include_path=self.incpath)

    def __compile(self, srcfile, incremental=True):

        if srcfile not in self.srcfiles:
            raise RuntimeError("Build does not known '%s'", srcfile)

        deps = self.src2deps[srcfile]

        objfile = self.__get_tmp_file(srcfile, "o")

        if incremental and deps is not None and objfile.is_newer(*deps, srcfile):
            return objfile

        deps = self.__get_deps(srcfile)
        self.src2deps[srcfile] = deps
        self.__save_cache()
        self.compiler.compile(srcfile, objfile, include_path=self.incpath, symbols=self.symbols)

        return objfile

    def preprocess(self, srcfile, use_fake_libc=True):
        """
        Preprocess the provided source file
        :param srcfile:
        :return:
        """

        ppfile = self.__get_tmp_file(srcfile, "pp")
        deps = self.src2deps[srcfile]

        if deps is not None and ppfile.is_newer(*deps, srcfile):
            return ppfile

        deps = self.__get_deps(srcfile)
        self.src2deps[srcfile] = deps
        self.__save_cache()

        includes = [Path(INCLUDE_FAKE_LIB_C)] + list(self.incpath) if use_fake_libc else self.incpath

        self.compiler.preprocess(srcfile, ppfile, include_path=includes, symbols=self.symbols)
        return ppfile

    def parse(self, srcfile):
        ppfile = self.preprocess(srcfile)
        return cp.parse_file(ppfile.abs_str(), use_cpp=False,  parser=PARSER())

    def compile_all(self, incremental=True):
        objfiles = []
        for srcfile in self.srcfiles:
            objfiles.append(self.__compile(srcfile, incremental))

        if self.binfile.is_older(*objfiles):
            self.compiler.link(self.binfile, *objfiles)
