import customtkinter as ctk
from tkinter import filedialog
import subprocess
import re
from tkinterdnd2 import TkinterDnD, DND_FILES

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, power_manager, on_tray_update):
        super().__init__()
        self.pm = power_manager
        self.on_tray_update = on_tray_update

        self.TkdndVersion = TkinterDnD._require(self)

        self.title("Power Plan Manager")
        self.geometry("920x600")
        self.minsize(920, 600)
        self.resizable(True, True)
        self.configure(fg_color="#131314")

        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.create_widgets()
        self.refresh_lists()
        self.setup_drag_drop()

    def create_widgets(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(16, 12))

        self.status_label = ctk.CTkLabel(
            header_frame,
            text="Current Plan: Checking...",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#81C784"
        )
        self.status_label.pack(side="left")

        btn_choose = ctk.CTkButton(
            header_frame,
            text="Choose Plans",
            width=100,
            corner_radius=16,
            fg_color="#282A2C",
            hover_color="#333538",
            text_color="#E3E2E6",
            command=self.open_plan_dialog
        )
        btn_choose.pack(side="right")

        startup_card = ctk.CTkFrame(self, fg_color="#1E1E20", corner_radius=12)
        startup_card.pack(fill="x", padx=16, pady=6)

        lbl_startup = ctk.CTkLabel(startup_card, text="Run at Windows Startup", text_color="#C4C6C0")
        lbl_startup.pack(side="left", padx=14, pady=10)

        self.switch_startup = ctk.CTkSwitch(
            startup_card,
            text="",
            width=46,
            progress_color="#2E7D32",
            command=self.toggle_startup
        )
        self.switch_startup.pack(side="right", padx=14, pady=10)
        if self.pm.is_startup_enabled():
            self.switch_startup.select()

        content_layout = ctk.CTkFrame(self, fg_color="transparent")
        content_layout.pack(fill="both", expand=True, padx=16, pady=(6, 16))

        left_container = ctk.CTkFrame(content_layout, fg_color="transparent")
        left_container.pack(side="left", fill="both", expand=True, padx=(0, 8))

        lbl_info = ctk.CTkLabel(
            left_container,
            text="High Performance Games:",
            font=ctk.CTkFont(size=11),
            text_color="#C4C6C0"
        )
        lbl_info.pack(anchor="w", pady=(0, 4))

        list_frame_games = ctk.CTkFrame(left_container, fg_color="#1E1E20", corner_radius=12, border_width=1, border_color="#333538")
        list_frame_games.pack(fill="both", expand=True, pady=(0, 8))

        self.games_scroll = ctk.CTkScrollableFrame(list_frame_games, fg_color="transparent")
        self.games_scroll.pack(fill="both", expand=True, padx=6, pady=6)

        self.selected_game = None
        self.game_buttons = {}

        btn_frame_games = ctk.CTkFrame(left_container, fg_color="transparent")
        btn_frame_games.pack(fill="x")

        btn_browse_game = ctk.CTkButton(
            btn_frame_games, text="Browse", corner_radius=16, fg_color="#282A2C", hover_color="#333538", command=self.browse_game
        )
        btn_browse_game.pack(side="left", expand=True, fill="x", padx=(0, 3))

        btn_remove_game = ctk.CTkButton(
            btn_frame_games, text="Remove", corner_radius=16, fg_color="#282A2C", hover_color="#333538", command=self.remove_selected_game
        )
        btn_remove_game.pack(side="left", expand=True, fill="x", padx=3)

        btn_launch_game = ctk.CTkButton(
            btn_frame_games, text="Launch", corner_radius=16, fg_color="#004A77", hover_color="#005A92", command=self.launch_selected_game
        )
        btn_launch_game.pack(side="left", expand=True, fill="x", padx=(3, 0))

        right_container = ctk.CTkFrame(content_layout, fg_color="transparent")
        right_container.pack(side="right", fill="both", expand=True, padx=(8, 0))

        lbl_info_launchers = ctk.CTkLabel(
            right_container,
            text="Game Launchers (No Power Shift):",
            font=ctk.CTkFont(size=11),
            text_color="#C4C6C0"
        )
        lbl_info_launchers.pack(anchor="w", pady=(0, 4))

        list_frame_launchers = ctk.CTkFrame(right_container, fg_color="#1E1E20", corner_radius=12, border_width=1, border_color="#333538")
        list_frame_launchers.pack(fill="both", expand=True, pady=(0, 8))

        self.launchers_scroll = ctk.CTkScrollableFrame(list_frame_launchers, fg_color="transparent")
        self.launchers_scroll.pack(fill="both", expand=True, padx=6, pady=6)

        self.selected_launcher = None
        self.launcher_buttons = {}

        btn_frame_launchers = ctk.CTkFrame(right_container, fg_color="transparent")
        btn_frame_launchers.pack(fill="x")

        btn_browse_launcher = ctk.CTkButton(
            btn_frame_launchers, text="Browse", corner_radius=16, fg_color="#282A2C", hover_color="#333538", command=self.browse_launcher
        )
        btn_browse_launcher.pack(side="left", expand=True, fill="x", padx=(0, 3))

        btn_remove_launcher = ctk.CTkButton(
            btn_frame_launchers, text="Remove", corner_radius=16, fg_color="#282A2C", hover_color="#333538", command=self.remove_selected_launcher
        )
        btn_remove_launcher.pack(side="left", expand=True, fill="x", padx=3)

        btn_launch_launcher = ctk.CTkButton(
            btn_frame_launchers, text="Launch", corner_radius=16, fg_color="#004A77", hover_color="#005A92", command=self.launch_selected_launcher
        )
        btn_launch_launcher.pack(side="left", expand=True, fill="x", padx=(3, 0))

    def setup_drag_drop(self):
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        raw_data = event.data
        files = self.tk.splitlist(raw_data)
        for file_path in files:
            if file_path.lower().endswith(".exe"):
                if "launcher" in file_path.lower():
                    added = self.pm.add_launcher(file_path)
                else:
                    added = self.pm.add_game(file_path)
                if added:
                    self.refresh_lists()
                    self.on_tray_update()

    def refresh_lists(self):
        for btn in self.game_buttons.values():
            btn.destroy()
        self.game_buttons.clear()

        for name in self.pm.games.keys():
            btn = ctk.CTkButton(
                self.games_scroll,
                text=name,
                anchor="w",
                fg_color="transparent",
                hover_color="#282A2C",
                text_color="#E3E2E6",
                corner_radius=8,
                command=lambda n=name: self.select_game(n)
            )
            btn.pack(fill="x", pady=2)
            self.game_buttons[name] = btn

        for btn in self.launcher_buttons.values():
            btn.destroy()
        self.launcher_buttons.clear()

        for name in self.pm.launchers.keys():
            btn = ctk.CTkButton(
                self.launchers_scroll,
                text=name,
                anchor="w",
                fg_color="transparent",
                hover_color="#282A2C",
                text_color="#E3E2E6",
                corner_radius=8,
                command=lambda n=name: self.select_launcher(n)
            )
            btn.pack(fill="x", pady=2)
            self.launcher_buttons[name] = btn

    def select_game(self, name):
        self.selected_game = name
        for btn_name, btn in self.game_buttons.items():
            if btn_name == name:
                btn.configure(fg_color="#004A77", text_color="#C2E7FF")
            else:
                btn.configure(fg_color="transparent", text_color="#E3E2E6")

    def select_launcher(self, name):
        self.selected_launcher = name
        for btn_name, btn in self.launcher_buttons.items():
            if btn_name == name:
                btn.configure(fg_color="#004A77", text_color="#C2E7FF")
            else:
                btn.configure(fg_color="transparent", text_color="#E3E2E6")

    def toggle_startup(self):
        self.pm.set_startup(self.switch_startup.get() == 1)

    def browse_game(self):
        path = filedialog.askopenfilename(filetypes=[("Executable Files", "*.exe")])
        if path:
            added = self.pm.add_game(path)
            if added:
                self.refresh_lists()
                self.on_tray_update()

    def browse_launcher(self):
        path = filedialog.askopenfilename(filetypes=[("Executable Files", "*.exe")])
        if path:
            added = self.pm.add_launcher(path)
            if added:
                self.refresh_lists()
                self.on_tray_update()

    def remove_selected_game(self):
        if self.selected_game:
            self.pm.remove_game(self.selected_game)
            self.selected_game = None
            self.refresh_lists()
            self.on_tray_update()

    def remove_selected_launcher(self):
        if self.selected_launcher:
            self.pm.remove_launcher(self.selected_launcher)
            self.selected_launcher = None
            self.refresh_lists()

    def launch_selected_game(self):
        if self.selected_game:
            self.pm.launch_game(self.selected_game)

    def launch_selected_launcher(self):
        if self.selected_launcher:
            self.pm.launch_launcher(self.selected_launcher)

    def update_status_label(self, is_high_perf):
        if is_high_perf:
            self.status_label.configure(text="Current Plan: High Performance", text_color="#E57373")
        else:
            self.status_label.configure(text="Current Plan: Balanced", text_color="#81C784")

    def hide_to_tray(self):
        self.withdraw()

    def show_from_tray(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def open_plan_dialog(self):
        output = subprocess.check_output("powercfg /l", shell=True).decode()
        plans = []
        for line in output.splitlines():
            match = re.search(r"([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})", line)
            if match:
                guid = match.group(1)
                name = line.split("(")[1].split(")")[0].strip() if "(" in line else guid
                plans.append((name, guid))

        dialog = ctk.CTkToplevel(self)
        dialog.title("Select Power Plans")
        dialog.geometry("360x220")
        dialog.configure(fg_color="#131314")
        dialog.grab_set()

        plan_names = [f"{p[0]} ({p[1]})" for p in plans]
        plan_map = {f"{p[0]} ({p[1]})": p[1] for p in plans}
        
        default_b = plan_names[0]
        default_h = plan_names[0]
        for name, guid in plan_map.items():
            if guid == self.pm.balanced_guid:
                default_b = name
            if guid == self.pm.high_perf_guid:
                default_h = name

        var_b = ctk.StringVar(value=default_b)
        var_h = ctk.StringVar(value=default_h)

        lbl_b = ctk.CTkLabel(dialog, text="Balanced Plan:", text_color="#E3E2E6")
        lbl_b.pack(anchor="w", padx=16, pady=(16, 4))
        combo_b = ctk.CTkComboBox(dialog, values=plan_names, variable=var_b, width=320)
        combo_b.pack(padx=16)

        lbl_h = ctk.CTkLabel(dialog, text="High Performance Plan:", text_color="#E3E2E6")
        lbl_h.pack(anchor="w", padx=16, pady=(12, 4))
        combo_h = ctk.CTkComboBox(dialog, values=plan_names, variable=var_h, width=320)
        combo_h.pack(padx=16)

        def save():
            selected_b = combo_b.get()
            selected_h = combo_h.get()
            if selected_b in plan_map and selected_h in plan_map:
                guid_b = plan_map[selected_b]
                guid_h = plan_map[selected_h]
                self.pm.save_config(guid_b, guid_h)
                dialog.destroy()

        btn_save = ctk.CTkButton(dialog, text="Save", corner_radius=16, command=save)
        btn_save.pack(padx=16, pady=16, anchor="e")