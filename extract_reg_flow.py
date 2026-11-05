import cv2
import os

video_path = r"d:\uzbekcodersbot\5millionsertifikat\20251115-0412-09.8012752.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

frames_dir = r"d:\uzbekcodersbot\5millionsertifikat\video_frames\reg_flow"
os.makedirs(frames_dir, exist_ok=True)

target_seconds = range(20, 130, 5)

for sec in target_seconds:
    frame_no = int(sec * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(os.path.join(frames_dir, f"sec_{sec:03d}.jpg"), frame)

cap.release()
print("Saved reg flow frames!")
