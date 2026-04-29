from enum import IntEnum


class State(IntEnum):
    DAY_MENU = 0
    EXERCISE_INTRO = 1
    SET_IN_PROGRESS = 2
    RESTING = 3
    WORKOUT_DONE = 4
    STATS_VIEW = 5
    PROG_MENU = 6
    PROG_SELECT_DAY = 7
    PROG_SELECT_EX = 8
    PROG_INPUT_ONE = 9
    PROG_INPUT_ALL = 10
