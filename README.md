# 🏷️ Meesho Label Export - Thank You Message & QR Code Generator

Automatically adds a **personalized thank-you message** and a **QR code** (linking to your Meesho store) below each shipping label in your Meesho Sub Order Labels PDF.

## ✨ Features

- 📝 **Personalized message** — Extracts the customer name from each label and creates a custom greeting
- 📱 **QR Code** — Links to your Meesho store so customers can follow you
- 🔄 **Batch processing** — Processes all pages in the PDF at once
- 📐 **Smart positioning** — Dynamically detects where the label content ends to avoid overlapping

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/bytebraincode/meesho-label-export.git
cd meesho-label-export

# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 🚀 Usage

```bash
# Auto-detect Sub_Order PDF in current directory
python3 add_message_to_label.py

# Specify input PDF
python3 add_message_to_label.py your_label.pdf

# Specify both input and output
python3 add_message_to_label.py input.pdf output.pdf
```

The output file will be saved as `<original_name>_with_message.pdf`.

## 📋 What Gets Added

Below each shipping label page, the script adds:

> **Dear [Customer Name],**
> Thank you for shopping with us! We are so happy to have you as our customer.
> If you loved your purchase, please follow our store on Meesho! Scan the QR code below to stay updated on our latest collections.
> Keep visiting and supporting!

Along with a **QR code** linking to the Meesho store.

## ⚙️ Configuration

Edit the following variables in `add_message_to_label.py`:

| Variable | Description |
|----------|-------------|
| `MEESHO_STORE_URL` | Your Meesho store URL for the QR code |
| `MESSAGE_TEMPLATE` | The thank-you message template (`$User` is replaced with the customer name) |

## 🛠️ Requirements

- Python 3.9+
- PyPDF2
- ReportLab
- qrcode
- PyMuPDF
- Pillow

## 📄 License

MIT License

---

Made with ❤️ by **JUMJUM ENTERPRISE**
