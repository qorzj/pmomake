import sys
from pmo.syntax import Project
from pmo.syntax_util import clear_comment


def entrypoint():
    target = sys.argv[-1]
    lines = open(target).read().splitlines()
    lines_without_comment = [x for x in clear_comment(lines)]
    project = Project(lines_without_comment)
    project.dfs_milestones()
    project.report()
