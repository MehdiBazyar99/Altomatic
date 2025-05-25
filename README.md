# 🧠 Altomatic (PyQt6 Edition)

Altomatic is a powerful desktop application that uses **AI vision capabilities** to analyze images and automatically generate:

- 📂 **Descriptive, readable filenames** (slug-style, AI-generated)
- 📝 **Alt text** suitable for accessibility and screen readers

It is built with **Python** and leverages OpenAI's vision-capable models (e.g., **GPT-4o-mini**) via their API. The app features a modern UI built with PyQt6, offering robust functionality and customization options.

---

## ⚠️ API Key Required

> You **must provide your own OpenAI API key** with access to vision-capable models (e.g., GPT-4o-mini, GPT-4 Turbo with Vision).  
> Without this, Altomatic cannot analyze images or generate filenames/alt text.

🔑 Get your API key from:  
👉 [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)

You can set it once inside the app via the **Settings** tab. The key is stored locally using simple obfuscation.

---

## ✨ Key Features

| Feature | Description |
|--------|-------------|
| 🧠 **AI-Powered Vision** | Uses OpenAI's vision models to analyze image content. |
| 🏷 **Filename Generator** | Creates meaningful, lowercase, dash-separated filenames. |
| ♿ **Alt Text Generator** | Produces detailed and accessible alt descriptions. |
| ✏️ **Editable Results** | Review and modify AI-generated filenames and alt text before saving. |
| 🖼️ **Image Preview** | Displays a preview for single selected image files. |
| 🛑 **Cancel Operation** | Ability to cancel ongoing AI processing. |
| 🌍 **Multilingual Support** | Choose output language for filename and alt text (English, Persian). |
| 🔠 **Detail Control** | Choose level of naming detail (Minimal, Normal, Detailed). |
| 👁️ **Vision Detail** | Select image vision detail for API calls ("low", "high", "auto"). |
| 📄 **OCR Support (Optional)** | Use Tesseract to extract text from images and enrich prompts. |
| 🔢 **Token Usage Stats** | Tracks and displays tokens used per session. |
| 🖥 **Drag & Drop UI** | Supports dragging and dropping folders or individual files onto the input path field. |
| 📁 **Smart Output Foldering** | Outputs are saved in timestamped session folders (default: relative to input, or Pictures/Desktop/Custom). |
| 🧾 **Real-Time Logs** | View detailed colored logs and API activity in the dockable Logs panel. |
| 🔧 **Persistent Settings** | All preferences saved locally between runs. |
| ✨ **Modern UI** | Built with PyQt6 for a responsive and platform-integrated experience. |

---

## 📦 Installation

### 1. Install Python (3.11+ Recommended)
Make sure Python is installed on your system. You can download it from [python.org](https://www.python.org/).

### 2. Create a Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Required Packages
With your virtual environment activated, install the dependencies:
```bash
pip install -r requirements.txt
```
This will install `PyQt6`, `openai`, `Pillow`, `pytesseract`, and `pyperclip`.

### 4. (Optional) Install Tesseract OCR
If you want OCR support (recommended for images with text), install Tesseract OCR:
-   **Windows**: Download from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki). Add Tesseract to your PATH or note the installation path for the settings.
-   **macOS**: `brew install tesseract tesseract-lang` (includes English language pack).
-   **Linux**: `sudo apt-get install tesseract-ocr tesseract-ocr-eng` (or use your distribution's package manager).

After installation, you may need to set the Tesseract path in Altomatic's **Settings** tab if it's not found automatically. You can also specify OCR languages there.

---

## 🚀 Usage

To run the app:

```bash
python main.py
```

Or use a pre-built executable if available from a "Releases" section (if you create one).

---

## 🛠 Building an Executable (Optional)

To generate a standalone executable (e.g., `.exe` on Windows, `.app` on macOS):

```bash
pyinstaller --onefile --windowed --icon=altomatic_icon.ico main.py --name Altomatic
```

**Notes for building:**
-   Ensure `altomatic_icon.ico` (or `.icns` for macOS) is present.
-   PyQt6 applications might require additional hooks or data files for PyInstaller. Test thoroughly. You might need to add `--collect-data qt6_applications` or similar flags if certain Qt plugins are missing.
-   The executable will appear in the `dist/` directory.

---

## 🗂 Project Structure

```
📦 Altomatic/
├── main.py                 # Main application entry point (PyQt6)
├── pyqt_ui.py              # PyQt6 UI layout, main window logic, and worker thread
├── helpers.py              # Utility functions (image conversion, file naming, OCR)
├── ai_handler.py           # Handles communication with OpenAI API
├── config.py               # Manages loading and saving of application settings
├── altomatic_icon.ico      # Application icon
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🔐 Security Note

Your OpenAI API key is stored locally in an obfuscated format and is only transmitted directly to OpenAI API servers during requests. You can reset or remove your key from the settings at any time.

---

## 👨‍💻 Author

**Mehdi Bazyar**  
GitHub: [https://github.com/MehdiBazyar99](https://github.com/MehdiBazyar99)
```
