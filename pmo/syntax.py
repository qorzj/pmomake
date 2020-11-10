from datetime import datetime as Datetime
from typing import List, Optional, Union, NamedTuple, Dict
from pmo.estimate_time import EstimateTime, EstimateTimeTopic
from pmo.syntax_util import split_into_blocks, starts_with_blank, is_milestone, promise_core, is_promise, is_date, is_unknown_time, is_estimate_time
from pmo.datetime_util import IDatetime


class PmoSyntaxError(Exception):
    reason: str
    line_no: int

    def __init__(self, reason: str, line_no: int=0):
        self.reason = reason
        self.line_no = line_no

    def __str__(self):
        return f'Line {self.line_no+1}: {self.reason}'


class PmoGrammerError(Exception):
    reason: str

    def __init__(self, reason: str):
        self.reason = reason

    def __str__(self):
        return f'Error: {self.reason}'


class MilestoneKey(NamedTuple):
    name: str
    promise: bool

    def __str__(self) -> str:
        return f'promise[{self.name}]' if self.promise else self.name


class Project:
    blocks: List['Block']
    milestone_index: Dict[MilestoneKey, 'Milestone']
    block_index: Dict[MilestoneKey, 'Block']

    def __init__(self, lines: List[str]) -> None:
        self.milestone_index = {}
        self.block_index = {}
        for start_line_no, end_line_no in split_into_blocks(lines):
            try:
                block = Block(lines[start_line_no: end_line_no])
                self.blocks.append(block)
                self.block_index[block.dependence_line.milestone.key] = block
            except PmoSyntaxError as e:
                e.line_no += start_line_no
                print(e)
                exit(1)

    def report(self) -> None:
        milestones = list(m for m in self.milestone_index.values() if m.done_date is None)
        milestones.sort(key = lambda m: str(m.will_finish), reverse=True)
        deadline_error = False
        for milestone in milestones:
            safe_sign: str
            if milestone.due_date and milestone.will_finish and milestone.will_finish <= milestone.due_date:
                safe_sign = '✓'
            else:
                safe_sign, deadline_error = '✗', True
            will_finish_str = str(milestone.will_finish.date()) if milestone.will_finish else ' ' * len('2000-01-01')
            due_date_str = str(milestone.due_date.date()) if milestone.due_date else ' ' * len('2000-01-01')
            print(f'{safe_sign}  {will_finish_str} < {milestone} < {due_date_str}')
        total = len(self.milestone_index)
        undone_count = len(milestones)
        if deadline_error:
            print(f'✗  {total - undone_count}/{total} milestones done.')
            exit(1)
        else:
            print(f'✓  {total - undone_count}/{total} milestones done.')

    def dfs_milestones(self) -> None:
        """
        从第一个block的milestone开始，计算所有milestone的预估完成时间
        """
        if not self.blocks:
            raise PmoGrammerError('至少需要一个milestone')
        milestone: Milestone = self.blocks[0].dependence_line.milestone
        try:
            self.dfs(milestone.key)
        except PmoGrammerError as e:
            print(e)
            exit(0)

    def dfs(self, milestone_key: 'MilestoneKey') -> Optional['Milestone']:
        """
        计算milestone的预估完成时间，并且更新到milestone_index
        """
        if milestone_key not in self.blocks:
            return None
        if milestone_key in self.milestone_index:
            return self.milestone_index[milestone_key]
        all_dependence_done = True
        all_dependence_will_finish = True
        will_finish: Datetime = Datetime(1970, 1, 1, 0, 0, 0)
        block = self.block_index[milestone_key]
        for dependence_key in block.dependence_line.dependences:
            if isinstance(dependence_key, Datetime):
                will_finish = max(will_finish, dependence_key)
            else:
                dependence: Optional[Milestone] = self.dfs(dependence_key)
                if dependence is None:
                    raise PmoGrammerError(f'{dependence_key}的依赖项未定义!')
                if dependence.done_date is None:
                    all_dependence_done = False
                if dependence.will_finish is None:
                    all_dependence_will_finish = False
                else:
                    will_finish = max(will_finish, dependence.will_finish)
        # 依赖项没有预估完成时间 -> will_finish=None
        # 预估时长为.estimate & all_dependence_done -> 语法异常
        # 预估时长为.unknown & promise未完成 -> will_finish=None
        # 预估时长为.unknown & promise已完成 -> 语法异常
        # 预估时长为.unknown & promise=None -> 语法异常
        # 其他 -> will_finish += 总预估时长
        total_minute = 0
        if not all_dependence_will_finish:
            total_minute = 99999999
        for estimate_line in block.estimate_lines:
            estimate_time: 'EstimateTime' = estimate_line.estimate_time
            estimate_time_topic = estimate_time.topic()
            if estimate_time_topic == EstimateTimeTopic.estimate:
                if all_dependence_done:
                    raise PmoGrammerError(f'{milestone_key}：所有依赖项已完成，预估时长必须确定，不能是区间!')
                best_minutes, _ = estimate_time.payload(estimate_time_topic)
                total_minute += best_minutes
            elif estimate_time_topic == EstimateTimeTopic.unknown and not milestone_key.promise:
                promise_milestone: Optional['Milestone'] = self.dfs(MilestoneKey(milestone_key.name, promise=True))
                if promise_milestone is None:
                    raise PmoGrammerError(f'{milestone_key}：预估时长unknown，并且没有promise!' )
                elif promise_milestone.done_date is not None:
                    raise PmoGrammerError(f'{milestone_key}：promise已完成，预估时长必须确定!' )
                else:
                    total_minute = 99999999
            elif estimate_time_topic == EstimateTimeTopic.unknown:
                raise PmoGrammerError(f'{milestone_key}：promise里程碑的预估时长必须确定!')
            elif estimate_time_topic == EstimateTimeTopic.duration:
                total_minute += estimate_time.payload(estimate_time_topic)
            else:
                raise NotImplementedError
        milestone: Milestone = block.dependence_line.milestone
        if will_finish.year == 1970 or total_minute >= 99999999:
            milestone.will_finish = None
        else:
            milestone.will_finish = IDatetime.add(will_finish, minutes=total_minute)
        # 更新到milestone_index
        self.milestone_index[milestone_key] = milestone
        return milestone


class Block:
    dependence_line: 'DependenceLine'
    estimate_lines: List['EstimateLine']

    def __init__(self, lines: List[str]):
        if starts_with_blank(lines[0]):
            raise PmoSyntaxError('依赖定义行不能有缩进')
        self.dependence_line = DependenceLine(lines[0].strip())
        self.estimate_lines = []
        for line in lines[1:]:
            if not starts_with_blank(line):
                raise PmoSyntaxError('预估时长行需要有缩进')
            self.estimate_lines.append(EstimateLine(line.strip()))


class DependenceLine:
    milestone: 'Milestone'
    dependences: List[Union['MilestoneKey', Datetime]]

    def __init__(self, line: str) -> None:
        milestone_part, dependence_part = line.split(':', 1)
        self.milestone = Milestone(milestone_part.strip())
        self.dependences = []
        for dependence_word in dependence_part.strip().split():
            if is_date(dependence_word):
                self.dependences.append(IDatetime.noon_of_str(dependence_word))
            elif is_milestone(dependence_word):
                self.dependences.append(MilestoneKey(name=dependence_word, promise=False))
            elif is_promise(dependence_word):
                self.dependences.append(MilestoneKey(name=dependence_word, promise=True))
            else:
                raise PmoSyntaxError(f"依赖项({dependence_word})不合法")


class EstimateLine:
    work: str
    estimate_time: 'EstimateTime'

    def __init__(self, line: str) -> None:
        work_part, est_word = line.split('=', 1)
        self.work = work_part
        est_word = est_word.strip()
        if is_estimate_time(est_word):
            self.estimate_time = EstimateTime(EstimateTimeTopic.duration, IDatetime.minute_of_str(est_word))
        elif is_unknown_time(est_word):
            self.estimate_time = EstimateTime(EstimateTimeTopic.unknown)
        elif est_word.count('~') == 1:
            first_seg, second_seg = est_word.split('~', 1)
            if is_estimate_time(first_seg) and is_estimate_time(second_seg):
                self.estimate_time = EstimateTime(EstimateTimeTopic.estimate, (IDatetime.minute_of_str(first_seg), IDatetime.minute_of_str(second_seg)))
            else:
                raise PmoSyntaxError(f"预估时长({est_word})不合法")
        else:
            raise PmoSyntaxError(f"预估时长({est_word})不合法")


class Milestone:
    name: str
    promise: bool
    will_finish: Optional[Datetime]  # 预估完成时间(乐观)
    due_date: Optional[Datetime]
    done_date: Optional[Datetime]

    def __init__(self, word: str) -> None:
        self.will_finish = None
        self.due_date = None
        self.done_date = None
        if '=' in word:
            name_part, date_part = word.split('=', 1)
            date_part = date_part.strip()
            if not is_date(date_part):
                raise PmoSyntaxError(f"完成日期({date_part})不合法")
            self.done_date = IDatetime.noon_of_str(date_part)
        elif '<' in word:
            name_part, date_part = word.split('<', 1)
            date_part = date_part.strip()
            if not is_date(date_part):
                raise PmoSyntaxError(f"Deadline日期({date_part})不合法")
            self.due_date = IDatetime.noon_of_str(date_part.strip())
        else:
            name_part = word
        name_part = name_part.strip()
        if is_promise(name_part):
            self.name = promise_core(name_part)
            self.promise = True
        elif is_milestone(name_part):
            self.name = name_part
            self.promise = False
        else:
            raise PmoSyntaxError(f"依赖项({name_part})不合法")


    @property
    def key(self) -> MilestoneKey:
        return MilestoneKey(name=self.name, promise=self.promise)
