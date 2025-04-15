# 🧠 Altomatic

Altomatic is a powerful desktop application that uses **AI vision capabilities** to analyze images and automatically generate:

- 📂 **Descriptive, readable filenames** (slug-style, AI-generated)
- 📝 **Alt text** suitable for accessibility and screen readers

It is built with **Python** and leverages the **GPT-4.1-nano** model via OpenAI’s API. The app comes with an elegant, dynamic UI and powerful customization options.

---

## ⚠️ API Key Required

> You **must provide your own OpenAI API key** with access to GPT-4.1-nano and vision capabilities.  
> Without this, Altomatic cannot analyze images or generate filenames/alt text.

🔑 Get your API key from:  
👉 [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)

You can set it once inside the app via the **Settings** tab. The key is securely saved in local config using obfuscation.

---

## ✨ Key Features

| Feature | Description |
|--------|-------------|
| 🧠 **AI-Powered Vision** | Uses GPT-4.1-nano to analyze image content |
| 🏷 **Filename Generator** | Creates meaningful, lowercase, dash-separated filenames |
| ♿ **Alt Text Generator** | Produces detailed and accessible alt descriptions |
| 🌍 **Multilingual Support** | Choose output language for filename and alt text (English, Persian) |
| 🔠 **Detail Control** | Choose level of naming detail (Minimal, Normal, Detailed) |
| 🖼 **OCR Support (Optional)** | Use Tesseract to extract text from images and enrich prompts |
| 🔢 **Token Usage Stats** | Tracks and displays total tokens used per session |
| 🖥 **Drag & Drop UI** | Supports folders or individual files |
| 🎨 **Theming** | Select from multiple beautiful themes (Light, Dark, BlueGray, Solarized, Pinky) |
| 📁 **Smart Output Foldering** | Outputs are saved in timestamped folders (default: Pictures) |
| 🧾 **Real-Time Logs** | View detailed colored logs and API activity in the Monitor panel |
| 🔧 **Persistent Settings** | All preferences saved between runs |

---

## 📦 Installation

### 1. Install Python (3.11+ Recommended)

### 2. Install Required Packages

```bash
pip install -r requirements.txt
```

### 3. (Optional) Install Tesseract OCR

If you want OCR support (recommended), install Tesseract:

👉 [Tesseract for Windows (UB Mannheim)](https://github.com/UB-Mannheim/tesseract/wiki)

Then set the `.exe` path inside the **Settings** tab in Altomatic.

---

## 🚀 Usage

To run the app:

```bash
python main.py
```

Or use the pre-built executable from the [Releases](https://github.com/MehdiBazyar99/altomatic/releases) section.

---

## 🛠 Building the EXE

To generate a standalone `.exe` with a custom icon:

```bash
pyinstaller --onefile --windowed --icon=altomatic_icon.ico main.py
```

Your final `.exe` will appear in the `dist/` directory.

---

## 🗂 Project Structure

```
📦 Altomatic
├── main.py
├── ui_components.py
├── logic.py
├── helpers.py
├── ai_handler.py
├── config.py
├── dragdrop.py
├── altomatic_icon.ico
└── README.md
```

---

## 🔐 Security Note

Your OpenAI API key is stored in an encoded format and never transmitted anywhere except to the OpenAI API servers during requests. You can reset your key anytime.

---

## 👨‍💻 Author

**Mehdi Bazyar**  
GitHub: [https://github.com/MehdiBazyar99](https://github.com/MehdiBazyar99)
همچنین اگه خواستی نسخه فارسی به‌روز و هماهنگ با این رو هم بنویسم، کافیه بگی ✅
