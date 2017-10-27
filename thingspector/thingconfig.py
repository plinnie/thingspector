import yaml
from thingspector.utils import Path
from thingspector import utils


class TestConfig:
    """
        Representation of a Test (module) config.
    """

    def __init__(self, p, name, yaml_section):
        self.p = p
        self.name = name
        self.target = yaml_section.get("target", name + ".c")
        # Module Under Test directory


        # Copy source directories
        self.srcdirs = Path.to_paths(yaml_section.get("srcdirs", [])) + p.srcdirs
        self.incdirs = Path.to_paths(yaml_section.get("incdirs", [])) + p.incdirs
        # Mut headers should always be added
        self.incdirs += [Path(utils.INCLUDE_MUT)]

        if self.target.endswith(".c"):
            header_guess = [self.target[:-2]+".h"]
        else:
            header_guess = []

        self.headers = yaml_section.get("headers", header_guess) + p.headers

        self.testsrc = Path(self.p.testdir, "test_%s.c" % self.name)
        self.runnersrc = Path(self.p.workdir, "runner_%s.c" % self.name)
        self.testbin = Path(self.p.workdir, "test_%s%s" % (self.name, utils.EXEC_EXTENSION))

        # print("Module %s, target=%s" % (name, self.target))


class ThingConfig:
    """
        Representation of a Thingspector Yaml file
    """

    __TEST_KEY = "test "

    def __init__(self, filename="inspect.yaml"):
        self.__load_file(filename)

    def __load_file(self, filename):
        with open(filename, "r") as stream:
            y = yaml.load(stream, Loader=yaml.CLoader)

        self.srcdirs = Path.to_paths(y.get('srcdirs', ['.']))
        self.incdirs = Path.to_paths(y.get('incdirs', ['.']))
        self.headers = Path.to_paths(y.get('headers', []))
        self.tests = {}
        self.dir = Path(y.get('testdir', 'inspect'))
        self.testdir = Path(self.dir, 'tests')
        self.workdir = self.dir + '.work'

        for key in y:
            if key.startswith(ThingConfig.__TEST_KEY):
                name = key[len(ThingConfig.__TEST_KEY):].strip()
                self.tests[name] = TestConfig(self, name, y[key])
