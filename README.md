### 📄 `README.md`

````markdown
# 📸 Advanced Screenshot Plugin for Enigma2

![Platform](https://img.shields.io/badge/platform-Enigma2-blue.svg)
![Status](https://img.shields.io/badge/status-Active-brightgreen.svg)
![Python](https://img.shields.io/badge/python-2.7-yellow.svg)
![License](https://img.shields.io/github/license/your-name/advanced-screenshot.svg)
![GUI](https://img.shields.io/badge/interface-GUI%20Based-orange)

---

## 🧩 Description

**Advanced Screenshot** is a powerful plugin for Enigma2-based devices that lets you:

- Take instant screenshots directly from your receiver
- Browse captured images with a built-in thumbnail gallery
- View full-screen previews
- Use slideshow mode for automated image browsing
- Navigate using remote control shortcuts

---

## 🖼️ Screenshots

| Thumbnail Gallery | Fullscreen View |
|------------------|-----------------|
| ![Gallery](gallery.png) | ![List](list.png) |

<img src="https://github.com/Belfagor2005/AdvancedScreenshot/blob/main/usr/lib/enigma2/python/Plugins/Extensions/AdvancedScreenshot/plugin.png?raw=true">

<img src="https://github.com/Belfagor2005/AdvancedScreenshot/blob/main/screen/galery.png?raw=true">

<img src="https://github.com/Belfagor2005/AdvancedScreenshot/blob/main/screen/list.png?raw=true">

---

## ⚙️ Features

- 📸 Quick screenshot capture
- 📁 File browser with image listing
- 🖥️ Fullscreen image preview
- 🔁 Slideshow mode with timer
- 🎨 Responsive skin, adjusts to screen size
- 🕹️ Remote control navigation

---

## 📦 Requirements

- Enigma2-based receiver (OE-A / OpenATV / OpenPLI compatible)
- Python > 3.x
- PNG/JPG image rendering support
- Compatible skin with GUI widgets

---

## 🚀 Installation

1. Copy the plugin directory:

```bash
/Plugins/Extensions/AdvancedScreenshot/
````

to your receiver path:

```bash
/usr/lib/enigma2/python/Plugins/Extensions/
```

2. Restart the GUI:

```bash
Menu > Standby / Restart > Restart GUI
```

3. Access the plugin from:

```bash
Menu > Plugins > Advanced Screenshot
```

---

## 🎮 Remote Control Shortcuts

| Button    | Action                 |
| --------- | ---------------------- |
| 🔴 Red    | Previous image         |
| 🔵 Blue   | Next image             |
| 🟡 Yellow | Play / Pause slideshow |
| 🟢 Green  | Play / Pause slideshow |
| ◀️ Left   | Previous image         |
| ▶️ Right  | Next image             |
| ❌ Exit    | Close viewer           |

---

## 📁 Directory Structure

```
AdvancedScreenshot/
├── plugin.py
├── picplayer.py
├── MyConsole.py
├── plugin.png
├── locale/
├── images/
│   ├── pic_frame.png
│   └── pic_framehd.png
└── README.md
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 💡 Credits

Developed and maintained by Lululla(https://github.com/Belfagor2005)
Contributions, bug reports, and suggestions are welcome!

```

---

```
