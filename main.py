"""
Time Capsule — write a message today, lock it until a future date.

The message is pushed to 0G storage immediately, but the app refuses to
show it back to you until the unlock date passes. Because the real data
lives on 0G (not just locally), the capsule survives even if you delete
and reinstall the app — only the date check is local.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import font as tkfont
import subprocess
import threading
import json
import os
import time
import uuid
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIDECAR_DIR = os.path.join(BASE_DIR, "sidecar")
CAPSULES_DIR = os.path.join(BASE_DIR, "capsules")
os.makedirs(CAPSULES_DIR, exist_ok=True)

CAPSULE_LOG = os.path.join(BASE_DIR, "capsules.json")

# ---------------- THEME ----------------
BG = "#0f1117"
PANEL = "#181b24"
PANEL_ALT = "#1f2330"
ACCENT = "#4d7cfe"
ACCENT_HOVER = "#6f97ff"
TEXT_PRIMARY = "#eef0f6"
TEXT_MUTED = "#8a8fa3"
GREEN = "#3ddc97"
RED = "#ff6b6b"
ORANGE = "#ffb454"
BORDER = "#2a2f3d"


def load_capsules():
    if os.path.exists(CAPSULE_LOG):
        with open(CAPSULE_LOG) as f:
            return json.load(f)
    return []


def save_capsules(data):
    with open(CAPSULE_LOG, "w") as f:
        json.dump(data, f, indent=2)


def push_to_0g(file_path, key, on_done):
    def worker():
        try:
            result = subprocess.run(
                ["node", "sync.js", "push", file_path, key],
                cwd=SIDECAR_DIR,
                timeout=60,
                capture_output=True,
                text=True,
            )
            tx_data = None
            for line in result.stdout.splitlines():
                if line.startswith("RESULT_JSON:"):
                    tx_data = json.loads(line[len("RESULT_JSON:"):])
            on_done(tx_data, result.stdout, result.stderr)
        except Exception as e:
            on_done(None, "", str(e))

    threading.Thread(target=worker, daemon=True).start()


class RoundButton(tk.Canvas):
    """A simple flat button with hover effect, since ttk buttons are hard to theme well."""

    def __init__(self, parent, text, command, bg=ACCENT, hover=ACCENT_HOVER,
                 fg="#0b0d12", width=260, height=44, font=None, **kwargs):
        super().__init__(parent, width=width, height=height, bg=parent["bg"],
                          highlightthickness=0, **kwargs)
        self.command = command
        self.bg_color = bg
        self.hover_color = hover
        self.fg_color = fg
        self.font = font or ("Segoe UI", 11, "bold")
        self.width = width
        self.height = height

        self.rect = self.create_rounded_rect(2, 2, width - 2, height - 2, radius=10, fill=bg, outline="")
        self.label = self.create_text(width // 2, height // 2, text=text, fill=fg, font=self.font)

        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def create_rounded_rect(self, x1, y1, x2, y2, radius=12, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _on_enter(self, _e):
        self.itemconfig(self.rect, fill=self.hover_color)
        self.config(cursor="hand2")

    def _on_leave(self, _e):
        self.itemconfig(self.rect, fill=self.bg_color)


class TimeCapsuleApp:
    def __init__(self, root):
        self.root = root
        root.title("Time Capsule")
        root.geometry("560x680")
        root.minsize(480, 600)
        root.configure(bg=BG)

        # ---------------- HEADER ----------------
        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=28, pady=(28, 6))

        tk.Label(header, text="⏳ Time Capsule", bg=BG, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(header, text="Write a message to your future self — sealed on 0G.",
                 bg=BG, fg=TEXT_MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

        # ---------------- WRITE PANEL ----------------
        panel = tk.Frame(root, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        panel.pack(fill="x", padx=28, pady=(18, 10))

        inner = tk.Frame(panel, bg=PANEL)
        inner.pack(fill="both", expand=True, padx=18, pady=18)

        self.text = tk.Text(inner, height=7, wrap="word", font=("Segoe UI", 10),
                             bg=PANEL_ALT, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                             relief="flat", padx=12, pady=10, highlightthickness=1,
                             highlightbackground=BORDER, highlightcolor=ACCENT)
        self.text.pack(fill="both", expand=True)

        controls = tk.Frame(inner, bg=PANEL)
        controls.pack(fill="x", pady=(14, 0))

        tk.Label(controls, text="Unlock in", bg=PANEL, fg=TEXT_MUTED,
                 font=("Segoe UI", 10)).pack(side="left")

        self.days_var = tk.StringVar(value="7")
        spin = tk.Spinbox(controls, from_=1, to=3650, width=5, textvariable=self.days_var,
                           font=("Segoe UI", 10), relief="flat", bg=PANEL_ALT, fg=TEXT_PRIMARY,
                           insertbackground=TEXT_PRIMARY, buttonbackground=PANEL_ALT,
                           highlightthickness=1, highlightbackground=BORDER)
        spin.pack(side="left", padx=(8, 6))

        tk.Label(controls, text="days", bg=PANEL, fg=TEXT_MUTED,
                 font=("Segoe UI", 10)).pack(side="left")

        seal_btn = RoundButton(controls, "Seal & Send to 0G  →", self.seal_capsule,
                                width=200, height=40)
        seal_btn.pack(side="right")

        # ---------------- STATUS ----------------
        self.status_label = tk.Label(root, text=" ", bg=BG, fg=TEXT_MUTED,
                                      font=("Segoe UI", 9))
        self.status_label.pack(padx=28, pady=(2, 14), anchor="w")

        # ---------------- HISTORY ----------------
        hist_header = tk.Frame(root, bg=BG)
        hist_header.pack(fill="x", padx=28)
        tk.Label(hist_header, text="Your capsules", bg=BG, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(hist_header, text="Double-click a capsule to try opening it.",
                 bg=BG, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 8))

        list_panel = tk.Frame(root, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        list_panel.pack(fill="both", expand=True, padx=28, pady=(0, 28))

        scrollbar = tk.Scrollbar(list_panel)
        scrollbar.pack(side="right", fill="y")

        self.capsule_list = tk.Listbox(
            list_panel, bg=PANEL, fg=TEXT_PRIMARY, font=("Segoe UI", 10),
            relief="flat", highlightthickness=0, selectbackground=ACCENT,
            selectforeground="#0b0d12", activestyle="none",
            yscrollcommand=scrollbar.set,
        )
        self.capsule_list.pack(fill="both", expand=True, padx=4, pady=4)
        scrollbar.config(command=self.capsule_list.yview)
        self.capsule_list.bind("<Double-Button-1>", self.try_open_capsule)

        self.refresh_list()

    # ---------------- LOGIC (unchanged) ----------------

    def refresh_list(self):
        self.capsule_list.delete(0, tk.END)
        capsules = load_capsules()
        if not capsules:
            self.capsule_list.insert(tk.END, "  No capsules yet — write one above.")
            return
        for c in capsules:
            unlock = datetime.fromisoformat(c["unlock_at"])
            if datetime.now() >= unlock:
                status = "🔓 Unlocked"
            else:
                status = f"🔒 Locked until {unlock.strftime('%b %d, %Y')}"
            h = (c.get("rootHash") or "pending")[:14]
            self.capsule_list.insert(tk.END, f"  {c['id']}   •   {status}   •   {h}...")

    def seal_capsule(self):
        content = self.text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showinfo("Empty", "Write something first.")
            return

        try:
            days = int(self.days_var.get())
        except ValueError:
            days = 7

        capsule_id = str(uuid.uuid4())[:8]
        unlock_at = datetime.now() + timedelta(days=days)
        file_path = os.path.join(CAPSULES_DIR, f"{capsule_id}.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        capsules = load_capsules()
        capsules.append({
            "id": capsule_id,
            "created_at": datetime.now().isoformat(),
            "unlock_at": unlock_at.isoformat(),
            "rootHash": None,
        })
        save_capsules(capsules)
        self.refresh_list()
        self.text.delete("1.0", tk.END)
        self.status_label.config(text="⏳ Sealing on 0G...", fg=ORANGE)

        def on_done(tx_data, stdout, stderr):
            capsules = load_capsules()
            for c in capsules:
                if c["id"] == capsule_id and tx_data:
                    c["rootHash"] = tx_data.get("dataMerkleRoot") or tx_data.get("rootHash")
            save_capsules(capsules)

            def update_ui():
                self.refresh_list()
                if tx_data:
                    self.status_label.config(text="✅ Capsule sealed on 0G", fg=GREEN)
                else:
                    self.status_label.config(text="⚠ 0G push failed — saved locally only", fg=RED)
                    print("STDOUT:", stdout)
                    print("STDERR:", stderr)

            self.root.after(0, update_ui)

        push_to_0g(file_path, capsule_id, on_done)

    def try_open_capsule(self, event):
        sel = self.capsule_list.curselection()
        if not sel:
            return
        capsules = load_capsules()
        if not capsules or sel[0] >= len(capsules):
            return
        capsule = capsules[sel[0]]
        unlock = datetime.fromisoformat(capsule["unlock_at"])

        if datetime.now() < unlock:
            remaining = unlock - datetime.now()
            messagebox.showinfo("Still locked", f"This capsule unlocks in {remaining.days} day(s).")
            return

        file_path = os.path.join(CAPSULES_DIR, f"{capsule['id']}.txt")
        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            messagebox.showinfo("Capsule unlocked", content)
        else:
            messagebox.showinfo("Capsule unlocked", "(local copy missing — would need to pull from 0G by root hash)")


if __name__ == "__main__":
    root = tk.Tk()
    app = TimeCapsuleApp(root)
    root.mainloop()
