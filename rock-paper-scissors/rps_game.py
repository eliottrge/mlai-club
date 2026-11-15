"""Rock-Paper-Scissors against the computer, using a Teachable Machine (Keras) model.

Put the two files from your Teachable Machine export (Tensorflow > Keras) somewhere
on your computer with these exact names:

    keras_model_rps.h5
    labels.txt

The game looks for them next to this script, in the current folder, and in your
Downloads / Desktop / Documents folders (also one folder deep, so an unzipped
export folder works too).

Controls:  SPACE = start a round     Q = quit
"""
import os

# Teachable Machine .h5 files only load reliably with the legacy Keras (tf_keras).
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS", "0")  # faster/more reliable MSMF

import argparse
import random
import sys
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

MODEL_NAME = "keras_model_rps.h5"
LABELS_NAME = "labels.txt"

CHOICES = ("rock", "paper", "scissors")
BEATS = {"rock": "scissors", "scissors": "paper", "paper": "rock"}

COUNTDOWN_SECONDS = 5
VOTE_WINDOW_SECONDS = 2.0   # only the last N seconds of the countdown count
MIN_CONFIDENCE = 0.60
PREDICT_INTERVAL = 0.1      # seconds between predictions
RESULT_SECONDS = 3


# --------------------------------------------------------------------------- #
# Pure game logic
# --------------------------------------------------------------------------- #
def decide_winner(user, computer):
    """Return 'user', 'computer' or 'tie'."""
    if user == computer:
        return "tie"
    return "user" if BEATS[user] == computer else "computer"


def parse_labels(lines):
    """Map each class index to rock/paper/scissors, or None for any other class.

    Teachable Machine writes lines like '0 Rock'.
    """
    mapped = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        name = parts[1] if len(parts) == 2 and parts[0].isdigit() else line
        name = name.strip().lower()
        mapped.append(next((c for c in CHOICES if c in name), None))
    missing = [c for c in CHOICES if c not in mapped]
    if missing:
        raise ValueError(
            "labels.txt must contain classes named Rock, Paper and Scissors "
            f"(missing: {', '.join(missing)})."
        )
    return mapped


def pick_choice(votes, now, end_time):
    """Pick the user's choice from (timestamp, label, confidence) votes.

    Only confident votes from the last VOTE_WINDOW_SECONDS before end_time count.
    Returns None if there is no valid vote.
    """
    recent = [
        label
        for t, label, conf in votes
        if label is not None and conf >= MIN_CONFIDENCE and t >= end_time - VOTE_WINDOW_SECONDS
    ]
    if not recent:
        return None
    return Counter(recent).most_common(1)[0][0]


# --------------------------------------------------------------------------- #
# Model loading
# --------------------------------------------------------------------------- #
def search_dirs():
    home = Path.home()
    roots = [Path(__file__).resolve().parent, Path.cwd()]
    for base in (home, home / "OneDrive"):  # OneDrive often hosts Desktop/Documents
        roots += [base / "Downloads", base / "Desktop", base / "Documents"]
    dirs = []
    for root in roots:
        if root.is_dir() and root not in dirs:
            dirs.append(root)
    return dirs


def find_file(name, max_depth=2):
    """Look for `name` in the usual places, then up to `max_depth` folders deep."""
    roots = search_dirs()
    level = roots
    for _ in range(max_depth + 1):
        for folder in level:
            if (folder / name).is_file():
                return folder / name
        nxt = []
        for folder in level:
            try:
                nxt += sorted(p for p in folder.iterdir()
                              if p.is_dir() and not p.name.startswith((".", "__")))
            except OSError:
                continue
        level = nxt
    return None


def locate(explicit, name):
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            sys.exit(f"File not found: {path}")
        return path
    path = find_file(name)
    if path is None:
        searched = "\n  ".join(str(d) for d in search_dirs())
        sys.exit(
            f"Could not find '{name}'.\n"
            f"Export your Teachable Machine model (Tensorflow > Keras), unzip it, and make sure\n"
            f"'{MODEL_NAME}' and '{LABELS_NAME}' are in one of these folders:\n  {searched}"
        )
    return path


def load_model(path):
    try:
        import tf_keras
    except ImportError:
        sys.exit("A required library is missing. Run play.bat (Windows) / play.command (Mac), "
                 "or install it with:  python -m pip install -r requirements.txt")
    return tf_keras.models.load_model(str(path), compile=False)


def preprocess(frame):
    """Teachable Machine preprocessing: square crop, 224x224, RGB, scaled to [-1, 1]."""
    h, w = frame.shape[:2]
    side = min(h, w)
    y0, x0 = (h - side) // 2, (w - side) // 2
    img = cv2.resize(frame[y0:y0 + side, x0:x0 + side], (224, 224))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
    return (img / 127.5 - 1.0)[np.newaxis, ...]


def predict(model, class_map, frame):
    probs = model(preprocess(frame), training=False).numpy()[0]
    idx = int(np.argmax(probs))
    return class_map[idx], float(probs[idx])


def open_camera(index):
    """Open the webcam, trying several backends and keeping the first that gives a real picture.

    Some backends open fine but return black/garbage frames, so each one is checked.
    """
    try:
        cv2.setLogLevel(2)  # hide OpenCV's noisy warnings
    except Exception:
        pass
    backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF] if sys.platform == "win32" else [cv2.CAP_ANY]
    indexes = [index] if index is not None else [0, 1, 2, 3]
    fallback = None
    for idx in indexes:
        for backend in backends:
            cap = cv2.VideoCapture(idx, backend)
            if not cap.isOpened():
                cap.release()
                continue
            kind = "black"
            for _ in range(40):  # cameras need a moment to warm up
                ok, frame = cap.read()
                if ok and frame is not None and frame.std() > 3:
                    # Infrared (Windows Hello) cameras give a grey picture: all colour channels equal.
                    b, g, r = (frame[..., i].astype(np.int16) for i in range(3))
                    colourful = (np.abs(r - g).mean() + np.abs(g - b).mean()) > 1.0
                    kind = "colour" if colourful else "grey"
                    break
                time.sleep(0.05)
            if kind == "colour":
                print(f"Using camera {idx}.")
                if fallback is not None:
                    fallback[0].release()
                return cap
            if kind == "grey" and (fallback is None or fallback[1] == "black"):
                if fallback is not None:
                    fallback[0].release()
                fallback = (cap, kind, idx)
            elif fallback is None:
                fallback = (cap, kind, idx)
            else:
                cap.release()
    if fallback is not None:
        cap, kind, idx = fallback
        print(f"Warning: camera {idx} only gives a {kind} picture (maybe an infrared camera). "
              "Try --camera 1 or --camera 2, close other apps using the camera, "
              "and check Windows camera privacy settings.")
        return cap
    sys.exit("Could not open any camera.")


# --------------------------------------------------------------------------- #
# Drawing helpers
# --------------------------------------------------------------------------- #
FONT = cv2.FONT_HERSHEY_SIMPLEX


def text(img, s, pos, scale=1.0, color=(255, 255, 255), thickness=2, center=False):
    if center:
        (tw, _), _ = cv2.getTextSize(s, FONT, scale, thickness)
        pos = (pos[0] - tw // 2, pos[1])
    cv2.putText(img, s, pos, FONT, scale, (0, 0, 0), thickness + 3, cv2.LINE_AA)
    cv2.putText(img, s, pos, FONT, scale, color, thickness, cv2.LINE_AA)


def draw_scoreboard(img, you, cpu):
    text(img, f"You {you} - {cpu} Computer", (img.shape[1] // 2, 40), 1.0, center=True)


# --------------------------------------------------------------------------- #
# Main loop
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Rock-Paper-Scissors with a Teachable Machine model")
    ap.add_argument("--model", help=f"path to {MODEL_NAME} (default: auto-find)")
    ap.add_argument("--labels", help=f"path to {LABELS_NAME} (default: auto-find)")
    ap.add_argument("--camera", type=int, default=None,
                    help="camera index (default: auto-detect a colour webcam)")
    args = ap.parse_args()

    model_path = locate(args.model, MODEL_NAME)
    beside_model = model_path.parent / LABELS_NAME  # labels normally sit next to the model
    if not args.labels and beside_model.is_file():
        labels_path = beside_model
    else:
        labels_path = locate(args.labels, LABELS_NAME)
    print(f"Model:  {model_path}\nLabels: {labels_path}")
    class_map = parse_labels(labels_path.read_text(encoding="utf-8").splitlines())
    model = load_model(model_path)

    cap = open_camera(args.camera)

    user_score = cpu_score = 0
    state = "IDLE"
    computer_choice = user_choice = None
    votes = []
    round_start = result_start = last_predict = 0.0
    live = (None, 0.0)
    message = ""
    outcome = ""

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera read failed.")
                break
            frame = cv2.flip(frame, 1)  # mirror so it feels natural
            now = time.time()
            view = frame.copy()

            if state == "IDLE":
                text(view, "Press SPACE to start, Q to quit", (view.shape[1] // 2, view.shape[0] - 30),
                     0.9, center=True)
                if message:
                    text(view, message, (view.shape[1] // 2, view.shape[0] - 70), 0.8,
                         (0, 200, 255), center=True)

            elif state == "COUNTDOWN":
                elapsed = now - round_start
                if now - last_predict >= PREDICT_INTERVAL:
                    live = predict(model, class_map, frame)
                    votes.append((now, live[0], live[1]))
                    last_predict = now
                remaining = COUNTDOWN_SECONDS - elapsed
                h, w = view.shape[:2]
                text(view, str(max(1, int(np.ceil(remaining)))), (w // 2, h // 2 + 60), 6.0,
                     (0, 255, 255), 8, center=True)
                label = live[0] if live[0] and live[1] >= MIN_CONFIDENCE else "..."
                text(view, f"I see: {label}", (w // 2, h - 30), 1.0, center=True)
                text(view, "Show rock, paper or scissors!", (w // 2, 80), 0.9, center=True)

                if remaining <= 0:
                    user_choice = pick_choice(votes, now, now)
                    if user_choice is None:
                        message = "No clear gesture detected - round not counted."
                        state = "IDLE"
                    else:
                        winner = decide_winner(user_choice, computer_choice)
                        if winner == "user":
                            user_score += 1
                            outcome = "YOU WIN!"
                        elif winner == "computer":
                            cpu_score += 1
                            outcome = "COMPUTER WINS"
                        else:
                            outcome = "TIE"
                        message = ""
                        state = "RESULT"
                        result_start = now

            elif state == "RESULT":
                h, w = view.shape[:2]
                text(view, f"You: {user_choice}", (w // 2, h // 2 - 60), 1.4, center=True)
                text(view, f"Computer: {computer_choice}", (w // 2, h // 2), 1.4, center=True)
                color = {"YOU WIN!": (0, 255, 0), "COMPUTER WINS": (0, 0, 255)}.get(outcome, (0, 255, 255))
                text(view, outcome, (w // 2, h // 2 + 80), 2.0, color, 4, center=True)
                if now - result_start >= RESULT_SECONDS:
                    state = "IDLE"

            draw_scoreboard(view, user_score, cpu_score)
            cv2.imshow("Rock Paper Scissors", view)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q")):
                break
            if key == ord(" ") and state == "IDLE":
                computer_choice = random.choice(CHOICES)
                votes = []
                live = (None, 0.0)
                message = ""
                round_start = now
                state = "COUNTDOWN"
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"Final score - You {user_score} : {cpu_score} Computer")


if __name__ == "__main__":
    main()
