import sys
from pmo.syntax import Project


def entrypoint():
    target = sys.argv[-1]
    lines = open(target).read().splitlines()
    project = Project(lines)
    project.report()
