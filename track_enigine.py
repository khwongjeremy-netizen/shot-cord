import cv2
import numpy as np
import math
from collections import deque

def run_analysis(VIDEO_SOURCE, mode="Initial Launch"):
    # --- 1. CONFIGURATION ---
    STRIKE_APPROACH_FRAME = 120  
    BALL_COLOR = (0, 0, 255)   
    FOOT_COLOR = (255, 255, 0) 
    TRAJECTORY_LIMIT = 60      
    LOOKBACK = 10 

    shot_category = "Analysis Incomplete" 
    ball_points = deque(maxlen=TRAJECTORY_LIMIT)
    foot_points = deque(maxlen=TRAJECTORY_LIMIT)
    ball_widths = deque(maxlen=TRAJECTORY_LIMIT)

    video_stream = cv2.VideoCapture(VIDEO_SOURCE)
    video_stream.set(cv2.CAP_PROP_POS_FRAMES, STRIKE_APPROACH_FRAME)

    is_loaded, current_frame = video_stream.read()
    if not is_loaded: return "Error: Video Failed"

    analytics_tracker = cv2.legacy.MultiTracker_create()

    for i in range(2):
        display_frame = current_frame.copy()
        target = "BALL" if i == 0 else "FOOT"
        color = (0, 0, 255) if i == 0 else (255, 255, 0)
        cv2.putText(display_frame, f"SELECT {target} (ENTER to confirm)", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        roi = cv2.selectROI("Selection Window", display_frame, False)
        analytics_tracker.add(cv2.legacy.TrackerCSRT_create(), current_frame, roi)

    cv2.destroyWindow("Selection Window")

    print("\n--- STARTING LIVE TELEMETRY ---")

    # --- 3. MAIN LOOP ---
    while True:
        is_loaded, current_frame = video_stream.read()
        if not is_loaded: break

        success, boxes = analytics_tracker.update(current_frame)

        if success:
            for i, box in enumerate(boxes):
                x, y, w, h = [int(v) for v in box]
                center = (x + w // 2, y + h // 2)
                if i == 0: 
                    ball_points.appendleft(center)
                    ball_widths.appendleft(w)
                    cv2.rectangle(current_frame, (x, y), (x + w, y + h), BALL_COLOR, 2)
                else: 
                    foot_points.appendleft(center)
                    cv2.rectangle(current_frame, (x, y), (x + w, y + h), FOOT_COLOR, 2)

        # --- 4. TRACER LOGIC ---
        for i in range(1, len(ball_points)):
            thickness = int(np.sqrt(TRAJECTORY_LIMIT / float(i + 1)) * 2.5)
            cv2.line(current_frame, ball_points[i - 1], ball_points[i], BALL_COLOR, thickness)

        # --- 5. RE-ENGINEERED PHYSICS & TERMINAL OUTPUT ---
        # Dynamic lookback ensures we get data even if we don't have 10 frames yet
        current_lookback = min(len(ball_points) - 1, LOOKBACK)
        
        if current_lookback >= 2 and len(foot_points) > current_lookback:
            # A. Depth & Vector Math
            curr_w = ball_widths[0]
            prev_w = ball_widths[current_lookback]
            depth_ratio = prev_w / curr_w if curr_w > 0 else 1.0

            dx = ball_points[0][0] - ball_points[current_lookback][0]
            dy = ball_points[current_lookback][1] - ball_points[0][1]

            if abs(dy) > abs(dx) * 1.5:
                corrected_dy = dy 
            else:
                corrected_dy = dy / (depth_ratio ** 1.5)

            # B. Anchor Math
            fdx = foot_points[0][0] - foot_points[current_lookback][0]
            fdy = foot_points[current_lookback][1] - foot_points[0][1]
            foot_bias = math.degrees(math.atan2(fdy, fdx)) if abs(fdx) > 1 else 0

            final_angle = math.degrees(math.atan2(corrected_dy, dx)) - foot_bias

            # C. Classification
            if dx > 1: # Lowered threshold for sensitivity
                if final_angle < 12: shot_category = "Low Driven / Power"
                elif 12 <= final_angle <= 30: shot_category = "Long Ball / Driven"
                else: shot_category = "Chip / Lob"

                # TERMINAL OUTPUT: SHOT DATA
                print(f"Angle: {final_angle:.2f}° | Type: {shot_category} | Z-Ratio: {depth_ratio:.2f}")

                # UI OVERLAY
                cv2.putText(current_frame, f"Angle: {int(final_angle)} Deg", (50, 80), 1, 1.5, (255, 255, 255), 2)
                cv2.putText(current_frame, f"Shot: {shot_category}", (50, 110), 1, 1.5, (0, 255, 255), 2)

        cv2.imshow("Striker Analytics v2.0", current_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    # --- 6. FINAL DATA DUMP ---
    print("\n--- FINAL TRAJECTORY COORDINATES (X, Y) ---")
    # Convert deque to a list and reverse so it prints in chronological order
    coords = list(ball_points)[::-1]
    for i, pt in enumerate(coords):
        print(f"Frame {i}: {pt}")

    video_stream.release()
    cv2.destroyAllWindows()
    return shot_category

#Plan to update script with this logic
'''
# --- 5. PHYSICS & NORMALIZATION LOGIC ---
        if len(ball_points) >= LOOKBACK + 1 and len(foot_points) >= LOOKBACK + 1:
            # 1. GET FOOT ANCHOR (The "True Ground")
            # We look at the foot's orientation over the lookback period
            fdx = foot_points[0][0] - foot_points[LOOKBACK][0]
            fdy = foot_points[LOOKBACK][1] - foot_points[0][1]
            
            # Note: If foot is static, fdx/fdy might be near 0. 
            # In a pro version, you'd use the bounding box width/height for orientation.
            foot_angle = math.degrees(math.atan2(fdy, fdx)) if abs(fdx) > 1 else 0

            # 2. GET RAW BALL VECTOR
            dx = ball_points[0][0] - ball_points[LOOKBACK][0]
            dy = ball_points[LOOKBACK][1] - ball_points[0][1]
            raw_ball_angle = math.degrees(math.atan2(dy, dx))
            
            # 3. NORMALIZE (The "Anchor" Step)
            # This 'zeros' the ball angle against the foot's baseline
            corrected_angle = raw_ball_angle - foot_angle

            if dx > 2:
                # Use corrected_angle for classification
                if corrected_angle < 15: shot_category = "Low Driven / Power"
                elif 15 <= corrected_angle <= 35: shot_category = "Floating Cross / Lifted"
                else: shot_category = "Chip / Lob"

                # Overlay corrected stats
                cv2.putText(current_frame, f"Foot Bias: {int(foot_angle)} Deg", (50, 80), 1, 1.2, (200, 200, 200), 2)
                cv2.putText(current_frame, f"Normal Angle: {int(corrected_angle)} Deg", (50, 110), 1, 1.5, (255, 255, 255), 2)
'''
'''
# --- RE-ENGINEERED PHYSICS: DEPTH & ANCHOR NORMALIZATION ---
        if len(ball_points) >= LOOKBACK + 1 and len(foot_points) >= LOOKBACK + 1:
            # 1. DEPTH ANALYSIS (The Z-Fix)
            # Track change in ball width (w) to identify depth movement
            # i=0 is current ball, i=LOOKBACK is 10 frames ago
            curr_w = boxes[0][2] 
            prev_w = last_known_w # Note: You'll need to store this from the previous loop
            
            # depth_ratio > 1 means ball is moving away (getting smaller)
            depth_ratio = prev_w / curr_w if curr_w > 0 else 1.0

            # 2. FOOT ANCHOR (The Tilted Ground Fix)
            fdx = foot_points[0][0] - foot_points[LOOKBACK][0]
            fdy = foot_points[LOOKBACK][1] - foot_points[0][1]
            ground_bias = math.degrees(math.atan2(fdy, fdx)) if abs(fdx) > 1 else 0

            # 3. VECTOR CALCULATION
            dx = ball_points[0][0] - ball_points[LOOKBACK][0]
            dy = ball_points[LOOKBACK][1] - ball_points[0][1]
            
            # --- THE "LONG BALL" CORRECTION ---
            # If depth_ratio is high, we 'flatten' the dy because the ball 
            # isn't rising as much as it appears to be on a 2D screen.
            corrected_dy = dy / (depth_ratio ** 2) 
            
            raw_angle = math.degrees(math.atan2(corrected_dy, dx))
            final_angle = raw_angle - ground_bias

            # 4. CLASSIFICATION WITH PERSPECTIVE CORRECTION
            if dx > 2:
                if final_angle < 12: shot_category = "Low Driven / Power"
                elif 12 <= final_angle <= 30: shot_category = "Long Ball / Driven Cross"
                else: shot_category = "Chip / Lob"
            # Overlay for Debugging
            cv2.putText(current_frame, f"Depth Multiplier: {round(depth_ratio, 2)}x", (50, 80), 1, 1.2, (255, 100, 0), 2)
            cv2.putText(current_frame, f"Corrected Angle: {int(final_angle)} Deg", (50, 110), 1, 1.5, (255, 255, 255), 2)
'''
