import sys
from pmo.syntax import Project
from pmo.syntax_util import clear_comment
from pmo.datetime_util import IDatetime


def print_help():
    help_text = """Usage: pmomake [options] [target]
Options:
  --predict[=?d|?h]        预警时间，默认为0d
  --day[=?h]               一天工作日包含多少工作小时，默认为4h
  --exclude[=DATE]         排除的日期，DATE支持2020-10-01,2020-10-02这样的日期
  --include[=DATE]         包含的日期
  --bot[=string]           企业微信机器人key
"""
    print(help_text)


def parse_options():
    if len(sys.argv) <= 1 or '--help' in sys.argv or '-h' in sys.argv:
        print_help()
        exit(0)
    option_segs = sys.argv[1:-1]
    options = {}
    for seg in option_segs:
        if '=' not in seg or not seg.startswith('--'):
            print('错误的参数：' + seg)
            exit(1)
        alice, bob = seg.split('=', 1)
        options[alice.lstrip('-')] = bob
    return options


def entrypoint():
    options = parse_options()
    IDatetime.load_options(options)
    target = sys.argv[-1]
    lines = open(target).read().splitlines()
    lines_without_comment = [x for x in clear_comment(lines)]
    project = Project(lines_without_comment)
    project.dfs_milestones()
    bot_key = options.get('bot')
    project.report(bot_key)
