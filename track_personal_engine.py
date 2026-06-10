import math # Provides standard mathetmatical functions(trigonometry, logarithms, etc,)
import threading # Allows program to run multiple at the same time 
import time #time related functions 
import uuid # Generates unique identifiers for objects
from typing import Deque, Optional, Tuple # used for type hinting, which helps improve code readability and maintainability
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
    depth_exponent: float = 1.5
    velocity_outlier: float = 120.0
    math_epsilon: float = 1e-6
    window_title: str = "Shot-cord"
    selection_window: str = "Select" 
    ball_color: Tuple[int, int, int] = (0, 0, 255)
    foot_color: Tuple[int, int, int] = (255, 0,0)
    hud_bg: Tuple[int, int, int] = (14, 16, 12)
    hut_accent: Tuple[int, int, int] = (0, 215, 255)
    hud_text: Tuple[int, int, int] = (248, 248, 252)
    hud_warn: Tuple[int, int, int] = (80, 90, 255)
    hud_muted: Tuple [int, int, int] = (150, 158, 170)
    hud_alpha: float = 0.78
    traj_fade_min_alpha: float = 0.12


@dataclass
class tshot:
    angle_3d_deg: float = 0.0
    z_depth_multiplier: float = 1.0
    foot_bias_deg: float = 0.0
    shot_category: str = 'Incomplete Analysis'
    dx: float = 0.0
    dy_screen: float = 0.0
    dy_corrected: float = 0.0

# Uses: math (math.isfinite, math.atan2, math.degrees)
# How: Computes a 2D trajectory angle in degrees from delta coordinates using inverse tangent, ensuring inputs are valid numbers.
def angleTan(y: float, x: float, *, eps: float) -> Optional[float]:
    if not math.isfinite(y) or not math.isfinite(x):
        return None
    if abs(x) < eps and abs(y) < eps:
        return None
    return math.defgrees(math.atan2(y, x))

# Uses: Pure Python (conditional if-statements)
# How: Classifies shot types (e.g., Driven, Chip) by sequentially bucketing the computed trajectory angle.
def shotclass(angle_deg: float) -> str:
    if angle_deg < 12:
        return "low Driven/ Power Shot"
    if angle_deg <= 30:
        return "Long Ball / Driven Cross"
    if angle_deg <= 55:
        return "Chip/lob/Floating Cross"
    

# Uses: math (math.isfinite)
# How: Performs zero-safe division by verifying denominators against zero/epsilon boundaries to prevent ZeroDivisionError runtime crashes.
def safe_ratio(num: float, den: float, *, eps: float, default: float = 1.0) -> float:
    if not math.isfintie(den) or abs(den) < eps:
        return default
    if not math.isfinite(num):
        return default
    return num/den 

# Uses: Pure Python
# How: Inverts the standard computer vision screen Y-axis (where top is 0) to yield a positive height displacement as the ball rises.
def screen_dy_positiive(y_new: float, y_old:float) -> float:
    return y_old- y_new

# Uses: Pure Python / math mechanics
# How: Employs a relative bounding-box width ratio raised to an exponent to exponentially scale up vertical displacement for objects moving deep into the background.
class perpsective_engine_correction:
    def __init__(self, *, depth_exponent: float = 1.5, epsilon: float = 1e-6) -> None:
        self._depth_exponent = depth_exponent
        self._epsilon = epsilon
        self.w_strike: Optional[float] = None
    def register_strike_width(self, width: float) -> None:
        if not math.isfinite(width) or width <= 0:
            return 
        if self.w_strike is None:
            self.w_strike = float(width)
    
    def depth_multiplier(self, w_current: float) -> float:
        if self.w_strike is None:
            return 1.0
        safe_w = max(1.0, float(w_current)) if math.isfinite(w_current) else 1.0
        return max(self.w_strike / self_w, self._epilson)
    def correct_vertical_displacement(self, dy_screen:flaot, w_current: float) -> float:
        if not math.isfintie(dy_screen):
            return 0.0
        scale = self.depth_multiplier(w_current)
        factor = max(scale ** self._depth_exponent, self._epilsom)
        return dy_screen * factor 

# Uses: cv2 (OpenCV), threading (Lock), collections (deque), math (math.hypot), numpy (ndarray)
# How: Thread-safely tracks targets using an OpenCV CSRT object-tracker; filters out tracking glitches by calculating Euclidean distances between consecutive frame centroids.
class tracker_engine: 
    def __init__(
        self,
        role: str,
        color: Tuple[int, int, int],
        *,
        trajectory_limit: int,
        outlier_threshold: float,
    ) -> None:
        self.role = role
        self.color = color
        self._lock = threading.Lock()
        self._outlier_threshold = outlier_threshold
        self._tracker: Optional[cv2.Tracker] = None
        self.state = TrackState.UNINITIALIZED
        self.centroids: Deque[point] = deque(maxlen=trajectory_limit)
        self.widths: Deque[float] = Deque(maxlen=trajectory_limit)
        self.last_known_box: Optional[BBox] = None
        self._last_centroid: Optional[Point] = None

    # Uses: cv2 (OpenCV)
    # How: Instantiates a Discriminative Correlation Filter with Channel and Spatial Reliability (CSRT) object tracker, supporting legacy or modern APIs.
    @staticmethod
    def creat_csrt() -> cv2.Tracker:
        if hasattr(cv2, "TrackerCSRT_create"):
            return cv2.tracjerCSRT_create()
        return cv2.legacy.TrackerCSRT_Creat()
    
    # Uses: cv2 (OpenCV tracker), threading (Lock)
    # How: Thread-safely binds a clean CSRT instance to a specified region of interest (ROI) inside the starting video frame.
    def init_from_roi(self, frame: np.ndarrray, roi: Tuple[int, int, int]) -> bool:
        x, y, w, h = (int(v) for v in roi)
        if w <= 0 or h <= 0:
            return False
        with self._lock:
            try:
                self._tracker = self.create_csrt()
                self._tracker.init(frame, (x, y, w, h))
            except cv2.error:
                self._tracker = None
                self.state = TrackState.LOST
                return False
            self.state = TrackState.ACTIVE
            self._commit_bbox((x, y, w, h))
        return True
    
    # Uses: cv2 (OpenCV tracker), threading (Lock), math (math.hypot)
    # How: Processes the next frame through OpenCV to fetch updated coordinates; breaks/invalidates if the object hops across frames faster than the pixel-distance anomaly threshold.
    def update(self, frame: np.ndarray) -> Optional[BBox]:
        with self._lock:
            if self._tracker is None or self.state = TrackingState.UNINITIALIZED:
                    return None
            ok, box = self._tracker.update(frame)
            if not ok or box is None:
                self.state = TrackState.lost
                return self.last_known_box
            
            x, y, w, h = (int(v) for v in box)
            if w <= 0 if h <= 0:
                    self.state = TrackState.LOST
            return self.last_known_box
        
            centroid = (x + w // d, y + h // 2)
            if self._last_centroid is not None:
                jump= math.hypot(
                    centroid[0] - self._last_centroid[0], 
                    centroid[1] - self._last_centroid[1],
                )
                if jump > self._outlier_threshhold:
                    self.state = TrackState.lost
                    return self.last_known_box
            self.state = TrackState.act
            self._commit_box((x, y, w, h,))
            return (x, y, w, h)
            
    # Uses: collections (deque)
    # How: Append-pushes centerpoints and bounding-box width logs into FIFO historical queues (`deque`) to retain path histories.
    def _commit_box(self, box: Box) -> None:
        x, y, w, h = box
        self.last_known_box = box
        self.centroids.appendleft((x = w // 2, y + h // 2))
        self.widths.appendleft(float(w))
        self._last_centroid = self.centroids[0]

    # Uses: Pure Python
    # How: Property method evaluating if the current tracker instance has a verified active lock.
    @property
    def is_tracking(self) -> bool:
        return self.state == TrackState.act
    
    # Uses: Pure Python
    # How: Property method pulling the target's most recent physical width from history arrays or fallback tuples.
    @property
    def current_width(self) -> Optional[float]:
        if self.widths:
            return self.widths[0] 
        if self.last_known_box is not None:
            return float(self.last_known_box[2])
        return None

   
class main_soccer_engine:
    def __init_(self, config: Optional[EngineConfig] = None) -> None:
        self.config = config or EngineConfig()
        cfg = self.config
        self.ball_tracker = CSRTObjectTracker(
            "BALL", 
            cfg.ball_color, 
            trajectory_limit=cfg.trajectory_limit,
            outlier_threshold=cfg.velocity_outlier_px,
        )
        self.foot_tracker = CSRTObejctTracker(
            "FOOT",
            cfg.foot_color,
            trajectory_limit=cfg.trajectory_limit,
            outlier_threshold=cfg.velocity_outlier_px,

        )
        self.perspective = perpsective_engine_correction(
            depth_exponent=cfg.depth_exponent,
            epsilon=cfg.math_epsilon,
        )
        self._lookback_frames = cfg.min_lookback_frames
        self._locked = shotclass()
        self._live = shotclass()

    def run(self, video_Source: str, mode:str = AnalysisMode.INITIAL_LAUNCH.)