# Rock-Paper-Scissors with Teachable Machine

Play rock-paper-scissors against the computer using your own
[Teachable Machine](https://teachablemachine.withgoogle.com/) image model.

## Setup
1. Train an **Image Project** with classes named `Rock`, `Paper`, `Scissors` (an extra
   "Nothing" class is fine).
2. Export: **Tensorflow > Keras > Download my model**, then unzip.
3. Rename the model file and keep the labels file name exactly as shown:
   - `keras_model.h5` → rename it to **`keras_model_rps.h5`**
   - `labels.txt` (unchanged)

   Put them next to `rps_game.py`, or leave them in Downloads / Desktop / Documents
   (an unzipped folder inside those works too).
4. Install Python 3.11 if you don't have it (https://www.python.org/downloads/, tick
   "Add python.exe to PATH").

## Play
Double-click **`play.bat`**. The first run installs all libraries automatically
(a few minutes, needs internet); after that it starts right away.

**Mac:** open Terminal in this folder and run `bash play.command` (or
`chmod +x play.command` once, then double-click it). When macOS asks, allow Terminal to
use the camera. Mac users: it's the same game; `play.bat` is Windows only.

Manual alternative: `pip install -r requirements.txt` then `python rps_game.py`.
- **SPACE** – start a round. You have 5 seconds to show your hand to the camera.
- **Q** – quit.

Ties don't change the score. Options: `--model PATH`, `--labels PATH`, `--camera N`.
