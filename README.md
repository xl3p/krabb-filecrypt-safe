# 🔐 FileCrypt Safe

**A secure file encryption utility that preserves original files.**

A desktop application with a graphical interface built on Flet.
Encrypts and decrypts files using a master password and unique per-file salt.
Encrypted copies are stored in an isolated folder — **originals are never
modified or deleted**, eliminating the risk of data loss.

## 📋 Features
| Feature | Description |
|:---|:---|
| 🔒 **Encryption** | Select one or multiple files, encrypt with unique per-file salt |
| 🔓 **Decryption** | Browse `encrypted/` folder, select files, restore to original locations |
| 🧂 **Unique salt** | Each file gets its own randomly generated salt, increasing security |
| 🛡️ **Safe-by-design** | Read-only approach — originals are read, encrypted copies are written separately |
| 🔑 **Master password** | Hashed with Argon2, making brute-force attacks impractical |

---

## 🧠 How It Works
```
┌──────────┐ ┌──────────────────┐ ┌──────────────┐
│ User │ ──▶ │ Enter master │ ──▶ │ Pick files │
│ │ │ password │ │ │
└──────────┘ └──────────────────┘ └──────┬────────┘
│
┌────────────────────────────▼────────────────────────────┐
│ For each file: │
│ 1. Generate random salt (Scrypt, N=2¹⁴) │
│ 2. Derive encryption key from salt + password │
│ 3. Encrypt file using Fernet (AES-128-CBC + HMAC) │
│ 4. Save result to encrypted/ folder │
│ 5. ORIGINAL FILE IS LEFT UNTOUCHED │
└─────────────────────────────────────────────────────────┘
```
## 🚀 Quick Start

### Option 1: Run from source

```bash
git clone https://github.com/YOUR_USERNAME/filecrypt-safe.git
cd filecrypt-safe
pip install -r requirements.txt
python main.py
```

### Option 2: Download release (no Python required)

1. Go to Releases

2. Download filecrypt-safe-windows.zip or filecrypt-safe-linux.zip

3. Extract and run the executable inside

4. On Linux you may need to mark the binary as executable:


``` bash
chmod +x filecrypt-safe
./filecrypt-safe
```

## 🔧 Dependencies

- Python 3.10+

- Flet — Flutter-like GUI framework

- Cryptography (Fernet) — AES-128-CBC symmetric encryption with HMAC authentication

- Scrypt (KDF) — Key derivation from password + salt (N=2¹⁴, r=8, p=1)

- Argon2 (argon2-cffi) — Master password hashing

## ⚠️ Important Notes

- Do not delete encrypted/ and salts/ folders — decryption is impossible without them.

- Do not forget your master password — it cannot be recovered. Data will be lost.

- This is a portfolio project built to demonstrate cryptographic primitives and GUI development skills.

## 📄 License

MIT License — do whatever you want, author bears no responsibility.

### Feedback
Made with 🦀 by [xl3pp](xl3p)

My [telegram](https://t.me/xlpp3)



