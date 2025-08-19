

import os
import json
import webbrowser
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import requests

APP_TITLE = "📍 Image Location Finder"
SAVE_FILE = "history.json"
HEADER_HEIGHT = 70

NO_GPS_REASON_TEXT = (
    "No GPS data found because:\n"
    "1) The sender stripped location data before sending, OR\n"
    "2) The camera’s location setting was OFF when the photo was taken."
)

def load_history():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history():
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def extract_exif(image_path: str) -> dict:
    try:
        image = Image.open(image_path)
        if not hasattr(image, "_getexif"):
            return {}
        raw = image._getexif()
        if not raw or not isinstance(raw, dict):
            return {}
        exif = {}
        for k, v in raw.items():
            tag = TAGS.get(k, k)
            if tag == "GPSInfo" and isinstance(v, dict):
                gps = {}
                for sub_k, sub_v in v.items():
                    gps_tag = GPSTAGS.get(sub_k, sub_k)
                    gps[gps_tag] = sub_v
                exif["GPSInfo"] = gps
            else:
                exif[tag] = v
        return exif
    except Exception:
        return {}

def _to_float(x):
    try:
        return float(x)
    except Exception:
        try:
            return float(x[0]) / float(x[1])
        except Exception:
            return None

def convert_to_degrees(value):
    try:
        d = _to_float(value[0])
        m = _to_float(value[1])
        s = _to_float(value[2])
        if None in (d, m, s):
            return None
        return d + (m / 60.0) + (s / 3600.0)
    except Exception:
        return None

def get_lat_lon(exif: dict):
    gps = exif.get("GPSInfo") or {}
    try:
        lat = convert_to_degrees(gps["GPSLatitude"])
        lon = convert_to_degrees(gps["GPSLongitude"])
        if lat is None or lon is None:
            return None
        if gps.get("GPSLatitudeRef") and gps["GPSLatitudeRef"] != "N":
            lat = -lat
        if gps.get("GPSLongitudeRef") and gps["GPSLongitudeRef"] != "E":
            lon = -lon
        return (lat, lon)
    except Exception:
        return None

def get_address(lat, lon) -> str:
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"format": "json", "lat": lat, "lon": lon}
        headers = {"User-Agent": "ImageLocationFinder/1.0 (desktop app)"}
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return data.get("display_name", "Address not found")
        return "Address not found"
    except Exception:
        return "Address not found"

def open_image_file(path: str):
    try:
        if os.name == "nt":
            os.startfile(path)
        elif sys.platform == "darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')
    except Exception:
        webbrowser.open(f"file:///{path}")

def open_in_maps(lat, lon):
    webbrowser.open(f"https://www.google.com/maps?q={lat},{lon}")

def upload_image():
    file_path = filedialog.askopenfilename(
        title="Select Image",
        filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.webp")]
    )
    if not file_path:
        status_label.configure(text="No file selected.")
        return

    exif = extract_exif(file_path)
    coords = get_lat_lon(exif)

    if not coords:
        item = {
            "status": "no_gps",
            "name": os.path.basename(file_path),
            "path": file_path,
            "reason": NO_GPS_REASON_TEXT
        }
        history.append(item)
        save_history()
        status_label.configure(text=f"Saved (no GPS): {item['name']}")
        refresh_history()
        return

    lat, lon = coords
    address = get_address(lat, lon)

    item = {
        "status": "ok",
        "name": os.path.basename(file_path),
        "path": file_path,
        "lat": lat,
        "lon": lon,
        "address": address
    }
    history.append(item)
    save_history()
    status_label.configure(text=f"Saved: {item['name']}")
    refresh_history()

def delete_entry(item):
    if messagebox.askyesno("Confirm Delete", f"Delete '{item['name']}' from history?"):
        try:
            history.remove(item)
            save_history()
            refresh_history()
            status_label.configure(text=f"Deleted: {item['name']}")
        except ValueError:
            pass

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title(APP_TITLE)
root.geometry("960x760")  # widened
root.minsize(920, 700)

header_container = ctk.CTkFrame(root, fg_color="transparent")
header_container.pack(fill="x", pady=(0, 8))

canvas = tk.Canvas(header_container, height=HEADER_HEIGHT, highlightthickness=0, bd=0)
canvas.pack(fill="x")

def draw_gradient():
    canvas_width = canvas.winfo_width() or 860
    canvas.delete("grad")
    for x in range(canvas_width):
        r = int(0 + (132 - 0) * (x / max(1, canvas_width)))
        g = int(201 + (94 - 201) * (x / max(1, canvas_width)))
        b = int(167 + (194 - 167) * (x / max(1, canvas_width)))
        color = f"#{r:02x}{g:02x}{b:02x}"
        canvas.create_line(x, 0, x, HEADER_HEIGHT, fill=color, tags="grad")
    canvas.create_text(
        canvas_width // 2, HEADER_HEIGHT // 2,
        text=APP_TITLE, fill="white",
        font=("Segoe UI", 20, "bold"), tags="grad"
    )

canvas.bind("<Configure>", lambda e: draw_gradient())
root.after(50, draw_gradient)

top_box = ctk.CTkFrame(root, fg_color="#1f2233", corner_radius=12)
top_box.pack(fill="x", padx=12, pady=(0, 8))
top_box.grid_columnconfigure(0, weight=1)

upload_container = ctk.CTkFrame(top_box, fg_color="transparent")
upload_container.grid(row=0, column=0, pady=(12, 6), sticky="nsew")

upload_btn = ctk.CTkButton(
    upload_container,
    text="📂 Upload Image (Use Document mode in WhatsApp)",
    font=ctk.CTkFont(size=14, weight="bold"),
    fg_color="#22C55E", hover_color="#16A34A",
    command=upload_image
)
upload_btn.pack(padx=12, pady=8, anchor="center")

info_text = (
    "Note: Upload an image that was sent as a *Document*.\n"
    "If GPS is missing, either the sender stripped it OR the camera’s location was OFF when taken."
)
info_label = ctk.CTkLabel(top_box, text=info_text, text_color="#9aa0a6", justify="center", wraplength=800)
info_label.grid(row=1, column=0, pady=(0, 12), sticky="n")

status_label = ctk.CTkLabel(root, text="", text_color="#c0c5ce", wraplength=880, justify="left")
status_label.pack(fill="x", padx=16, pady=(0, 8))

history_frame = ctk.CTkScrollableFrame(root, width=900, height=600, corner_radius=12, fg_color="#131624")
history_frame.pack(padx=12, pady=6, fill="both", expand=True)

_thumbnail_refs = {}

def make_thumbnail(img_path, max_size=(96, 96)):
    try:
        im = Image.open(img_path)
        im.thumbnail(max_size)
        return ctk.CTkImage(light_image=im, dark_image=im, size=im.size)
    except Exception:
        from PIL import Image as PILImage
        placeholder = PILImage.new("RGB", max_size, (60, 60, 60))
        return ctk.CTkImage(light_image=placeholder, dark_image=placeholder, size=max_size)

def refresh_history():
    for w in history_frame.winfo_children():
        w.destroy()

    if not history:
        empty = ctk.CTkLabel(history_frame, text="No saved items yet. Upload an image to get started.", text_color="#7c818c")
        empty.pack(pady=16)
        return

    for idx, item in enumerate(history):
        row = ctk.CTkFrame(history_frame, corner_radius=12, fg_color="#1b1f30")
        row.pack(fill="x", padx=8, pady=8)

        thumb = make_thumbnail(item["path"])
        _thumbnail_refs[idx] = thumb
        img_btn = ctk.CTkButton(
            row, image=thumb, text="",
            width=100, height=100,
            fg_color="transparent", hover_color="#232844",
            command=lambda p=item["path"]: open_image_file(p)
        )
        img_btn.grid(row=0, column=0, rowspan=4, padx=10, pady=10)

        name_lbl = ctk.CTkLabel(row, text=item["name"], font=ctk.CTkFont(size=14, weight="bold"))
        name_lbl.grid(row=0, column=1, sticky="w", padx=6, pady=(10, 2))

        path_lbl = ctk.CTkLabel(row, text=item["path"], text_color="#9aa0a6",
                                font=ctk.CTkFont(size=11), wraplength=740, justify="left")
        path_lbl.grid(row=1, column=1, sticky="w", padx=6)

        if item.get("status") == "ok":
            addr = item.get("address", "Address not found")
            details_text = f"{addr}\nLat: {round(item['lat'], 6)}   Lon: {round(item['lon'], 6)}"
        else:
            details_text = item.get("reason", NO_GPS_REASON_TEXT)

        details_lbl = ctk.CTkLabel(row, text=details_text, wraplength=740, justify="left")
        details_lbl.grid(row=2, column=1, sticky="w", padx=6, pady=(2, 10))

        btns = ctk.CTkFrame(row, fg_color="transparent")
        btns.grid(row=0, column=2, rowspan=4, padx=8, pady=8, sticky="e")

        if item.get("status") == "ok":
            maps_btn = ctk.CTkButton(
                btns, text="Open in Google Maps",
                fg_color="#3B82F6", hover_color="#2563EB",
                command=lambda lt=item["lat"], ln=item["lon"]: open_in_maps(lt, ln)
            )
            maps_btn.pack(padx=6, pady=(8, 6), fill="x")

        del_btn = ctk.CTkButton(
            btns, text="❌ Delete",
            fg_color="#DC2626", hover_color="#B91C1C",
            command=lambda it=item: delete_entry(it)
        )
        del_btn.pack(padx=6, pady=(0, 8), fill="x")

        row.grid_columnconfigure(1, weight=1)

history = load_history()
refresh_history()
root.mainloop()
