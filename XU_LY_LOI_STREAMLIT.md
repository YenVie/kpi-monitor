# ⚠️ XỬ LÝ LỖI "ModuleNotFoundError: No module named 'streamlit'"

## 🔍 NGUYÊN NHÂN

Lỗi này xảy ra khi:
1. **Cursor dùng Python interpreter khác** với terminal
2. **Streamlit chưa cài trong Python environment** mà Cursor đang dùng
3. **Cần chọn đúng Python interpreter** trong Cursor

---

## ✅ GIẢI PHÁP

### Cách 1: Chạy từ Terminal (KHUYẾN NGHỊ - Dễ nhất)

**Đừng chạy trực tiếp trong Cursor!** Hãy chạy từ Terminal:

```bash
streamlit run app.py
```

**Hoặc:**

```bash
python -m streamlit run app.py
```

**Kết quả:**
- Streamlit sẽ tự động mở trình duyệt
- Hoặc truy cập: `http://localhost:8501`

---

### Cách 2: Chọn đúng Python Interpreter trong Cursor

1. **Mở Command Palette**: `Ctrl + Shift + P`
2. **Gõ**: `Python: Select Interpreter`
3. **Chọn**: Python interpreter có Streamlit (thường là `Python 3.10.11`)
4. **Kiểm tra**: Chọn interpreter có path: `c:\users\phatk\appdata\local\programs\python\python310\`

---

### Cách 3: Cài Streamlit vào Python environment đúng

1. **Mở Terminal trong Cursor**: `Ctrl + ~`
2. **Kiểm tra Python đang dùng**:
   ```bash
   python --version
   which python  # hoặc where python (Windows)
   ```
3. **Cài Streamlit**:
   ```bash
   pip install streamlit
   ```
4. **Chạy lại app**

---

## 🚀 CÁCH CHẠY ĐÚNG (3 BƯỚC)

### Bước 1: Mở Terminal
- Trong Cursor: `Ctrl + ~`
- Hoặc mở PowerShell/CMD riêng

### Bước 2: Chạy Streamlit
```bash
cd "D:\Mobifone (PVT)\Giám sát KPI thủ công\Thứ tự thu thập dữ liệu"
streamlit run app.py
```

### Bước 3: Mở trình duyệt
- Tự động mở hoặc vào: `http://localhost:8501`

---

## 📝 KIỂM TRA STREAMLIT ĐÃ CÀI CHƯA

### Trong Terminal:
```bash
# Kiểm tra version
streamlit --version

# Hoặc
python -m streamlit --version

# Kiểm tra có thể import không
python -c "import streamlit; print('OK')"
```

### Nếu chưa cài:
```bash
pip install streamlit
```

---

## 🔧 XỬ LÝ LỖI KHÁC

### Lỗi: "command not found: streamlit"
```bash
# Dùng python -m thay vì streamlit trực tiếp
python -m streamlit run app.py
```

### Lỗi: "Port 8501 already in use"
```bash
# Chạy trên port khác
streamlit run app.py --server.port 8502
```

### Lỗi: "File not found: app.py"
```bash
# Đảm bảo đang ở đúng thư mục
cd "D:\Mobifone (PVT)\Giám sát KPI thủ công\Thứ tự thu thập dữ liệu"
ls app.py  # Kiểm tra file có tồn tại
```

---

## 💡 LƯU Ý QUAN TRỌNG

### ❌ Không nên:
- Chạy `python app.py` trực tiếp (không phải cách chạy Streamlit)
- Chạy qua nút Run trong Cursor (có thể dùng sai interpreter)

### ✅ Nên làm:
- **Luôn chạy từ Terminal**: `streamlit run app.py`
- **Kiểm tra Python interpreter** trong Cursor
- **Dùng terminal tích hợp** của Cursor

---

## 🎯 TÓM TẮT

1. **Streamlit đã cài** (kiểm tra: `pip list | grep streamlit`)
2. **Chạy từ Terminal**: `streamlit run app.py`
3. **Không chạy trực tiếp**: `python app.py` sẽ không hoạt động
4. **Mở trình duyệt**: `http://localhost:8501`

---

## 🚀 CHẠY NGAY

```bash
# 1. Mở Terminal
Ctrl + ~

# 2. Chạy Streamlit
streamlit run app.py

# 3. Mở trình duyệt
# Tự động mở hoặc vào: http://localhost:8501
```

**Nếu vẫn lỗi, hãy cho tôi biết thông báo lỗi cụ thể!** 🔧

