#!/usr/bin/env python3
"""
Generate an animated GIF demo for git-cl using real command output.

Sets up a temporary Git repo, runs actual git-cl commands, captures
the output, and renders an animated terminal GIF.
"""

import os
import shlex
import subprocess
import tempfile
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ─── Config ──────────────────────────────────────────────────────────────────

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_SIZE = 15
LINE_HEIGHT = 22
CHAR_WIDTH = 9

PAD_X = 20
PAD_Y = 14
TITLE_BAR_H = 32

BG = (30, 30, 46)
TITLE_BG = (40, 40, 58)
FG = (205, 214, 244)
PROMPT_COL = (166, 227, 161)
DIM = (140, 140, 160)
CL_NAME = (137, 180, 250)
STATUS_RED = (243, 139, 168)
STATUS_BLUE = (137, 180, 250)
STATUS_GREEN = (166, 227, 161)
YELLOW = (249, 226, 175)

TYPING_DELAY = 35
PAUSE_SHORT = 500
PAUSE_MEDIUM = 1400
PAUSE_LONG = 2800
PAUSE_XLONG = 3500

WIDTH = 750

font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
font_bold = ImageFont.truetype(FONT_BOLD_PATH, FONT_SIZE)


# ─── Colourising output ──────────────────────────────────────────────────────

def colourise_line(line: str) -> list[tuple[str, tuple]]:
    """Parse a line of git-cl output and return coloured segments."""
    stripped = line.rstrip()

    # Changelist header: "name:" at start of line
    if stripped.endswith(":") and not stripped.startswith(" "):
        return [(stripped, CL_NAME)]

    # Status line: "  [ M] filename"
    if stripped.startswith("  ["):
        bracket_end = stripped.index("]") + 1
        code = stripped[:bracket_end]
        rest = stripped[bracket_end:]
        # Colour the status code
        inner = code.strip()[1:-1]  # e.g. " M" or "??"
        if inner == "??":
            code_col = STATUS_BLUE
        elif inner[0] != " ":
            code_col = STATUS_GREEN
        else:
            code_col = STATUS_RED
        return [(code, code_col), (rest, FG)]

    # "Added to..." confirmation
    if stripped.startswith("Added to"):
        return [(stripped, DIM)]

    # Branch workflow messages
    if stripped.startswith("Creating branch") or stripped.startswith("Ready to work"):
        return [(stripped, STATUS_GREEN)]
    if stripped.startswith("Stashing") or stripped.startswith("Switched to") or stripped.startswith("Restored"):
        return [(stripped, FG)]
    if stripped.startswith("Note:"):
        return [(stripped, DIM)]

    # Stashed changelists section
    if stripped.startswith("Stashed Changelist"):
        return [(stripped, YELLOW)]
    if stripped.startswith("  ") and ("file" in stripped) and ("20" in stripped):
        return [(stripped, DIM)]

    # Blank
    if not stripped:
        return [("", FG)]

    return [(stripped, FG)]


# ─── Run real commands ────────────────────────────────────────────────────────

def setup_repo():
    """Create a temp repo, run the demo commands, return (command, output) pairs."""
    repo_dir = Path(tempfile.mkdtemp(prefix="git-cl-demo."))

    env = {**os.environ, "NO_COLOR": "1", "PATH": os.path.expanduser("~/bin") + ":" + os.environ["PATH"]}

    def run(cmd_str):
        args = shlex.split(cmd_str)
        result = subprocess.run(args, capture_output=True, text=True, cwd=repo_dir, env=env)
        return (result.stdout + result.stderr).strip()

    # Set up repo
    run("git init --quiet")
    run("git config user.email demo@git-cl.test")
    run("git config user.name git-cl-demo")

    # Create and commit files
    for f in ["clean_data.py", "filters.py", "math.py", "plot.py", "charts.py", "test.py"]:
        (repo_dir / f).write_text(f"# {f}\n")
    run("git add clean_data.py filters.py math.py plot.py charts.py test.py")
    run("git commit --quiet -m Initial")

    # Modify all
    for f in ["clean_data.py", "filters.py", "math.py", "plot.py", "charts.py", "test.py"]:
        (repo_dir / f).write_text(f"# {f} modified\n")

    # Demo commands
    commands = [
        ("git cl add preprocessing clean_data.py filters.py math.py", PAUSE_SHORT),
        ("git cl add visualisation plot.py charts.py", PAUSE_SHORT),
        ("git cl add tests test.py", PAUSE_SHORT),
        ("git cl status", PAUSE_XLONG),
        ("git cl branch preprocessing", PAUSE_LONG),
        ("git cl status", PAUSE_XLONG),
    ]

    results = []
    for cmd, pause in commands:
        output = run(cmd)
        # Filter out git's stderr "Switched to a new branch..." since
        # git-cl prints its own version of this message
        output_lines = []
        seen_switched = False
        for line in output.split("\n"):
            if "Switched to" in line:
                if seen_switched:
                    continue  # skip duplicate
                seen_switched = True
            output_lines.append(line)
        results.append((cmd, "\n".join(output_lines), pause))

    # Cleanup
    shutil.rmtree(repo_dir)
    return results


# ─── Frame rendering ─────────────────────────────────────────────────────────

def make_frame(lines, cursor_line=None, cursor_col=None):
    """Render a terminal frame."""
    content_h = len(lines) * LINE_HEIGHT + PAD_Y * 2
    h = TITLE_BAR_H + content_h
    img = Image.new("RGB", (WIDTH, h), BG)
    draw = ImageDraw.Draw(img)

    # Title bar
    draw.rectangle([0, 0, WIDTH, TITLE_BAR_H], fill=TITLE_BG)
    for i, col in enumerate([(243, 139, 168), (249, 226, 175), (166, 227, 161)]):
        draw.ellipse([12 + i * 22, 10, 24 + i * 22, 22], fill=col)
    title = "git-cl demo"
    tw = draw.textlength(title, font=font)
    draw.text(((WIDTH - tw) / 2, 7), title, fill=DIM, font=font)

    # Content
    y = TITLE_BAR_H + PAD_Y
    for i, segments in enumerate(lines):
        x = PAD_X
        for text, colour in segments:
            draw.text((x, y), text, fill=colour, font=font)
            x += draw.textlength(text, font=font)
        if cursor_line == i and cursor_col is not None:
            cx = PAD_X
            full_text = "".join(t for t, _ in segments)
            cx += draw.textlength(full_text[:cursor_col], font=font)
            draw.rectangle([cx, y, cx + CHAR_WIDTH, y + LINE_HEIGHT - 2], fill=(150, 150, 180))
        y += LINE_HEIGHT

    return img


def generate_frames(command_results):
    """Walk through captured command results and yield (image, duration_ms)."""
    lines = []
    prompt = [("$ ", PROMPT_COL)]

    for cmd, output, pause in command_results:
        # Type the command
        cmd_line_idx = len(lines)
        lines.append(list(prompt))
        for i in range(len(cmd)):
            partial = cmd[:i + 1]
            lines[cmd_line_idx] = list(prompt) + [(partial, FG)]
            yield make_frame(lines, cursor_line=cmd_line_idx, cursor_col=len("$ ") + i + 1), TYPING_DELAY
        # Full command, brief pause
        lines[cmd_line_idx] = list(prompt) + [(cmd, FG)]
        yield make_frame(lines), 120

        # Show output lines
        if output.strip():
            # Small pause before output appears
            yield make_frame(lines), 200

            for out_line in output.split("\n"):
                segments = colourise_line(out_line)
                lines.append(segments)
                yield make_frame(lines), 40

        # Pause to read
        yield make_frame(lines), pause

    # Final prompt
    lines.append(list(prompt))
    yield make_frame(lines, cursor_line=len(lines) - 1, cursor_col=2), 4000


# ─── GIF assembly ─────────────────────────────────────────────────────────────

def save_gif(filepath, frames):
    if not frames:
        return

    max_h = max(f.height for f, _ in frames)
    max_w = max(f.width for f, _ in frames)

    padded = []
    for img, dur in frames:
        if img.height < max_h or img.width < max_w:
            new = Image.new("RGB", (max_w, max_h), BG)
            new.paste(img, (0, 0))
            padded.append((new, dur))
        else:
            padded.append((img, dur))

    images = [f for f, _ in padded]
    durations = [d for _, d in padded]

    images[0].save(
        filepath,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        optimize=False,
    )
    print(f"Saved {filepath} ({len(images)} frames, {max_w}x{max_h})")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running real git-cl commands...")
    results = setup_repo()

    print("\nCaptured output:")
    for cmd, output, _ in results:
        print(f"  $ {cmd}")
        for line in output.split("\n"):
            print(f"    {line}")

    print("\nRendering GIF...")
    frames = list(generate_frames(results))
    save_gif("git-cl-demo.gif", frames)
