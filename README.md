# Altomatic

Altomatic is a modern desktop application that uses **AI and vision** to generate:
- 📂 Meaningful filenames (slug-style)
- 📝 Descriptive alt texts for images

Built with Python and OpenAI's GPT-4.1-nano, it supports:
- Drag & drop images
- Folder or single-file processing
- Custom output folders
- Multiple languages
- Token usage tracking
- Optional OCR (Tesseract)
- Dynamic UI themes
- Logs and monitoring
- Fully customizable config

---

## ✨ Features

- 💡 GPT-4.1-nano-powered vision analysis
- 🧠 Generates accessible alt texts for screen readers
- 🏷 Creates clear, dash-separated filenames based on content
- 🔠 Multi-language support (English & Persian for now)
- 🧾 Live logs and colored monitor window
- 📊 Token usage stats per session
- 🖼 OCR text extraction from images (optional)
- 🌈 UI theme selection (Light, Dark, BlueGray, Solarized, Pinky)
- 📁 Output is stored in timestamped folders in `Pictures` by default
- 💾 Config settings are saved between sessions
- 🔒 API key is stored securely in local config

---

## 🔧 Installation

### 1. Install Python 3.11+
### 2. Install dependencies:
```bash
pip install -r requirements.txt
3. Install Tesseract (Optional for OCR)
Download from: 👉 https://github.com/UB-Mannheim/tesseract/wiki

Then specify its path in the Settings tab.

🖥 Usage
Run the app:

bash
Copy
Edit
python main.py
Or use the provided executable from the Releases.

🛠 Build EXE
To build your own standalone .exe file with custom icon:

bash
Copy
Edit
pyinstaller --onefile --windowed --icon=altomatic_icon.ico main.py
The final executable will be in dist/.

📁 Project Structure
arduino
Copy
Edit
📦 Altomatic
├── main.py
├── ui_components.py
├── logic.py
├── helpers.py
├── ai_handler.py
├── config.py
├── dragdrop.py
├── altomatic_icon.ico
├── requirements.txt
└── README.md
🔐 Note
This tool uses OpenAI APIs. Please review your usage and API key safety.

👨‍💻 Author
Mehdi
GitHub: MehdiDevX

