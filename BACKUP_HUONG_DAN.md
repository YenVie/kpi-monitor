# HƯỚNG DẪN BACKUP VÀ ROLLBACK CODE

## 📦 Cách 1: Backup Thủ Công (Đơn giản nhất)

### Tạo backup:
```powershell
# Tạo thư mục backup
mkdir backup

# Copy các file Python quan trọng
Copy-Item *.py backup\

# Hoặc copy toàn bộ (bao gồm cả CSV, MD)
Copy-Item *.* backup\
```

### Khôi phục khi cần:
```powershell
# Copy lại từ backup
Copy-Item backup\*.py .
```

## 🔄 Cách 2: Dùng Git (Khuyến nghị cho dự án dài hạn)

### Thiết lập Git (chỉ cần làm 1 lần):
```bash
# Config user (thay thông tin của bạn)
git config --global user.email "your.email@example.com"
git config --global user.name "Your Name"

# Hoặc chỉ cho thư mục này
git config user.email "your.email@example.com"
git config user.name "Your Name"
```

### Tạo backup điểm:
```bash
# Khởi tạo Git (chỉ cần làm 1 lần)
git init

# Thêm các file quan trọng
git add *.py *.md

# Tạo commit (backup điểm)
git commit -m "Backup: Trạng thái hiện tại - [Mô tả ngắn]"
```

### Xem lịch sử backup:
```bash
git log --oneline
```

### Khôi phục về trạng thái trước:
```bash
# Xem các commit
git log

# Khôi phục về commit cụ thể (thay COMMIT_HASH)
git checkout COMMIT_HASH

# Hoặc khôi phục về commit gần nhất
git checkout HEAD~1

# Quay lại trạng thái hiện tại
git checkout main
# hoặc
git checkout master
```

### Tạo nhánh mới để thử nghiệm:
```bash
# Tạo nhánh mới từ trạng thái hiện tại
git checkout -b experiment-feature-x

# Làm việc trên nhánh này...
# Nếu không ổn, quay lại nhánh chính
git checkout main
git branch -D experiment-feature-x  # Xóa nhánh thử nghiệm
```

## 📝 Cách 3: Đổi tên file trước khi sửa

### Trước khi sửa file quan trọng:
```powershell
# Đổi tên file gốc
Rename-Item visualization_module.py visualization_module.py.backup

# Copy và chỉnh sửa
Copy-Item visualization_module.py.backup visualization_module.py
```

### Khôi phục:
```powershell
# Xóa file đã sửa
Remove-Item visualization_module.py

# Đổi tên lại
Rename-Item visualization_module.py.backup visualization_module.py
```

## ⚠️ Lưu Ý Quan Trọng

1. **Luôn backup trước khi thử nghiệm tính năng mới**
2. **Đặt tên backup rõ ràng**: `backup_20250101_ten_tinh_nang`
3. **Kiểm tra backup hoạt động** trước khi xóa file gốc
4. **Git là cách tốt nhất** cho dự án dài hạn, nhưng cần học một chút

## 🎯 Khuyến Nghị

- **Ngắn hạn/Thử nghiệm**: Dùng cách 1 (copy thủ công)
- **Dài hạn/Chuyên nghiệp**: Dùng cách 2 (Git)
- **Sửa file đơn lẻ**: Dùng cách 3 (đổi tên)

---

**Trạng thái hiện tại**: Đã có backup trong thư mục `backup/` (nếu đã chạy lệnh backup)



