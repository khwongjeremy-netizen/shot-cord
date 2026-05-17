"""
Striker Analytics — SoccerTelemetryEngine

Production OOP telemetry with decoupled CSRT trackers, Z-axis perspective
correction (w_strike scaling), and foot-anchored ground alignment.
"""

from __future__ import annotations

import math
import threading
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Deque, Optional, Tuple

import cv2
import numpy as np

Point = Tuple[int, int]
BBox = Tuple[int, int, int, int]


class TrackingState(Enum):
    UNINITIALIZED = "uninitialized"
    ACTIVE = "active"
    LOST = "lost"


class AnalysisMode(str, Enum):
    INITIAL_LAUNCH = "Initial Launch"
    FULL_TRAJECTORY = "Full Trajectory"


@dataclass(frozen=True)
class EngineConfig:
    strike_approach_frame: int = 120
    trajectory_limit: int = 60
    lookback_seconds: float = 0.33
    min_lookback_frames: int = 2
    max_lookback_frames: int = 30
    min_forward_dx: float = 1.0
    depth_exponent: float = 1.5
    velocity_outlier_px: float = 120.0
    math_epsilon: float = 1e-6
    window_title: str = "Striker Analytics v3.0"
    selection_window: str = "Selection Window"
    ball_color: Tuple[int, int, int] = (0, 0, 255)
    foot_color: Tuple[int, int, int] = (255, 255, 0)
    hud_bg: Tuple[int, int, int] = (14, 16, 22)
    hud_accent: Tuple[int, int, int] = (0, 210, 255)
    hud_text: Tuple[int, int, int] = (248, 248, 252)
    hud_warn: Tuple[int, int, int] = (80, 90, 255)
    hud_muted: Tuple[int, int, int] = (150, 158, 170)
    hud_alpha: float = 0.74
    traj_fade_min_alpha: float = 0.12


@dataclass
class ShotTelemetry:
    angle_3d_deg: float = 0.0
    z_depth_multiplier: float = 1.0
    foot_bias_deg: float = 0.0
    shot_category: str = "Analysis Incomplete"
    dx: float = 0.0
    dy_screen: float = 0.0
    dy_corrected: float = 0.0


# ---------------------------------------------------------------------------
# Math utilities
# ---------------------------------------------------------------------------


def screen_dy_up_positive(y_recent: float, y_older: float) -> float:
    """Positive dy when the ball rises (OpenCV y grows downward)."""
    return y_older - y_recent


def safe_ratio(num: float, den: float, *, eps: float, default: float = 1.0) -> float:
    if not math.isfinite(den) or abs(den) < eps:
        return default
    if not math.isfinite(num):
        return default
    return num / den


def safe_atan2_deg(y: float, x: float, *, eps: float) -> Optional[float]:
    if not math.isfinite(y) or not math.isfinite(x):
        return None
    if abs(x) < eps and abs(y) < eps:
        return None
    return math.degrees(math.atan2(y, x))


def classify_shot_3d(angle_deg: float) -> str:
    if angle_deg < 12:
        return "Low Driven / Power Shot"
    if angle_deg <= 30:
        return "Long Ball / Driven Cross"
    return "Chip / Lob / Floating Cross"


# ---------------------------------------------------------------------------
# Perspective & Z-axis correction (PRD §1)
# ---------------------------------------------------------------------------


class PerspectiveCorrectionEngine:
    """
    Corrects 2D lens compression: distant balls show artificially flat dy.
    Uses strike-frame width as the depth reference (w_strike).
    """

    def __init__(self, *, depth_exponent: float = 1.5, epsilon: float = 1e-6) -> None:
        self._depth_exponent = depth_exponent
        self._epsilon = epsilon
        self.w_strike: Optional[float] = None

    def register_strike_width(self, width: float) -> None:
        """Cache w_strike from the ball bbox at the strike / ROI init frame."""
        if not math.isfinite(width) or width <= 0:
            return
        if self.w_strike is None:
            self.w_strike = float(width)

    def depth_multiplier(self, w_current: float) -> float:
        """scale_factor = w_strike / max(1, w_current) — Z-axis depth multiplier."""
        if self.w_strike is None:
            return 1.0
        safe_w = max(1.0, float(w_current)) if math.isfinite(w_current) else 1.0
        return max(self.w_strike / safe_w, self._epsilon)

    def correct_vertical_displacement(self, dy_screen: float, w_current: float) -> float:
        """dy_corrected = dy_screen * (scale_factor ** 1.5)"""
        if not math.isfinite(dy_screen):
            return 0.0
        scale = self.depth_multiplier(w_current)
        factor = max(scale ** self._depth_exponent, self._epsilon)
        return dy_screen * factor


# ---------------------------------------------------------------------------
# Decoupled CSRT tracker (PRD §3)
# ---------------------------------------------------------------------------


class CSRTObjectTracker:
    """Thread-safe wrapper around a single CSRT instance."""

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
        self.state = TrackingState.UNINITIALIZED
        self.centroids: Deque[Point] = deque(maxlen=trajectory_limit)
        self.widths: Deque[float] = deque(maxlen=trajectory_limit)
        self.last_known_bbox: Optional[BBox] = None
        self._last_centroid: Optional[Point] = None

    @staticmethod
    def create_csrt() -> cv2.Tracker:
        if hasattr(cv2, "TrackerCSRT_create"):
            return cv2.TrackerCSRT_create()
        return cv2.legacy.TrackerCSRT_create()

    def init_from_roi(self, frame: np.ndarray, roi: Tuple[int, int, int, int]) -> bool:
        x, y, w, h = (int(v) for v in roi)
        if w <= 0 or h <= 0:
            return False
        with self._lock:
            try:
                self._tracker = self.create_csrt()
                self._tracker.init(frame, (x, y, w, h))
            except cv2.error:
                self._tracker = None
                self.state = TrackingState.LOST
                return False
            self.state = TrackingState.ACTIVE
            self._commit_bbox((x, y, w, h))
        return True

    def update(self, frame: np.ndarray) -> Optional[BBox]:
        with self._lock:
            if self._tracker is None or self.state == TrackingState.UNINITIALIZED:
                return None

            ok, box = self._tracker.update(frame)
            if not ok or box is None:
                self.state = TrackingState.LOST
                return self.last_known_bbox

            x, y, w, h = (int(v) for v in box)
            if w <= 0 or h <= 0:
                self.state = TrackingState.LOST
                return self.last_known_bbox

            centroid = (x + w // 2, y + h // 2)
            if self._last_centroid is not None:
                jump = math.hypot(
                    centroid[0] - self._last_centroid[0],
                    centroid[1] - self._last_centroid[1],
                )
                if jump > self._outlier_threshold:
                    self.state = TrackingState.LOST
                    return self.last_known_bbox

            self.state = TrackingState.ACTIVE
            self._commit_bbox((x, y, w, h))
            return (x, y, w, h)

    def _commit_bbox(self, bbox: BBox) -> None:
        x, y, w, h = bbox
        self.last_known_bbox = bbox
        self.centroids.appendleft((x + w // 2, y + h // 2))
        self.widths.appendleft(float(w))
        self._last_centroid = self.centroids[0]

    @property
    def is_tracking(self) -> bool:
        return self.state == TrackingState.ACTIVE

    @property
    def current_width(self) -> Optional[float]:
        if self.widths:
            return self.widths[0]
        if self.last_known_bbox is not None:
            return float(self.last_known_bbox[2])
        return None


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------


class SoccerTelemetryEngine:
    """
    Principal telemetry pipeline: dual trackers, perspective correction,
    foot-ground normalization, and alpha-blended HUD.
    """

    def __init__(self, config: Optional[EngineConfig] = None) -> None:
        self.config = config or EngineConfig()
        cfg = self.config

        self.ball_tracker = CSRTObjectTracker(
            "BALL",
            cfg.ball_color,
            trajectory_limit=cfg.trajectory_limit,
            outlier_threshold=cfg.velocity_outlier_px,
        )
        self.foot_tracker = CSRTObjectTracker(
            "FOOT",
            cfg.foot_color,
            trajectory_limit=cfg.trajectory_limit,
            outlier_threshold=cfg.velocity_outlier_px,
        )

        self.perspective = PerspectiveCorrectionEngine(
            depth_exponent=cfg.depth_exponent,
            epsilon=cfg.math_epsilon,
        )

        self._lookback_frames = cfg.min_lookback_frames
        self._locked = ShotTelemetry()
        self._live = ShotTelemetry()

    def run(self, video_source: str, mode: str = AnalysisMode.INITIAL_LAUNCH.value) -> str:
        capture = cv2.VideoCapture(video_source)
        if not capture.isOpened():
            return "Error: Video Failed"

        fps = capture.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(fps) or fps <= 0:
            fps = 30.0
        self._lookback_frames = max(
            self.config.min_lookback_frames,
            min(
                int(round(fps * self.config.lookback_seconds)),
                self.config.max_lookback_frames,
            ),
        )

        capture.set(cv2.CAP_PROP_POS_FRAMES, self.config.strike_approach_frame)
        ok, frame = capture.read()
        if not ok or frame is None:
            capture.release()
            return "Error: Video Failed"

        if not self._interactive_roi_setup(frame):
            capture.release()
            cv2.destroyAllWindows()
            return "Error: ROI Selection Cancelled"

        cv2.destroyWindow(self.config.selection_window)
        print("\n--- STARTING LIVE TELEMETRY (3D CORRECTED) ---")

        analysis_mode = (
            AnalysisMode.FULL_TRAJECTORY
            if mode == AnalysisMode.FULL_TRAJECTORY.value
            else AnalysisMode.INITIAL_LAUNCH
        )

        try:
            self._telemetry_loop(capture, analysis_mode)
        finally:
            capture.release()
            cv2.destroyAllWindows()

        self._print_trajectory_dump()
        return (
            self._locked.shot_category
            if analysis_mode == AnalysisMode.INITIAL_LAUNCH
            else self._live.shot_category
        )

    def _interactive_roi_setup(self, frame: np.ndarray) -> bool:
        sequence = (
            (self.ball_tracker, "BALL"),
            (self.foot_tracker, "FOOT"),
        )
        for tracker, label in sequence:
            overlay = frame.copy()
            cv2.putText(
                overlay,
                f"SELECT {label} (ENTER to confirm)",
                (48, 52),
                cv2.FONT_HERSHEY_DUPLEX,
                1.0,
                tracker.color,
                2,
                cv2.LINE_AA,
            )
            roi = cv2.selectROI(self.config.selection_window, overlay, False)
            if roi[2] <= 0 or roi[3] <= 0:
                return False
            if not tracker.init_from_roi(frame, roi):
                return False
            if label == "BALL":
                self.perspective.register_strike_width(float(roi[2]))
        return True

    def _telemetry_loop(self, capture: cv2.VideoCapture, mode: AnalysisMode) -> None:
        while True:
            ok, frame = capture.read()
            if not ok or frame is None:
                break

            ball_bbox = self.ball_tracker.update(frame)
            foot_bbox = self.foot_tracker.update(frame)

            if self.ball_tracker.is_tracking and ball_bbox is not None:
                x, y, w, h = ball_bbox
                cv2.rectangle(
                    frame, (x, y), (x + w, y + h),
                    self.config.ball_color, 2, cv2.LINE_AA,
                )
                w_now = self.ball_tracker.current_width
                if w_now is not None:
                    self.perspective.register_strike_width(w_now)

            if self.foot_tracker.is_tracking and foot_bbox is not None:
                x, y, w, h = foot_bbox
                cv2.rectangle(
                    frame, (x, y), (x + w, y + h),
                    self.config.foot_color, 2, cv2.LINE_AA,
                )

            self._draw_fading_trajectory(frame)
            self._draw_tracking_status(frame)

            telemetry = self._compute_physics()
            if telemetry is not None:
                self._live = telemetry
                if telemetry.shot_category != "Analysis Incomplete":
                    if (
                        mode == AnalysisMode.FULL_TRAJECTORY
                        or self._locked.shot_category == "Analysis Incomplete"
                    ):
                        self._locked = telemetry
                        print(
                            f"3D Angle: {telemetry.angle_3d_deg:.2f}° | "
                            f"{telemetry.shot_category} | "
                            f"Z-Mult: {telemetry.z_depth_multiplier:.2f}x"
                        )

            self._draw_telemetry_hud(frame, self._live)
            cv2.imshow(self.config.window_title, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    # -- Rendering ----------------------------------------------------------

    def _draw_fading_trajectory(self, frame: np.ndarray) -> None:
        """Alpha-blended trail; newest segment brightest, oldest fades out."""
        pts = list(self.ball_tracker.centroids)
        if len(pts) < 2:
            return

        n = len(pts)
        b, g, r = self.config.ball_color
        for i in range(1, n):
            t = i / max(n - 1, 1)
            alpha = self.config.traj_fade_min_alpha + (1.0 - self.config.traj_fade_min_alpha) * (1.0 - t)
            layer = frame.copy()
            thickness = max(1, int(3.5 * alpha + 0.5))
            cv2.line(layer, pts[i - 1], pts[i], (b, g, r), thickness, cv2.LINE_AA)
            cv2.addWeighted(layer, alpha, frame, 1.0 - alpha, 0, frame)

    def _draw_tracking_status(self, frame: np.ndarray) -> None:
        statuses = (
            (self.ball_tracker, "Ball", 24, frame.shape[0] - 56),
            (self.foot_tracker, "Foot", 24, frame.shape[0] - 28),
        )
        for tracker, name, x, y in statuses:
            if tracker.state == TrackingState.LOST:
                cv2.putText(
                    frame,
                    f"{name}: Tracking Lost",
                    (x, y),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.62,
                    self.config.hud_warn,
                    2,
                    cv2.LINE_AA,
                )

    def _draw_telemetry_hud(self, frame: np.ndarray, t: ShotTelemetry) -> None:
        h, w_img = frame.shape[:2]
        x0, y0, pw, ph = 20, 20, 480, 148

        overlay = frame.copy()
        cv2.rectangle(overlay, (x0, y0), (min(x0 + pw, w_img - 1), min(y0 + ph, h - 1)), self.config.hud_bg, -1)
        cv2.addWeighted(overlay, self.config.hud_alpha, frame, 1.0 - self.config.hud_alpha, 0, frame)

        if t.shot_category == "Analysis Incomplete":
            cv2.putText(
                frame, "Awaiting trajectory data…",
                (x0 + 14, y0 + 40), cv2.FONT_HERSHEY_DUPLEX, 0.62,
                self.config.hud_muted, 1, cv2.LINE_AA,
            )
            return

        lines = [
            (f"3D Corrected Angle: {t.angle_3d_deg:+.1f}°", self.config.hud_text, 0.82, 2),
            (f"Calculated Shot Category: {t.shot_category}", self.config.hud_accent, 0.64, 2),
            (f"Z-Axis Depth Multiplier: {t.z_depth_multiplier:.2f}x", self.config.hud_muted, 0.58, 1),
        ]
        ty = y0 + 38
        for text, color, scale, thickness in lines:
            cv2.putText(
                frame, text, (x0 + 14, ty),
                cv2.FONT_HERSHEY_DUPLEX, scale, color, thickness, cv2.LINE_AA,
            )
            ty += 36

    # -- Physics (PRD §1, §2, §4) -------------------------------------------

    def _effective_lookback(self) -> int:
        n = len(self.ball_tracker.centroids)
        if n < 2:
            return 0
        return min(n - 1, self._lookback_frames)

    def _compute_physics(self) -> Optional[ShotTelemetry]:
        lookback = self._effective_lookback()
        eps = self.config.math_epsilon
        if lookback < self.config.min_lookback_frames:
            return None
        if len(self.foot_tracker.centroids) <= lookback:
            return None

        ball_pts = self.ball_tracker.centroids
        foot_pts = self.foot_tracker.centroids

        w_current = self.ball_tracker.current_width
        if w_current is None or self.perspective.w_strike is None:
            return None

        z_mult = self.perspective.depth_multiplier(w_current)

        dx = float(ball_pts[0][0] - ball_pts[lookback][0])
        dy_screen = screen_dy_up_positive(
            float(ball_pts[0][1]),
            float(ball_pts[lookback][1]),
        )
        dy_corrected = self.perspective.correct_vertical_displacement(dy_screen, w_current)

        fdx = float(foot_pts[0][0] - foot_pts[lookback][0])
        fdy = screen_dy_up_positive(
            float(foot_pts[0][1]),
            float(foot_pts[lookback][1]),
        )
        foot_bias = safe_atan2_deg(fdy, fdx, eps=eps) or 0.0

        raw_ball_angle = safe_atan2_deg(dy_corrected, dx, eps=eps)
        if raw_ball_angle is None:
            return None

        angle_3d = raw_ball_angle - foot_bias

        if dx <= self.config.min_forward_dx:
            return ShotTelemetry(
                angle_3d_deg=angle_3d,
                z_depth_multiplier=z_mult,
                foot_bias_deg=foot_bias,
                shot_category="Analysis Incomplete",
                dx=dx,
                dy_screen=dy_screen,
                dy_corrected=dy_corrected,
            )

        return ShotTelemetry(
            angle_3d_deg=angle_3d,
            z_depth_multiplier=z_mult,
            foot_bias_deg=foot_bias,
            shot_category=classify_shot_3d(angle_3d),
            dx=dx,
            dy_screen=dy_screen,
            dy_corrected=dy_corrected,
        )

    def _print_trajectory_dump(self) -> None:
        print("\n--- FINAL TRAJECTORY COORDINATES (X, Y) ---")
        for i, pt in enumerate(reversed(self.ball_tracker.centroids)):
            print(f"Frame {i}: {pt}")


def run_analysis(video_source: str, mode: str = "Initial Launch") -> str:
    """Backward-compatible entry point for main.py."""
    return SoccerTelemetryEngine().run(video_source, mode=mode)
