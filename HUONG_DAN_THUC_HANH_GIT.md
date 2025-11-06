# 📚 HƯỚNG DẪN THỰC HÀNH GIT - TỪNG BƯỚC CỤ THỂ

## 🎯 Mục tiêu: Bạn sẽ học cách commit thay đổi vào Git

---

## 📋 BƯỚC 1: TẠO THAY ĐỔI TRONG CODE

### Bước 1.1: Mở file `analyze_any_province_kpi.py`
- Tìm đến dòng 7 (có chữ "Version: 1.0")
- Thay đổi thành: `Version: 1.1` (hoặc bất kỳ số nào bạn muốn)

**Hoặc bạn có thể:**
- Thêm một comment mới vào đầu hàm: `# TODO: Cải thiện performance`
- Thêm một dòng trống

**QUAN TRỌNG**: Hãy LƯU FILE lại (Ctrl+S)

---

## 📋 BƯỚC 2: KIỂM TRA GIT ĐÃ PHÁT HIỆN THAY ĐỔI CHƯA

### Bước 2.1: Mở Terminal/PowerShell
- Trong VS Code/Cursor: Nhấn `Ctrl + ~` (hoặc View → Terminal)
- Hoặc mở PowerShell bình thường và cd vào thư mục dự án

### Bước 2.2: Chạy lệnh kiểm tra
```bash
git status
```

### Bước 2.3: Xem kết quả
Bạn sẽ thấy:
```
Changes not staged for commit:
  modified:   analyze_any_province_kpi.py
```

**✅ Nếu thấy như trên → Git đã phát hiện thay đổi!**
**❌ Nếu thấy "working tree clean" → Bạn chưa lưu file hoặc chưa có thay đổi**

---

## 📋 BƯỚC 3: XEM CHI TIẾT THAY ĐỔI (TÙY CHỌN)

### Bước 3.1: Xem file nào đã thay đổi
```bash
git diff analyze_any_province_kpi.py
```

### Bước 3.2: Giải thích kết quả
Bạn sẽ thấy:
- Dòng có dấu `-` (màu đỏ): Dòng CŨ đã bị xóa
- Dòng có dấu `+` (màu xanh): Dòng MỚI đã thêm vào

**Ví dụ:**
```
- Version: 1.0
+ Version: 1.1
```

**→ Đây là cách Git cho bạn biết đã sửa gì!**

---

## 📋 BƯỚC 4: THÊM FILE VÀO STAGING (CHUẨN BỊ COMMIT)

### Bước 4.1: Thêm file vào staging
```bash
git add analyze_any_province_kpi.py
```

**Hoặc thêm tất cả file đã thay đổi:**
```bash
git add .
```

### Bước 4.2: Kiểm tra lại
```bash
git status
```

### Bước 4.3: Xem kết quả
Bạn sẽ thấy:
```
Changes to be committed:
  modified:   analyze_any_province_kpi.py
```

**✅ Nếu thấy "Changes to be committed" → File đã được thêm vào staging thành công!**

---

## 📋 BƯỚC 5: COMMIT (LƯU LẠI THAY ĐỔI)

### Bước 5.1: Commit với message
```bash
git commit -m "Update version to 1.1"
```

**Lưu ý**: 
- Thay message bằng mô tả thay đổi của bạn
- Ví dụ: "Thêm comment về Git", "Fix typo", "Cập nhật version"

### Bước 5.2: Xem kết quả
Bạn sẽ thấy:
```
[master xxxxxxx] Update version to 1.1
 1 file changed, 1 insertion(+), 1 deletion(-)
```

**✅ Nếu thấy như trên → Commit thành công!**

---

## 📋 BƯỚC 6: XÁC NHẬN COMMIT ĐÃ ĐƯỢC LƯU

### Bước 6.1: Kiểm tra status
```bash
git status
```

### Bước 6.2: Xem kết quả
Bạn sẽ thấy:
```
On branch master
nothing to commit, working tree clean
```

**✅ "working tree clean" → Hoàn thành! Code đã được lưu vào Git.**

### Bước 6.3: Xem lịch sử commit
```bash
git log --oneline -3
```

### Bước 6.4: Xem kết quả
Bạn sẽ thấy danh sách các commit gần nhất:
```
xxxxxxx (HEAD -> master) Update version to 1.1
d14febe Thêm file hướng dẫn Git và comment về Git trong code
047de2d Initial commit: Thêm code phân tích KPI và documentation
```

**✅ Commit mới nhất của bạn đã xuất hiện ở đầu danh sách!**

---

## 🎉 HOÀN THÀNH!

Bạn đã thành công commit thay đổi vào Git!

---

## 📝 TÓM TẮT QUY TRÌNH

```
1. Sửa code → Lưu file
2. git status          → Xem thay đổi
3. git add .           → Thêm vào staging
4. git commit -m "..." → Lưu vào Git
5. git log --oneline   → Xem lại lịch sử
```

---

## 🆘 XỬ LÝ LỖI

### Lỗi: "Please tell me who you are"
```bash
git config --global user.name "Tên của bạn"
git config --global user.email "email@của-bạn.com"
```

### Lỗi: "nothing to commit"
- Kiểm tra xem bạn đã lưu file chưa (Ctrl+S)
- Kiểm tra xem bạn đã thay đổi gì chưa

### Muốn hủy commit vừa làm?
```bash
git reset --soft HEAD~1    # Hủy commit nhưng giữ lại thay đổi
```

---

## 💡 BÀI TẬP THỰC HÀNH

### Thử làm lại với thay đổi khác:
1. Thêm một comment mới vào code
2. Chạy lại tất cả các bước từ đầu
3. Commit với message khác

### Mục tiêu: Làm quen với quy trình này!

---

**Chúc bạn thành công! 🎓**

