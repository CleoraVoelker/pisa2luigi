#!/usr/bin/env python3
from enum import IntEnum

class TaskStatus(IntEnum):
    DONE = 0
    IDLE = 1
    PROCESSING = 2
    FAILED = 3
class task:  # add / remove all the necessary parameters for a task
    def __init__(self, exe: str, args: str, w_dir: str, env: str, out: str, err: str):
        self.cmd = str(exe) + str(args)
        self.w_dir = w_dir
        self.env = env
        self.out = out
        self.err = err
        self.status:TaskStatus = TaskStatus.IDLE

    def enumerate(self, num: int) -> None:
        self.num = num

    def __repr__(self):  # print the tasks in case of a dry run
        return f"Task {'' if not hasattr(self, 'num') else self.num}: {self.cmd}; WDIR={self.w_dir}; ENV={self.env}; OUT={self.out}; ERR={self.err}"


class enumerator:
    def __init__(self) -> None:
        self.value = 0

    def next(self) -> int:
        old_value = self.value
        self.value += 1
        return old_value
