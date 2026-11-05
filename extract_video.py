import cv2
import os

video_path = r"d:\uzbekcodersbot\5millionsertifikat\20251115-0412-09.8012752.mp4"
cap = cv2.VideoCapture(video_path)

fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration_sec = total_frames / fps if fps > 0 else 0
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"Video Info:")
print(f"Duration: {duration_sec:.1f}s ({duration_sec/60:.2f} mins)")
print(f"FPS: {fps}")
print(f"Total Frames: {total_frames}")
print(f"Resolution: {width}x{height}")

# Create output folder for extracted frames
frames_dir = r"d:\uzbekcodersbot\5millionsertifikat\video_frames"
os.makedirs(frames_dir, exist_ok=True)

# Sample 1 frame every 10 seconds or 20 frames total
num_samples = 25
interval = max(1, total_frames // num_samples)

frame_idx = 0
saved_count = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    if frame_idx % interval == 0:
        sec = frame_idx / fps
        out_name = os.path.join(frames_dir, f"frame_{saved_count:02d}_{int(sec)}s.jpg")
        cv2.imwrite(out_name, frame)
        saved_count += 1
    frame_idx += 1

cap.release()
print(f"Extracted {saved_count} frames to {frames_dir}")
