"""
Striker Analytics — production telemetry engine.

SoccerTelemetryEngine owns dual isolated CSRT trackers (ball / foot),
perspective-aware launch-angle math, and alpha-blended HUD rendering.
"""

from __future__ import annotations

import math
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
    height_vs_depth_ratio: float = 1.5
    velocity_outlier_px: float = 120.0
    math_epsilon: float = 1e-6
    window_title: str = "Striker Analytics v2.0"
    selection_window: str = "Selection Window"
    ball_color: Tuple[int, int, int] = (0, 0, 255)
    foot_color: Tuple[int, int, int] = (255, 255, 0)
    hud_bg: Tuple[int, int, int] = (18, 18, 24)
    hud_accent: Tuple[int, int, int] = (0, 200, 255)
    hud_text: Tuple[int, int, int] = (245, 245, 245)
    hud_muted: Tuple[int, int, int] = (160, 165, 175)
    hud_alpha: float = 0.72


@dataclass
class ShotTelemetry:
    launch_angle_deg: float = 0.0
    depth_ratio: float = 1.0
    foot_bias_deg: float = 0.0
    shot_category: str = "Analysis Incomplete"
    dx: float = 0.0
    dy_corrected: float = 0.0


def screen_dy_up_positive(y_recent: float, y_older: float) -> float:
    """Positive when the object moved upward (OpenCV y increases downward)."""
    return y_older - y_recent


def safe_ratio(numerator: float, denominator: float, *, epsilon: float, default: float = 1.0) -> float:
    if abs(denominator) < epsilon:
        return default
    return numerator / denominator


def classify_shot(angle_deg: float) -> str:
    if angle_deg < 12:
        return "Low Driven / Power"
    if angle_deg <= 30:
        return "Long Ball / Driven"
    return "Chip / Lob"


class IsolatedCSRTTracker:
    """Independent CSRT tracker with explicit state and bbox history."""

    def __init__(
        self,
        label: str,
        color: Tuple[int, int, int],
        *,
        trajectory_limit: int,
        outlier_threshold: float,
    ) -> None:
        self.label = label
        self.color = color
        self._outlier_threshold = outlier_threshold
        self._tracker: Optional[cv2.Tracker] = None
        self.state = TrackingState.UNINITIALIZED
        self.centroids: Deque[Point] = deque(maxlen=trajectory_limit)
        self.widths: Deque[float] = deque(maxlen=trajectory_limit)
        self.last_known_bbox: Optional[BBox] = None
        self._last_centroid: Optional[Point] = None

    @staticmethod
    def _create_csrt() -> cv2.Tracker:
        if hasattr(cv2, "TrackerCSRT_create"):
            return cv2.TrackerCSRT_create()
        return cv2.legacy.TrackerCSRT_create()

    def init_from_roi(self, frame: np.ndarray, roi: Tuple[int, int, int, int]) -> bool:
        x, y, w, h = (int(v) for v in roi)
        if w <= 0 or h <= 0:
            return False
        try:
            self._tracker = self._create_csrt()
            self._tracker.init(frame, (x, y, w, h))
        except cv2.error:
            self._tracker = None
            self.state = TrackingState.LOST
            return False
        self.state = TrackingState.ACTIVE
        self._record_bbox((x, y, w, h))
        return True

    def update(self, frame: np.ndarray) -> Optional[BBox]:
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
        self._record_bbox((x, y, w, h))
        return (x, y, w, h)

    def _record_bbox(self, bbox: BBox) -> None:
        x, y, w, h = bbox
        centroid = (x + w // 2, y + h // 2)
        self.last_known_bbox = bbox
        self.centroids.appendleft(centroid)
        self.widths.appendleft(float(w))
        self._last_centroid = centroid

    @property
    def is_active(self) -> bool:
        return self.state == TrackingState.ACTIVE and bool(self.centroids)

    @property
    def current_width(self) -> Optional[float]:
        if self.widths:
            return self.widths[0]
        if self.last_known_bbox is not None:
            return float(self.last_known_bbox[2])
        return None

    def width_at_lookback(self, lookback: int) -> Optional[float]:
        if lookback < len(self.widths):
            return self.widths[lookback]
        if self.last_known_bbox is not None:
            return float(self.last_known_bbox[2])
        return None


class SoccerTelemetryEngine:
    """Production-grade soccer ball / foot telemetry and shot classification."""

    def __init__(self, config: Optional[EngineConfig] = None) -> None:
        self.config = config or EngineConfig()
        cfg = self.config
        self.ball = IsolatedCSRTTracker(
            "BALL",
            cfg.ball_color,
            trajectory_limit=cfg.trajectory_limit,
            outlier_threshold=cfg.velocity_outlier_px,
        )
        self.foot = IsolatedCSRTTracker(
            "FOOT",
            cfg.foot_color,
            trajectory_limit=cfg.trajectory_limit,
            outlier_threshold=cfg.velocity_outlier_px,
        )
        self._lookback_frames = cfg.min_lookback_frames
        self._locked: ShotTelemetry = ShotTelemetry()
        self._live: ShotTelemetry = ShotTelemetry()

    def run(self, video_source: str, mode: str = AnalysisMode.INITIAL_LAUNCH.value) -> str:
        capture = cv2.VideoCapture(video_source)
        if not capture.isOpened():
            return "Error: Video Failed"

        fps = capture.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(fps) or fps <= 0:
            fps = 30.0
        self._lookback_frames = int(round(fps * self.config.lookback_seconds))
        self._lookback_frames = max(
            self.config.min_lookback_frames,
            min(self._lookback_frames, self.config.max_lookback_frames),
        )

        capture.set(cv2.CAP_PROP_POS_FRAMES, self.config.strike_approach_frame)
        ok, frame = capture.read()
        if not ok or frame is None:
            capture.release()
            return "Error: Video Failed"

        if not self._select_rois(frame):
            capture.release()
            cv2.destroyAllWindows()
            return "Error: ROI Selection Cancelled"

        cv2.destroyWindow(self.config.selection_window)
        print("\n--- STARTING LIVE TELEMETRY ---")

        analysis_mode = (
            AnalysisMode.FULL_TRAJECTORY
            if mode == AnalysisMode.FULL_TRAJECTORY.value
            else AnalysisMode.INITIAL_LAUNCH
        )

        try:
            self._main_loop(capture, analysis_mode)
        finally:
            capture.release()
            cv2.destroyAllWindows()

        self._dump_trajectory()
        if analysis_mode == AnalysisMode.INITIAL_LAUNCH:
            return self._locked.shot_category
        return self._live.shot_category

    def _select_rois(self, frame: np.ndarray) -> bool:
        for tracker, label in ((self.ball, "BALL"), (self.foot, "FOOT")):
            overlay = frame.copy()
            cv2.putText(
                overlay,
                f"SELECT {label} (ENTER to confirm)",
                (50, 50),
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
        return True

    def _main_loop(self, capture: cv2.VideoCapture, mode: AnalysisMode) -> None:
        while True:
            ok, frame = capture.read()
            if not ok or frame is None:
                break

            ball_bbox = self.ball.update(frame)
            foot_bbox = self.foot.update(frame)

            if ball_bbox is not None and self.ball.is_active:
                x, y, w, h = ball_bbox
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    self.config.ball_color,
                    2,
                    cv2.LINE_AA,
                )

            if foot_bbox is not None and self.foot.is_active:
                x, y, w, h = foot_bbox
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    self.config.foot_color,
                    2,
                    cv2.LINE_AA,
                )

            self._draw_trajectory(frame)
            telemetry = self._compute_telemetry()
            if telemetry is not None:
                self._live = telemetry
                if telemetry.shot_category != "Analysis Incomplete":
                    if (
                        mode == AnalysisMode.FULL_TRAJECTORY
                        or self._locked.shot_category == "Analysis Incomplete"
                    ):
                        self._locked = telemetry
                        print(
                            f"Angle: {telemetry.launch_angle_deg:.2f}° | "
                            f"Type: {telemetry.shot_category} | "
                            f"Z-Ratio: {telemetry.depth_ratio:.2f}"
                        )

            self._draw_hud(frame, self._live)
            cv2.imshow(self.config.window_title, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    def _draw_trajectory(self, frame: np.ndarray) -> None:
        pts = list(self.ball.centroids)
        limit = self.config.trajectory_limit
        for i in range(1, len(pts)):
            thickness = max(1, int(math.sqrt(limit / float(i + 1)) * 2.5))
            cv2.line(
                frame,
                pts[i - 1],
                pts[i],
                self.config.ball_color,
                thickness,
                cv2.LINE_AA,
            )

    def _draw_hud(self, frame: np.ndarray, t: ShotTelemetry) -> None:
        if t.shot_category == "Analysis Incomplete":
            return

        h, w = frame.shape[:2]
        x0, y0, pw, ph = 24, 24, 420, 130
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (x0, y0),
            (min(x0 + pw, w - 1), min(y0 + ph, h - 1)),
            self.config.hud_bg,
            -1,
        )
        cv2.addWeighted(
            overlay,
            self.config.hud_alpha,
            frame,
            1.0 - self.config.hud_alpha,
            0,
            frame,
        )

        rows = [
            (f"Launch Angle  {t.launch_angle_deg:+.1f}°", self.config.hud_text, 0.85, 2),
            (t.shot_category, self.config.hud_accent, 0.72, 2),
            (
                f"Depth {t.depth_ratio:.2f}x   Foot bias {t.foot_bias_deg:+.1f}°",
                self.config.hud_muted,
                0.58,
                1,
            ),
        ]
        ty = y0 + 36
        for text, color, scale, thickness in rows:
            cv2.putText(
                frame,
                text,
                (x0 + 16, ty),
                cv2.FONT_HERSHEY_DUPLEX,
                scale,
                color,
                thickness,
                cv2.LINE_AA,
            )
            ty += 34

    def _effective_lookback(self) -> int:
        if len(self.ball.centroids) < 2:
            return 0
        return min(len(self.ball.centroids) - 1, self._lookback_frames)

    def _compute_telemetry(self) -> Optional[ShotTelemetry]:
        lookback = self._effective_lookback()
        eps = self.config.math_epsilon
        if lookback < self.config.min_lookback_frames:
            return None
        if len(self.foot.centroids) <= lookback:
            return None

        ball_pts = self.ball.centroids
        foot_pts = self.foot.centroids

        curr_w = self.ball.current_width
        prev_w = self.ball.width_at_lookback(lookback)
        if curr_w is None or prev_w is None:
            return None

        depth_ratio = max(safe_ratio(prev_w, curr_w, epsilon=eps, default=1.0), eps)

        dx = float(ball_pts[0][0] - ball_pts[lookback][0])
        dy = screen_dy_up_positive(float(ball_pts[0][1]), float(ball_pts[lookback][1]))

        if abs(dy) > abs(dx) * self.config.height_vs_depth_ratio:
            corrected_dy = dy
        else:
            corrected_dy = dy / max(depth_ratio ** self.config.depth_exponent, eps)

        fdx = float(foot_pts[0][0] - foot_pts[lookback][0])
        fdy = screen_dy_up_positive(float(foot_pts[0][1]), float(foot_pts[lookback][1]))
        foot_bias = (
            math.degrees(math.atan2(fdy, fdx)) if abs(fdx) > eps else 0.0
        )

        if abs(dx) < eps and abs(corrected_dy) < eps:
            return None

        launch_angle = math.degrees(math.atan2(corrected_dy, dx)) - foot_bias

        if dx <= self.config.min_forward_dx:
            return ShotTelemetry(
                launch_angle_deg=launch_angle,
                depth_ratio=depth_ratio,
                foot_bias_deg=foot_bias,
                shot_category="Analysis Incomplete",
                dx=dx,
                dy_corrected=corrected_dy,
            )

        return ShotTelemetry(
            launch_angle_deg=launch_angle,
            depth_ratio=depth_ratio,
            foot_bias_deg=foot_bias,
            shot_category=classify_shot(launch_angle),
            dx=dx,
            dy_corrected=corrected_dy,
        )

    def _dump_trajectory(self) -> None:
        print("\n--- FINAL TRAJECTORY COORDINATES (X, Y) ---")
        for i, pt in enumerate(reversed(self.ball.centroids)):
            print(f"Frame {i}: {pt}")


def run_analysis(video_source: str, mode: str = "Initial Launch") -> str:
    """Backward-compatible entry point for main.py."""
    return SoccerTelemetryEngine().run(video_source, mode=mode)
