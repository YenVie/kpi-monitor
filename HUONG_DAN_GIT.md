# 📚 HƯỚNG DẪN SỬ DỤNG GIT - DỰ ÁN KPI MONITORING

## 🎯 Git là gì?
Git là hệ thống quản lý phiên bản code. Giống như "Checkpoint" trong game - bạn có thể lưu lại trạng thái code và quay lại sau này.

---

## 📋 QUY TRÌNH LÀM VIỆC VỚI GIT (Workflow)

### Quy trình cơ bản:
```
1. Làm việc với code (sửa file)
   ↓
2. git status          (xem file nào đã thay đổi)
   ↓
3. git add .           (thêm file vào staging)
   ↓
4. git commit -m "..." (lưu lại thay đổi)
   ↓
5. Lặp lại từ bước 1
```

---

## 🛠️ CÁC LỆNH GIT CƠ BẢN

### 1. **git status** - Xem trạng thái
```bash
git status
```
**Dùng khi nào**: Sau khi sửa code, muốn xem file nào đã thay đổi
**Kết quả**: 
- Hiển thị file đã sửa (modified)
- Hiển thị file mới (untracked)
- Hiển thị file đã sẵn sàng commit (staged)

---

### 2. **git add** - Thêm file vào staging
```bash
# Thêm 1 file cụ thể
git add analyze_any_province_kpi.py

# Thêm tất cả file đã thay đổi
git add .

# Thêm tất cả file .py
git add *.py
```
**Dùng khi nào**: Sau khi sửa code, muốn chuẩn bị commit
**Lưu ý**: File CSV, charts, logs KHÔNG được thêm (đã có trong .gitignore)

---

### 3. **git commit** - Lưu lại thay đổi
```bash
# Commit với message ngắn
git commit -m "Sửa lỗi logic phát hiện suy giảm"

# Commit với message dài
git commit -m "Thêm tính năng: Phân tích tự động cho nhiều tỉnh
- Thêm hàm analyze_all_provinces_for_kpi
- Cải thiện fuzzy matching cho KPI
- Fix bug khi so sánh ngày"
```
**Dùng khi nào**: Sau khi `git add`, muốn lưu lại snapshot
**Lưu ý**: Message nên rõ ràng, mô tả chính xác thay đổi

**Ví dụ message tốt**:
- ✅ "Thêm tính năng tương tác cho biểu đồ"
- ✅ "Fix lỗi crash khi file CSV không có dữ liệu"
- ✅ "Cải thiện performance khi load file lớn"
- ❌ "Update"
- ❌ "Sửa lỗi"
- ❌ "abc"

---

### 4. **git log** - Xem lịch sử commit
```bash
# Xem chi tiết
git log

# Xem ngắn gọn (1 dòng)
git log --oneline

# Xem với graph
git log --oneline --graph

# Xem 5 commit gần nhất
git log -5 --oneline
```
**Dùng khi nào**: Muốn xem các commit đã làm trước đó

---

### 5. **git diff** - Xem sự khác biệt
```bash
# Xem sự khác biệt so với commit trước
git diff

# Xem sự khác biệt của 1 file cụ thể
git diff analyze_any_province_kpi.py

# Xem sự khác biệt giữa 2 commit
git diff 047de2d HEAD
```
**Dùng khi nào**: Muốn xem chính xác đã sửa gì trong code

---

### 6. **git checkout** - Khôi phục file về phiên bản cũ
```bash
# Khôi phục 1 file về commit trước
git checkout -- analyze_any_province_kpi.py

# Khôi phục tất cả file về commit trước
git checkout -- .

# Xem file ở commit cũ (không sửa)
git checkout 047de2d -- analyze_any_province_kpi.py
```
**Dùng khi nào**: Sửa nhầm code, muốn quay lại như cũ
**⚠️ CẢNH BÁO**: Lệnh này sẽ XÓA thay đổi chưa commit!

---

### 7. **git reset** - Hủy commit hoặc unstage
```bash
# Hủy add (file vẫn còn, chỉ bỏ khỏi staging)
git reset

# Hủy commit cuối cùng (giữ lại thay đổi)
git reset --soft HEAD~1

# Hủy commit và xóa thay đổi
git reset --hard HEAD~1
```
**Dùng khi nào**: Commit nhầm, muốn hủy
**⚠️ CẢNH BÁO**: `--hard` sẽ XÓA thay đổi!

---

## 🔄 TÌNH HUỐNG THỰC TẾ

### Tình huống 1: Sửa code xong, muốn lưu lại
```bash
# Bước 1: Xem đã sửa gì
git status

# Bước 2: Thêm tất cả file đã sửa
git add .

# Bước 3: Commit với message rõ ràng
git commit -m "Thêm tính năng phân tích theo ngày cụ thể"

# Bước 4: Kiểm tra lại
git status
git log --oneline -1
```

---

### Tình huống 2: Sửa nhầm code, muốn quay lại
```bash
# Xem file nào đã sửa
git status

# Khôi phục file về phiên bản cũ
git checkout -- analyze_any_province_kpi.py

# Hoặc khôi phục tất cả
git checkout -- .
```

---

### Tình huống 3: Muốn xem code cách đây 1 tuần
```bash
# Xem lịch sử commit
git log --oneline

# Xem code ở commit cụ thể
git show 047de2d:analyze_any_province_kpi.py

# Hoặc checkout về commit đó (tạm thời)
git checkout 047de2d
# Sau đó quay lại
git checkout master
```

---

### Tình huống 4: Commit nhầm message, muốn sửa
```bash
# Sửa message của commit cuối cùng
git commit --amend -m "Message mới chính xác hơn"
```

---

## 🌿 BRANCH (Nhánh) - Làm việc song song

### Tạo branch mới để thử nghiệm
```bash
# Tạo branch mới
git checkout -b feature/thu-nghiem-tinh-nang-moi

# Hoặc
git branch feature/thu-nghiem-tinh-nang-moi
git checkout feature/thu-nghiem-tinh-nang-moi

# Xem tất cả branch
git branch

# Quay lại branch chính
git checkout master

# Xóa branch
git branch -d feature/thu-nghiem-tinh-nang-moi
```

**Khi nào dùng branch**:
- Muốn thử nghiệm tính năng mới mà không ảnh hưởng code chính
- Làm việc nhóm, mỗi người làm trên branch riêng

---

## 📤 REMOTE REPOSITORY (GitHub/GitLab)

### Kết nối với GitHub
```bash
# Thêm remote repository
git remote add origin https://github.com/username/repo-name.git

# Push code lên GitHub
git push -u origin master

# Lấy code từ GitHub
git pull origin master
```

**Lưu ý**: Cần có tài khoản GitHub và tạo repository trước

---

## 📝 BEST PRACTICES

### ✅ NÊN LÀM:
1. **Commit thường xuyên**: Mỗi khi làm xong 1 tính năng nhỏ
2. **Message rõ ràng**: Mô tả chính xác thay đổi
3. **Commit nhỏ**: Mỗi commit chỉ làm 1 việc
4. **Review trước khi commit**: Dùng `git diff` để xem lại

### ❌ KHÔNG NÊN:
1. **Commit code lỗi**: Đảm bảo code chạy được trước khi commit
2. **Commit file dữ liệu lớn**: CSV, PDF, charts (đã có .gitignore)
3. **Commit toàn bộ**: Nên commit từng phần có liên quan
4. **Message mơ hồ**: Tránh "Update", "Fix", "Changes"

---

## 🔍 LỆNH HỮU ÍCH KHÁC

```bash
# Xem thay đổi của 1 file qua các commit
git log -p analyze_any_province_kpi.py

# Xem ai đã sửa file nào
git blame analyze_any_province_kpi.py

# Tìm commit theo message
git log --grep="bug"

# Xem thống kê thay đổi
git diff --stat

# So sánh 2 branch
git diff master..feature/new-feature
```

---

## 🆘 XỬ LÝ LỖI THƯỜNG GẶP

### Lỗi: "Please tell me who you are"
```bash
git config --global user.name "Tên của bạn"
git config --global user.email "email@của-bạn.com"
```

### Lỗi: "LF will be replaced by CRLF"
Đây là cảnh báo bình thường trên Windows, không ảnh hưởng code

### Muốn xóa file khỏi Git nhưng giữ lại ở máy
```bash
git rm --cached file.csv
git commit -m "Xóa file CSV khỏi tracking"
```

---

## 📚 TÀI LIỆU THAM KHẢO

- **Git Documentation**: https://git-scm.com/doc
- **Git Cheat Sheet**: https://education.github.com/git-cheat-sheet-education.pdf
- **Learn Git**: https://learngitbranching.js.org/

---

**Tác giả**: Hướng dẫn Git cho dự án KPI Monitoring  
**Ngày tạo**: 2025-11-06  
**Version**: 1.0

