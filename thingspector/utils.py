import subprocess
import os
import pycparser as cp
try:
    import pycparserext.ext_c_parser as ecp
    PARSER = ecp.GnuCParser
except _:
    PARSER = cp.CParser


IS_WINDOWS = os.name == 'nt'

EXEC_EXTENSION = ".exe" if IS_WINDOWS else ""
INCLUDE_ROOT = os.path.join(os.path.dirname(__file__), "includes")
INCLUDE_FAKE_LIB_C = os.path.join(INCLUDE_ROOT, "fake_libc")
INCLUDE_MUT = os.path.join(INCLUDE_ROOT, "thingspector")


def exec2str(*path_list):
    try:
        pipe = subprocess.Popen(path_list,
                                stdout=subprocess.PIPE,
                                universal_newlines=True)
        rv = pipe.communicate()[0]
        return rv, pipe.returncode
    except OSError as e:
        raise RuntimeError("Unable to invoke '%s'. Original error: %s" % (path_list[0], e))

def exec4iter(*path_list):
    pipe = subprocess.Popen(path_list,
                            stdout=subprocess.PIPE,
                            universal_newlines=True)
    for stdout_line in iter(pipe.stdout.readline, ""):
        yield stdout_line
    pipe.stdout.close()
    return_code = pipe.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, path_list)


def parse_c(file_to_parse, *pp_directives):
    pp_directives = ["-I"+INCLUDE_FAKE_LIB_C] + list(pp_directives)
    return cp.parse_file(file_to_parse, use_cpp=True, cpp_args=pp_directives, parser=PARSER())


class Path:
    """
        Lightweight path wrapper
    """

    def __init__(self, *path):
        self.path = os.path.join(*[str(p) for p in path])

    def __add__(self, other):
        p = Path(self.path)
        p.join(other)
        return p

    def is_file(self):
        """
        Check if it is a file which exists.
        """
        return os.path.isfile(self.path)

    def is_dir(self):
        """
        Check if it is a directory which exists.
        """
        return os.path.isdir(self.path)

    def __is_newer_or_older(self, *others, newer=False):
        others = [other.path if isinstance(other, Path) else other for other in others]

        self_t = os.path.getmtime(self.path)
        others_t = (os.path.getmtime(other) for other in others)

        if newer:

            for other_t in others_t:
                if other_t > self_t:
                    return False
            return True

        for other_t in others_t:
            if self_t < other_t:
                return True
        return False

    def is_newer(self, *others):
        """
            Check if this file is newer than all of the others.
        """

        return self.__is_newer_or_older(*others, newer=True)

    def is_older(self, *others):
        """
            Check if this file is older than any of the others.
        """

        return self.__is_newer_or_older(*others, newer=False)

    def mkdirs(self):
        """
            Makes all directories in this path which do not exist
        """

        os.makedirs(self.path)

    def join(self, other):
        """
            Joins all of them
        """

        if isinstance(other, Path):
            self.path = os.path.join(self.path, other.path)
        elif isinstance(other, str):
            self.path = os.path.join(self.path, other)
        elif isinstance(other, tuple):
            self.path = os.path.join(self.path, *(str(p) for p in other))
        else:
            raise ValueError("Can only add Path of str to Path or tuple of strings/Paths")

    def abs_str(self):
        """
            To absolute string path
        """

        return os.path.abspath(self.path)

    def __str__(self):
        return self.path

    def __repr__(self):
        return self.path

    @staticmethod
    def to_paths(strings):
        return [Path(s) for s in strings]

    @staticmethod
    def to_strings(paths):
        return [str(p) for p in paths]


class bc:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DARK = '\033[90m'
    UNDERLINE = '\033[4m'

class Log:
    """
        Lightweight logger.
    """

    TRACE, VERBOSE, INFO, WARNING, SEVERE = range(5)

    USE_ANSI_COLORS = True
    LOG_LEVEL = TRACE

    if USE_ANSI_COLORS:
        FORMATS = [bc.DARK + '[T] %s' + bc.ENDC, '[V] %s', bc.BOLD + '[I] %s' + bc.ENDC,
                   bc.WARNING + '[?] %s' + bc.ENDC, bc.FAIL + '[!] %s' + bc.ENDC]

    else:
        FORMATS = ['[T] %s', '[V] %s', '[I] %s', '[?] %s', '[!] %s']

    def __call__(self, level, msg, **params):
        if level < Log.LOG_LEVEL:
            return

        fmsg = msg % params
        print(Log.FORMATS[level] % fmsg)

    def trace(self, msg, **params):
        self(Log.TRACE, msg, **params)

    def verbose(self, msg, **params):
        self(Log.VERBOSE, msg, **params)

    def info(self, msg, **params):
        self(Log.INFO, msg, **params)

    def warning(self, msg, **params):
        self(Log.WARNING, msg, **params)

    def severe(self, msg, **params):
        self(Log.SEVERE, msg, **params)


log = Log()

