from enum import Enum, auto
from typing import Union, overload, Literal, Tuple


class EstimateTimeTopic(Enum):
    unknown = auto()  # None
    duration = auto()  # int, 单位：分钟
    estimate = auto()  # (int, int) 单位：分钟


estimate_time_topic_literal_t = Literal[EstimateTimeTopic.unknown, EstimateTimeTopic.duration, EstimateTimeTopic.estimate]

estimate_time_msg_t = Union[
    Tuple[Literal[EstimateTimeTopic.unknown], None],
    Tuple[Literal[EstimateTimeTopic.duration], int],
    Tuple[Literal[EstimateTimeTopic.estimate], Tuple[int, int]],
]


class EstimateTime:
    message: estimate_time_msg_t

    @overload
    def __init__(self, topic: Literal[EstimateTimeTopic.unknown]) -> None: ...
    @overload
    def __init__(self, topic: Literal[EstimateTimeTopic.duration], payload: int) -> None: ...
    @overload
    def __init__(self, topic: Literal[EstimateTimeTopic.estimate], payload: Tuple[int, int]) -> None: ...

    def __init__(self, topic, payload=None):
        self.message = topic, payload

    def topic(self) -> estimate_time_topic_literal_t:
        return self.message[0]

    @overload
    def payload(self, topic: Literal[EstimateTimeTopic.unknown]) -> None: ...
    @overload
    def payload(self, topic: Literal[EstimateTimeTopic.duration]) -> int: ...
    @overload
    def payload(self, topic: Literal[EstimateTimeTopic.estimate]) -> Tuple[int, int]: ...

    def payload(self, topic):
        return self.message[1]
