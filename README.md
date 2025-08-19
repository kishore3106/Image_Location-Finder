# 📍 Image Location Finder

**Image Location Finder** is a lightweight desktop application that helps you extract and display the GPS location embedded in an image’s metadata (EXIF data).  
If available, it shows the exact **latitude, longitude, and address**, and lets you open the location in **Google Maps** directly.  

If GPS is missing, the app also explains possible reasons — such as the camera’s location setting being off, or GPS data being stripped when the photo was shared.

---

## ✨ Features
- Upload any supported image (`.jpg`, `.jpeg`, `.png`, `.webp`)  
- Extract and display GPS coordinates & full address  
- Open location directly in Google Maps  
- Keeps a **history** of previously uploaded images (with thumbnails)  
- Saves cases where GPS is not found along with reasons  
- Simple and modern **dark-themed UI**  

---

## 📦 How to Run

Inside the repository, you’ll find a folder:  

In that folder, there is a ready-to-use **`.exe` file** (`ImageLocationFinder.exe`).  
You can double-click it to run the app without needing Python installed.

⚠️ **Note:**  
Windows Defender (or other antivirus) may sometimes flag `.exe` files generated with PyInstaller.  
If that happens, please temporarily turn off Windows Defender or whitelist the file.  
This app is completely safe and only processes images locally.

---

## 🖥️ Usage
1. Launch the app (`ImageLocationFinder.exe` or run the Python script).  
2. Click **Upload Image** and select your photo.  
3. If GPS is found:
   - View the address, latitude, and longitude.  
   - Click **"Open in Google Maps"** to view location.  
4. If GPS is missing:
   - The app will save it to history with possible reasons.  

---

## 📌 Why GPS Data May Be Missing
- The sender shared the image through WhatsApp/Telegram without using **Document mode**, which strips GPS data.  
- The camera’s **location setting** was OFF when the photo was taken.  

---

## 🛠️ Full Source Code

```python
import os
import json
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS, GPSTAGS
import requests

# ------------------------- Config -------------------------
APP_TITLE = "📍 Image Location Finder"
SAVE_FILE = "history.json"
HEADER_HEIGHT = 70

NO_GPS_REASON_TEXT = (
    "❌ No GPS data found.\n\n"
    "Possible reasons:\n"
    "1. The sender ripped the location when sending.\n"
    "2. Location option was denied when the image was taken."
)

# ------------------------- Helpers -------------------------
def extract_gps(image_path):
    try:
        img = Image.open(image_path)
        exif = img._getexif()
        if not exif:
            return None
        gps_info = {}
        for tag, value in exif.items():
            tag_name = TAGS.get(tag)
            if tag_name == "GPSInfo":
                for key in value.keys():
                    gps_info[GPSTAGS.get(key)] = value[key]
        if not gps_info:
            return None

        def conv(coord, ref):
            d, m, s = coord
            decimal = d[0] / d[1] + (m[0] / m[1]) / 60 + (s[0] / s[1]) / 3600
            if ref in ["S", "W"]:
                decimal = -decimal
            return decimal

        lat = conv(gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"])
        lon = conv(gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"])
        return lat, lon
    except Exception:
        return None

def get_address(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        resp = requests.get(url, headers={"User-Agent": "ImageLocationFinderApp"})
        if resp.status_code == 200:
            return resp.json().get("display_name", "Unknown address")
    except:
        return "Unknown address"
    return "Unknown address"

def save_history(entry):
    history = []
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            try:
                history = json.load(f)
            except:
                history = []
    history.insert(0, entry)
    with open(SAVE_FILE, "w") as f:
        json.dump(history, f, indent=4)

def load_history():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

# ------------------------- GUI -------------------------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1000x700")

        self.history_frame = ctk.CTkScrollableFrame(self, width=350)
        self.history_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)

        header = ctk.CTkFrame(self.main_frame, height=HEADER_HEIGHT)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)

        upload_btn = ctk.CTkButton(header, text="📤 Upload Image", command=self.upload_image)
        upload_btn.pack(expand=True)

        self.output = ctk.CTkTextbox(self.main_frame, wrap="word", height=200)
        self.output.pack(expand=True, fill="both", padx=10, pady=10)

        self.image_label = ctk.CTkLabel(self.main_frame, text="")
        self.image_label.pack(pady=10)

        self.refresh_history()

    def upload_image(self):
        file = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")])
        if not file:
            return

        img = Image.open(file)
        img.thumbnail((300, 300))
        photo = ImageTk.PhotoImage(img)
        self.image_label.configure(image=photo, text="")
        self.image_label.image = photo

        coords = extract_gps(file)
        if coords:
            lat, lon = coords
            addr = get_address(lat, lon)
            result = f"✅ GPS Found!\n\nLatitude: {lat}\nLongitude: {lon}\n\nAddress:\n{addr}"
            self.output.delete("1.0", "end")
            self.output.insert("end", result)

            save_history({"path": file, "coords": (lat, lon), "address": addr, "status": "success"})
        else:
            self.output.delete("1.0", "end")
            self.output.insert("end", NO_GPS_REASON_TEXT)
            save_history({"path": file, "status": "failed", "reason": NO_GPS_REASON_TEXT})

        self.refresh_history()

    def refresh_history(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        history = load_history()
        for entry in history:
            frame = ctk.CTkFrame(self.history_frame)
            frame.pack(fill="x", padx=5, pady=5)

            img = Image.open(entry["path"])
            img.thumbnail((60, 60))
            photo = ImageTk.PhotoImage(img)

            img_label = ctk.CTkLabel(frame, image=photo, text="")
            img_label.image = photo
            img_label.pack(side="left", padx=5)

            text = entry["status"]
            if entry["status"] == "success":
                text = f"✅ {entry['address']}"
            else:
                text = f"❌ {entry['reason'].splitlines()[0]}"

            lbl = ctk.CTkLabel(frame, text=text, anchor="w", justify="left", wraplength=250)
            lbl.pack(side="left", fill="x", expand=True, padx=5)

            if entry["status"] == "success":
                def open_map(lat=entry["coords"][0], lon=entry["coords"][1]):
                    webbrowser.open(f"https://www.google.com/maps?q={lat},{lon}")
                btn = ctk.CTkButton(frame, text="🌍 Open", width=60, command=open_map)
                btn.pack(side="right", padx=5)

if __name__ == "__main__":
    app = App()
    app.mainloop()
```

## 📸 Screenshots

### 🔹 Home Screen
<img width="1920" height="1200" alt="Screenshot (158)" src="https://github.com/user-attachments/assets/69a4303b-77d5-4f93-9e60-4f6e0c671397" />


### 🔹 Extracted Location
<img width="1849" height="1096" alt="Screenshot 2025-08-19 090405" src="https://github.com/user-attachments/assets/d2d06d14-e89a-4594-a130-427d9cafa8a0" />

