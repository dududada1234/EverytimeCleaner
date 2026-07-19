import os
import sys
import random

_IMG_CACHE = []
_LAST_ERROR = None


def get_resource_path(relative_path):
    """exe 옆 폴더 — 사용자가 직접 수정하는 파일 (config.json, chromedriver 등)"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, relative_path)


def get_bundled_path(relative_path):
    """exe 내부 번들 리소스 — --add-data로 넣은 이미지 등 (--onefile은 임시폴더에 풀림)"""
    base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base, relative_path)


def get_asset_path(filename):
    """번들 폴더 우선, 없으면 exe 옆 폴더"""
    p = get_bundled_path(os.path.join("assets", filename))
    if os.path.exists(p):
        return p
    return get_resource_path(os.path.join("assets", filename))


def last_image_error():
    return _LAST_ERROR


def rand_delay(lo=1.5, hi=3.0):
    if lo > hi:
        lo, hi = hi, lo
    return random.uniform(lo, hi)


def load_gif_frames(filename, size=None):
    """애니메이션 GIF → (프레임 리스트, 딜레이 리스트). 실패하면 (None, None)."""
    global _LAST_ERROR
    import tkinter as tk

    path = get_asset_path(filename)          # ← 핵심 수정

    if not os.path.exists(path):
        _LAST_ERROR = f"파일 없음: {path}"
        return None, None

    # 1순위: Pillow
    try:
        from PIL import Image, ImageTk, ImageSequence
        img = Image.open(path)
        frames, delays = [], []
        for f in ImageSequence.Iterator(img):
            fr = f.convert("RGBA")
            if size:
                fr.thumbnail(size, Image.LANCZOS)
            frames.append(ImageTk.PhotoImage(fr))
            delays.append(max(f.info.get("duration", 80), 20))
        if frames:
            _IMG_CACHE.extend(frames)
            _LAST_ERROR = None
            return frames, delays
        _LAST_ERROR = "Pillow: 프레임 0개"
    except ImportError:
        _LAST_ERROR = "Pillow 미설치 → tkinter 폴백"
    except Exception as e:
        _LAST_ERROR = f"Pillow 실패: {type(e).__name__}: {e}"

    # 2순위: tkinter 전용 (Pillow 없어도 동작, 리사이즈는 안 됨)
    try:
        frames = []
        i = 0
        while True:
            try:
                frames.append(tk.PhotoImage(file=path, format=f"gif -index {i}"))
                i += 1
            except tk.TclError:
                break
        if not frames:
            _LAST_ERROR = f"tkinter도 프레임을 읽지 못함: {path}"
            return None, None
        _IMG_CACHE.extend(frames)
        _LAST_ERROR = None
        return frames, [80] * len(frames)
    except Exception as e:
        _LAST_ERROR = f"tkinter 실패: {type(e).__name__}: {e}"
        return None, None


def load_image(filename, size=None):
    """정지 이미지 로드. 실패하면 None."""
    global _LAST_ERROR
    path = get_asset_path(filename)          # ← 핵심 수정
    if not os.path.exists(path):
        _LAST_ERROR = f"파일 없음: {path}"
        return None

    try:
        from PIL import Image, ImageTk
        img = Image.open(path).convert("RGBA")
        if size:
            img.thumbnail(size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
    except ImportError:
        import tkinter as tk
        try:
            photo = tk.PhotoImage(file=path)
        except Exception as e:
            _LAST_ERROR = f"{type(e).__name__}: {e}"
            return None
    except Exception as e:
        _LAST_ERROR = f"{type(e).__name__}: {e}"
        return None

    _IMG_CACHE.append(photo)
    return photo