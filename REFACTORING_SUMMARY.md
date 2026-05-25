# Right-Triangle Trigonometry Visualization Refactoring

## Overview
The backend processing engine has been refactored to visually project right-triangle trigonometry elements directly onto the video overlay frame. This provides real-time visualization of the spatial geometry used for trajectory angle computation via `math.atan2`.

---

## Core Implementation Details

### 1. Spatial Anchor Definition
The right triangle is constructed using three vertices representing the exact spatial points used by the engine:

- **Vertex A (Base Point)**: `ball_pts[lookback]`
  - Historical ball location at the lookback interval boundary
  - Represents the origin of motion analysis
  
- **Vertex B (Tip Point)**: `ball_pts[0]`
  - Most recent tracked live ball center location
  - Represents the current trajectory endpoint
  
- **Vertex C (Right-Angle Intersection Point)**: `(ball_pts[0][0], ball_pts[lookback][1])`
  - Dynamically calculated using raw horizontal frame path and screen space vertical layout
  - Creates the 90° angle for trigonometric decomposition

### 2. Enhanced ShotTelemetry Dataclass
Modified the `ShotTelemetry` dataclass to persist calculated geometric metrics:
```python
@dataclass
class ShotTelemetry:
    angle_3d_deg: float = 0.0
    z_depth_multiplier: float = 1.0
    foot_bias_deg: float = 0.0
    shot_category: str = "Analysis Incomplete"
    dx: float = 0.0              # ← Base component (horizontal displacement)
    dy_screen: float = 0.0
    dy_corrected: float = 0.0    # ← Height component (perspective-corrected vertical)
```

### 3. Dynamic HUD Telemetry Display
Extended `_draw_telemetry_hud()` to render calculated digital metrics:
- **Base (dx)**: `"Base (dx): X px"` — Horizontal component of ball trajectory
- **Height (dy_corr)**: `"Height (dy_corr): Y px"` — Perspective-corrected vertical component

The HUD panel was expanded from 148px to 184px height to accommodate the new metric lines.

### 4. New Internal Method: `_draw_geometric_triangle()`
Created a dedicated rendering method with the following characteristics:

**Method Signature:**
```python
def _draw_geometric_triangle(self, frame: np.ndarray, lookback: int, t: ShotTelemetry) -> None
```

**Alpha-Blended Rendering Components:**

1. **Base Line (dx, Adjacent)**
   - Connects: `ball_pts[lookback]` → `(ball_pts[0][0], ball_pts[lookback][1])`
   - Color: `hud_muted` (subtle layout indicator)
   - Thickness: 1px (thin, minimal visual weight)
   - Style: Solid line with anti-aliasing (`cv2.LINE_AA`)

2. **Height Line (dy, Opposite)**
   - Connects: `(ball_pts[0][0], ball_pts[lookback][1])` → `ball_pts[0]`
   - Color: `hud_accent` (high-contrast operational indicator)
   - Thickness: 2px (emphasized for visibility)
   - Style: Solid line with anti-aliasing (`cv2.LINE_AA`)

3. **Hypotenuse Line**
   - Connects: `ball_pts[lookback]` → `ball_pts[0]`
   - Color: `ball_color` (primary tracking color)
   - Thickness: 2px (emphasized, primary geometric element)
   - Style: Solid line with anti-aliasing (`cv2.LINE_AA`)

4. **Vertex Markers**
   - 5-pixel radius circles at each vertex
   - Color-coded to match corresponding line colors
   - Filled circles for visual clarity

**Anti-Aliasing Configuration:**
- All lines and circles use `cv2.LINE_AA` for smooth, professional rendering
- No jagged edges or pixelation artifacts

### 5. Integration into Telemetry Loop
Modified `_telemetry_loop()` to conditionally draw the geometric triangle:

```python
# Draw geometric triangle overlay
lookback = self._effective_lookback()
if self.ball_tracker.is_tracking and lookback >= self.config.min_lookback_frames:
    self._draw_geometric_triangle(frame, lookback, telemetry)
```

**Conditional Rendering:**
- Only draws when ball tracking is **ACTIVE** (`self.ball_tracker.is_tracking`)
- Only draws when lookback satisfies **minimum frame requirements**
- Ensures triangle geometry is always mathematically valid

---

## Mathematical Foundation

The right triangle directly visualizes the components used in trajectory angle calculation:

```python
# From _compute_physics():
dx = float(ball_pts[0][0] - ball_pts[lookback][0])
dy_corrected = self.perspective.correct_vertical_displacement(dy_screen, w_current)

# Angle computation via atan2 (the visualized operation):
raw_ball_angle = math.atan2(dy_corrected, dx)
```

The rendered triangle's sides directly correspond to these mathematical operations:
- **Base** = `dx` (independent variable)
- **Height** = `dy_corrected` (dependent variable)
- **Hypotenuse** = `sqrt(dx² + dy_corrected²)`

---

## Color Scheme & Visual Hierarchy

| Element | Color | Purpose |
|---------|-------|---------|
| Base Line | `hud_muted` | Subtle layout reference |
| Height Line | `hud_accent` | High-contrast operation indicator |
| Hypotenuse | `ball_color` | Primary tracking element |
| Vertex A | `hud_muted` | Matches base line |
| Vertex B | `ball_color` | Matches hypotenuse (current position) |
| Vertex C | `hud_accent` | Matches height line (right-angle point) |

---

## Rendering Performance

- **No additional frame copies** beyond existing HUD rendering
- **Minimal computational overhead**: 3 line draws + 3 circle draws per frame
- **Optimized line rendering** with `cv2.LINE_AA` (hardware-accelerated on modern OpenCV)
- **Conditional execution** prevents unnecessary rendering when tracking is inactive

---

## Implementation Checklist

✅ **Spatial Anchor Definition**: Three vertices correctly positioned based on ball tracking data  
✅ **ShotTelemetry Enhancement**: `dx` and `dy_corrected` fields persisted  
✅ **HUD Telemetry Update**: Digital metrics displayed with proper formatting  
✅ **Geometric Triangle Method**: Dedicated `_draw_geometric_triangle()` implementation  
✅ **Anti-Aliased Rendering**: All lines and circles use `cv2.LINE_AA`  
✅ **Telemetry Loop Integration**: Triangle drawn conditionally in real-time loop  
✅ **Syntax Validation**: No compilation errors  

---

## Usage Notes

The geometric triangle overlay will automatically appear during video analysis when:
1. The ball tracker enters **ACTIVE** state after ROI initialization
2. Sufficient frames have been accumulated to satisfy the lookback requirement
3. Valid physics data is available for rendering

To disable the overlay (if needed for performance), comment out the call to `_draw_geometric_triangle()` in `_telemetry_loop()`.
