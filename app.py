import os
import platform
import subprocess
from rembg import remove
from PIL import Image, ImageTk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog, Text, END
from tkinterdnd2 import DND_FILES, TkinterDnD

from tkinter import BooleanVar, IntVar
import json

SETTINGS_PATH = "settings.json"
settings = {
    "theme": "darkly",
    "auto_open": True,
    "delete_original": False,
    "output_dir": "",
    "thumb_size": 100
}

settings_window = [None]
selected_files = []
last_output_path = [None]
output_dir = [None]
preview_images = []     # list of output image paths
current_index = [0]     # mutable so it works inside functions

thumbnail_images = []         # Stores Tkinter thumbnails (PhotoImage)
#thumbnail_buttons = []        # Stores Button widgets depreciated 

def load_settings():
    global settings
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as f:
            settings.update(json.load(f))

def save_settings():
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=4)

def refresh_file_table():
    file_table.delete(*file_table.get_children())
    for path in selected_files:
        name = os.path.basename(path)
        folder = os.path.dirname(path)
        file_table.insert('', END, values=(name, folder))
    preview_frame.pack_forget()
    nav_frame.pack_forget()
    show_folder_button.pack_forget()
    clear_thumbnails()
    file_table.pack(pady=10)

def process_images():
    
    #clear/reset
    file_table.pack_forget()     # Hide the table
    preview_frame.pack_forget()  # Also hide preview before processing
    nav_frame.pack_forget()
    preview_images.clear()
    current_index[0] = 0
    
    file_paths = selected_files
    total = len(file_paths)
    if total == 0:
        error_text.config(state='normal')
        error_text.delete('1.0', END)
        error_text.insert(END, "❌ No images selected.")
        error_text.config(state='disabled')
        return

    output_dir[0] = os.path.dirname(file_paths[0])
    for index, file_path in enumerate(file_paths):
        if not os.path.isfile(file_path):
            continue

        try:
            with open(file_path, 'rb') as input_file:
                input_data = input_file.read()
                output_data = remove(input_data)

            output_path = os.path.splitext(file_path)[0] + "_nobg.png"
            with open(output_path, 'wb') as out_file:
                out_file.write(output_data)
            
            if settings.get("delete_original", False):
                try:
                    if os.path.exists(output_path):
                        os.remove(file_path)
                        print(f"✅ Deleted original: {file_path}")
                except Exception as e:
                    print(f"⚠️ Failed to delete original file {file_path}: {e}")
            
            preview_images.append(output_path)
        except Exception as e:
            Messagebox.showerror("Error", f"Error processing {file_path}:\n{str(e)}")

        # Update progress
        progress_var.set(int(((index + 1) / total) * 100))
        app.update_idletasks()

    show_preview()
    if settings.get("auto_open") and output_dir[0]:
        open_folder()
    show_folder_button.pack(pady=5)

def on_drop(event):
    progress_var.set("0")
    paths = event.data.strip().split()
    clean_paths = [p.strip("{}") for p in paths]
    selected_files.clear()
    selected_files.extend(clean_paths)
    error_text.config(state='normal')
    error_text.delete('1.0', END)
    error_text.config(state='disabled')
    refresh_file_table() 

def browse_files():
    progress_var.set("0") 
    files = filedialog.askopenfilenames(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
    if files:
        selected_files.clear()
        selected_files.extend(files)
        error_text.config(state='normal')
        error_text.delete('1.0', END)
        error_text.config(state='disabled')
    refresh_file_table() 

def show_preview(index=0):
    if not preview_images:
        return

    current_index[0] = index
    path = preview_images[index]
    if not os.path.exists(path):
        return

    try:
        img = Image.open(path)
        img.thumbnail((200, 200))
        img_tk = ImageTk.PhotoImage(img)

        preview_label.config(image=img_tk)
        preview_label.image = img_tk
        preview_path_label.config(text=os.path.basename(path))
        preview_count_label.config(text=f"{index + 1} / {len(preview_images)}")

        preview_frame.pack(pady=10)
        nav_frame.pack(pady=5)
        show_folder_button.pack(pady=10)
        build_thumbnail_gallery()
        
        #dynamic resize
        thumbnails_per_row = max(1, app.winfo_width() // (settings["thumb_size"] + 20))
        rows_needed = (len(preview_images) + thumbnails_per_row - 1) // thumbnails_per_row
        new_height = 500 + rows_needed * (settings["thumb_size"] + 20)
        app.geometry(f"{app.winfo_width()}x{new_height}")
        
        thumbnail_gallery.pack(pady=5)
    except Exception as e:
        print(f"Preview error: {e}")

def open_folder():
    try:
        if output_dir[0]:
            if platform.system() == "Windows":
                os.startfile(output_dir[0])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", output_dir[0]])
            else:
                subprocess.Popen(["xdg-open", output_dir[0]])
    except Exception as e:
        print(f"Failed to open folder: {e}")

#preview navigation functions        
def show_previous():
    if current_index[0] > 0:
        current_index[0] -= 1
        show_preview(current_index[0])

def show_next():
    if current_index[0] < len(preview_images) - 1:
        current_index[0] += 1
        show_preview(current_index[0])

def build_thumbnail_gallery():
    
    clear_thumbnails()
    for idx, path in enumerate(preview_images):
        try:
            img = Image.open(path)
            img.thumbnail((settings["thumb_size"], settings["thumb_size"]))
            img_tk = ImageTk.PhotoImage(img)
            thumbnail_images.append(img_tk)

            lbl = ttk.Label(thumbnail_gallery, image=img_tk)
            lbl.image = img_tk  # keep a reference to prevent garbage collection
            lbl.bind("<Button-1>", lambda e, i=idx: show_preview(i))
            lbl.pack(side='left', padx=5)
        except Exception as e:
            print(f"Failed to load thumbnail for {path}: {e}")

def clear_thumbnails():
    for widget in thumbnail_gallery.winfo_children():
        widget.destroy()
        thumbnail_images.clear()
    #thumbnail_buttons.clear()

def load_settings():
    global settings
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r") as f:
                user_settings = json.load(f)
                settings.update(user_settings)  # merge into defaults
        except Exception as e:
            print("⚠️ Failed to load settings.json. Using defaults:", e)
    else:
        save_settings()  # Save default settings on first launch

def open_settings():
     # If already open, bring to front
    if settings_window[0] and settings_window[0].winfo_exists():
        settings_window[0].lift()
        settings_window[0].focus_force()
        return

    # Create new settings window
    win = ttk.Toplevel(app)
    win.title("Settings")
    win.geometry("350x350")
    win.resizable(False, False)

    settings_window[0] = win  # track this window

    def on_close():
        settings_window[0] = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)

    ttk.Label(win, text="Theme:").pack(pady=(10, 0))
    ttk.Button(win, text="Light", command=lambda: change_theme("flatly")).pack()
    ttk.Button(win, text="Dark", command=lambda: change_theme("darkly")).pack()

    auto_var = BooleanVar(value=settings["auto_open"])
    ttk.Checkbutton(win, text="Auto-open output folder", variable=auto_var).pack(pady=5)

    delete_var = BooleanVar(value=settings["delete_original"])
    ttk.Checkbutton(win, text="Delete original images after processing", variable=delete_var).pack(pady=5)

    ttk.Label(win, text="Thumbnail size:").pack(pady=(10, 0))
    thumb_var = IntVar(value=settings["thumb_size"])
    ttk.Combobox(win, textvariable=thumb_var, values=[100, 150, 200], state="readonly").pack()

    def choose_output_folder():
        path = filedialog.askdirectory()
        if path:
            settings["output_dir"] = path

    ttk.Button(win, text="Set Output Folder", command=choose_output_folder).pack(pady=10)

    def save_and_close():
        settings["auto_open"] = auto_var.get()
        settings["delete_original"] = delete_var.get()
        settings["thumb_size"] = thumb_var.get()
        save_settings()
        win.destroy()

    ttk.Button(win, text="Save", command=save_and_close).pack(pady=20)

def change_theme(theme):
    settings["theme"] = theme
    app.style.theme_use(theme)

# GUI setup
class ThemedDnDWindow(TkinterDnD.Tk):
    def __init__(self, *args, themename="flatly", **kwargs):
        super().__init__(*args, **kwargs)
        self.style = ttk.Style()
        self.style.theme_use(settings["theme"])

load_settings()

app = ThemedDnDWindow(themename="flatly")
app.title("Multi Image BG Remover")
app.geometry("800x700")

#settings
header_frame = ttk.Frame(app)
header_frame.pack(fill='x', pady=5, padx=10)
#ttk.Label(header_frame, text="BG Remover", font=("Segoe UI", 14, "bold")).pack(side='left')
# Gear icon button on the right
ttk.Button(header_frame, text="⚙️", width=3, command=open_settings, bootstyle="secondary").pack(side='right')

ttk.Label(app, text="Drag and drop images here, or click the box", bootstyle="info", anchor="center", justify="center").pack(pady=5)

drop_area = ttk.Label(
    app,
    text="Drop Image(s) Here Or Click Here To Browse",
    relief="groove",
    width=60,
    padding=10,
    anchor="center",
    justify="center"
)
drop_area.pack(pady=10, anchor="center")

drop_area.drop_target_register(DND_FILES)
drop_area.dnd_bind('<<Drop>>', on_drop)

# ⬇️ This makes it clickable to browse
drop_area.bind("<Button-1>", lambda e: browse_files())

# Top button row with just Browse
# top_button_frame = ttk.Frame(app)
# top_button_frame.pack(pady=5)

# ttk.Button(top_button_frame, text="Browse", command=browse_files, bootstyle="primary").pack(side='left', padx=10)

# Bottom-right Process button with visual separation
bottom_button_frame = ttk.Frame(app)
bottom_button_frame.pack(side='bottom', fill='x', pady=15)

ttk.Button(bottom_button_frame, text="Process Images", command=process_images, bootstyle="success").pack(side='right', padx=20)


progress_var = ttk.StringVar(value="0")
ttk.Progressbar(app, variable=progress_var, length=400, maximum=100, bootstyle="success-striped").pack(pady=10)

# Error message
error_text = Text(app, height=1, fg="red", state='disabled', bg=app.cget("bg"), borderwidth=0)
error_text.pack()

# File table before preview
file_table = ttk.Treeview(app, columns=("Filename", "Folder"), show="headings", height=4)
file_table.heading("Filename", text="Filename")
file_table.heading("Folder", text="Folder")
file_table.column("Filename", width=200)
file_table.column("Folder", width=450)
file_table.pack(pady=10)

# Preview section
preview_frame = ttk.Frame(app)
preview_frame.pack(pady=15)

preview_label = ttk.Label(preview_frame)
preview_label.pack()

preview_path_label = ttk.Label(preview_frame, text="", wraplength=450)
preview_path_label.pack()

preview_count_label = ttk.Label(preview_frame, text="")
preview_count_label.pack()

nav_frame = ttk.Frame(preview_frame)
nav_frame.pack_forget()

thumbnail_gallery = ttk.Frame(preview_frame)
thumbnail_gallery.pack_forget()

# Show folder button (hidden at start)
show_folder_button = ttk.Button(preview_frame, text="Show Output Folder", command=open_folder, bootstyle="secondary")
show_folder_button.pack_forget()

ttk.Button(nav_frame, text="⟵", command=show_previous).pack(side="left", padx=10)
ttk.Button(nav_frame, text="⟶", command=show_next).pack(side="left", padx=10)

app.mainloop()
