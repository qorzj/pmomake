from typing import List, Iterator, NamedTuple
from datetime import date as Date
import re


def clear_comment(lines: List[str]) -> Iterator[str]:
    for line in lines:
        if '#' in line:
            yield line.split('#', 1)[0]
        else:
            yield line


class block_tuple_t(NamedTuple):
    start_line_no: int
    end_line_no: int


def split_into_blocks(lines: List[str]) -> Iterator[block_tuple_t]:
    """
    按空行将lines分隔成若干个block
    """
    start_line_no = -1
    end_line_no = -1
    for cur_line_no in range(0, len(lines)):
        line = lines[cur_line_no]
        if not line:
            if start_line_no == -1:
                pass
            else:
                yield block_tuple_t(start_line_no, end_line_no)
                start_line_no = end_line_no = -1
        else:
            if start_line_no == -1:
                start_line_no = cur_line_no
                end_line_no = cur_line_no + 1
            else:
                end_line_no += 1
    if start_line_no != -1:
        yield block_tuple_t(start_line_no, end_line_no)


def starts_with_blank(line: str):
    return line.startswith(' ') or line.startswith('\t')


def is_milestone(word: str) -> bool:
    return re.match(r'^[^=<>,;:~\[\]#(){}]+$', word) is not None


def promise_core(word: str) -> str:
    return word[8:-1]


def is_promise(word: str) -> bool:
    return word.startswith('promise[') and word.endswith(']') \
           and is_milestone(promise_core(word))


def is_date(word: str) -> bool:
    try:
        return bool(Date.fromisoformat(word))
    except:
        return False


def is_unknown_time(word: str) -> bool:
    return re.match(r'^\?+$', word) is not None


def is_estimate_time(word: str) -> bool:
    if re.match(r'^\d+(\.5)?d$', word):
        return True
    if re.match(r'^\d+h$', word):
        return True
    if word == '0':
        return True
    return False
