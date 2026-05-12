"""
Split baltimore_streets.mp4 into segments.
Run from the assignment3 folder:
    python split_video.py
Requires ffmpeg to be installed.
"""
import subprocess
import os

segments = [
    (1,  "00:00:00", "00:02:10"),
    (2,  "00:02:10", "00:03:54"),
    (3,  "00:03:54", "00:06:05"),
    (4,  "00:06:05", "00:10:19"),
    (5,  "00:10:19", "00:15:03"),
    (6,  "00:15:03", "00:21:52"),
    (7,  "00:21:52", "00:22:27"),
    (8,  "00:22:27", "00:25:01"),
    (9,  "00:25:01", "00:28:14"),
    (10, "00:28:14", "00:31:05.584"),
]

input_file = "baltimore_streets.mp4"

for num, start, end in segments:
    output = f"segment_{num:02d}.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-ss", start,
        "-to", end,
        "-c", "copy",
        output
    ]
    print(f"Creating {output} ({start} -> {end})...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  Done.")
    else:
        print(f"  Error: {result.stderr[-200:]}")

print("\nAll segments created.")
