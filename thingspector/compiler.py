import os
from thingspector import utils
from thingspector.utils import Path


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

    def compile(self, outfile, *srcfiles, includepaths=None):
        raise NotImplemented()

    def __str__(self):
        return "%s %s (%s)" % (self.get_type(), self.version, self.executable)


class GccCompiler(Compiler):

    ENDS_WIDTH = "gcc" + utils.EXEC_EXTENSION

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

    def compile(self, outfile, *srcfiles, includepaths=[]):
        path_items = [self.executable]
        path_items.append("-o%s" % outfile)
        for incpath in includepaths:
            path_items.append("-I%s" % incpath)
        path_items += Path.to_strings(srcfiles)




COMPILERS = [
    GccCompiler.check_create
]


def find():

    found_compilers = []

    for p in os.environ['PATH'].split(os.pathsep):
        for f in os.listdir(p):
            fp = os.path.join(p, f)
            for c in COMPILERS:
                e = c(fp)
                if e is not None:
                    found_compilers.append(e)


    return found_compilers