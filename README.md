# PowerTray

PowerTray is a lightweight Windows utility that automatically switches your power plan to **High Performance** when designated games are running, and reverts back to **Balanced** mode when you close them. It sits quietly in your system tray and includes a dedicated dashboard for managing games, utility launchers, and custom power plan preferences.

## Features

* **Automatic Power Switching**: Detects active games and applies your chosen high performance power plan.
* **System Tray Integration**: Runs minimized in the system tray with live status indicators and quick access controls.
* **Game Launchers Section**: Separate management for non-tracked game launchers (like Epic Games, HoyoPlay, or Steam) that do not trigger power plan changes.
* **Steam Library Shortcut**: Direct access to open your Steam library right from the tray menu.
* **Drag-and-Drop Support**: Easily add games or launchers by dragging `.exe` files directly into the window.
* **Windows Startup Option**: Toggle the app to start automatically with Windows.

## Installation & Setup

1. Download the latest release folder from the releases page and extract it.
2. Run `PowerTray.exe`.
3. Open the app interface to choose your preferred balanced and high-performance power plans.
4. Drag and drop your game executables or launchers into their respective sections.

```cmd
python -m PyInstaller --noconfirm --onedir --windowed --name "PowerTray" --additional-hooks-dir=. main.py
<img width="1147" height="787" alt="Powertray1" src="https://github.com/user-attachments/assets/0eebec4c-e70f-4142-a1c4-db9688adb624" />
<img width="450" height="311" alt="Powertray2" src="https://github.com/user-attachments/assets/5f8ee053-50a2-4588-8bb5-f42eaf82df22" />
<img width="322" height="517" alt="Powertray3" src="https://github.com/user-attachments/assets/ccaa6d5a-cd39-4221-b033-3c86a26de28f" />
