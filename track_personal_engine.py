import math # Provides standard mathetmatical functions(trigonometry, logarithms, etc,)
import threading # Allows program to run multiple at the same time 
import time #time related functions 
import uuid # Generates unique identifiers for objects
from typing import Dict, List, Optional, Tuple # used for type hinting, which helps improve code readability and maintainability
from collections import deque # a memory-efficient list-like object that allows you to quiickly add or remove items from both ends. 
from dataclasses import dataclass # A shortcut tool to create custom data objects quickly.
from enum import Enum # lets you create a predefined set of constnts making your code readable and maintainable.


import cv2 # Open source vision libraray used to load videos and images manipulate pixels and detect objects. 
import numpy as np  # Opperate multi-dimensional arrays and matrics, along with a large collection of mathematical functiosn to operate on thesen arrays. 

Point = Tuple[int, int]
Box = Tuple[int, int, int, int]

class TrackState(Enum):
    unin = "UNINITIALIZED"
    act = "ACTIVE"
    lost = "LOST"

@dataclass (froxen=True)
class Constants:
    strike_approach_frame: int = 120
    trajectory_limit: int = 60
    lookback_seconds: float = 0.33
    min_lookback_frames: int = 2
    max_lookback_frames: int = 30
    min_forward_dx: float = 1.0
    depth_exponen: float = 1.5

@dataclass
class tshot:
    timestamp: float
    position: Point
    depth: Optional[float] = None 

def angleTan():
    pass

def shotclass():
    pass

def safe_ratio():
    pass
def screen_dy_positiive():
    pass

class perpsective_engine_correction:
    pass

class tracker_engine: 
    pass

class main_soccer_engine:
    pass