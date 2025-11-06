# 🔄 CÁCH QUAY LẠI CODE CŨ TRONG GIT

## 🎯 Các tình huống và cách xử lý

---

## 📋 TÌNH HUỐNG 1: Sửa nhầm code nhưng CHƯA COMMIT

### ✅ Cách 1: Khôi phục 1 file cụ thể
```bash
# Cách cũ (vẫn dùng được)
git checkout -- tên-file.py

# Cách mới (khuyên dùng)
git restore tên-file.py
```

**Ví dụ:**
```bash
git restore analyze_any_province_kpi.py
```

**Kết quả**: File sẽ về đúng như phiên bản đã commit cuối cùng

---

### ✅ Cách 2: Khôi phục TẤT CẢ file
```bash
# ⚠️ CẢNH BÁO: Xóa TẤT CẢ thay đổi chưa commit!
git checkout -- .

# Hoặc
git restore .
```

**Khi nào dùng**: Khi bạn sửa nhiều file và muốn quay lại hết

---

## 📋 TÌNH HUỐNG 2: Đã COMMIT nhưng muốn quay lại commit trước

### ✅ Cách 1: Xem code ở commit cũ (không sửa)
```bash
# Xem nội dung file ở commit cũ
git show commit-id:tên-file.py

# Xem toàn bộ commit
git show commit-id
```

**Ví dụ:**
```bash
git show 047de2d:analyze_any_province_kpi.py
```

---

### ✅ Cách 2: Lấy file từ commit cũ về (tạm thời)
```bash
# Xem file ở commit cũ nhưng không thay đổi file hiện tại
git checkout commit-id -- tên-file.py
```

**Ví dụ:**
```bash
git checkout 047de2d -- analyze_any_province_kpi.py
```

**Lưu ý**: File sẽ được thay đổi và sẵn sàng để commit (đã trong staging)

---

### ✅ Cách 3: Reset về commit trước (giữ lại thay đổi trong file)
```bash
# Xem commit nào
git log --oneline

# Reset về commit trước (giữ lại code trong file)
git reset --soft HEAD~1
```

**Giải thích**:
- `HEAD~1` = commit trước đó 1 bước
- `--soft` = giữ lại code trong file, chỉ hủy commit

**Kết quả**: 
- Commit bị hủy
- Code vẫn còn trong file
- File đã sẵn sàng để commit lại

---

### ✅ Cách 4: Reset về commit trước (XÓA thay đổi)
```bash
# ⚠️ CẢNH BÁO: Xóa code và commit!
git reset --hard HEAD~1

# Hoặc reset về commit cụ thể
git reset --hard 047de2d
```

**Giải thích**:
- `--hard` = Xóa tất cả thay đổi
- Code sẽ về đúng như commit đó

**⚠️ CẢNH BÁO**: Mất tất cả thay đổi sau commit đó!

---

## 📋 TÌNH HUỐNG 3: So sánh code giữa các commit

### ✅ Xem sự khác biệt giữa 2 commit
```bash
# So sánh commit hiện tại với commit trước
git diff HEAD~1 HEAD

# So sánh 2 commit cụ thể
git diff 047de2d d14febe

# So sánh file cụ thể
git diff 047de2d d14febe -- analyze_any_province_kpi.py
```

---

## 📋 TÌNH HUỐNG 4: Xem tất cả các phiên bản của file

### ✅ Xem lịch sử thay đổi của 1 file
```bash
# Xem commit nào đã sửa file
git log --oneline -- analyze_any_province_kpi.py

# Xem chi tiết thay đổi qua các commit
git log -p -- analyze_any_province_kpi.py

# Xem thay đổi ngắn gọn
git log --oneline --graph -- analyze_any_province_kpi.py
```

---

## 📋 TÌNH HUỐNG 5: Tạo branch mới từ commit cũ (an toàn nhất)

### ✅ Tạo branch mới từ commit cũ
```bash
# Tạo branch mới từ commit cũ
git checkout -b branch-moi 047de2d

# Hoặc
git branch branch-moi 047de2d
git checkout branch-moi
```

**Lợi ích**: 
- Giữ nguyên branch cũ
- Có thể làm việc trên code cũ mà không ảnh hưởng code mới

---

## 🎯 BẢNG TÓM TẮT

| Tình huống | Lệnh | Lưu ý |
|------------|------|-------|
| **Sửa nhầm, chưa commit** | `git restore file.py` | An toàn |
| **Sửa nhầm, chưa commit (tất cả)** | `git restore .` | ⚠️ Xóa tất cả |
| **Xem code ở commit cũ** | `git show commit-id:file.py` | Chỉ xem |
| **Lấy file từ commit cũ** | `git checkout commit-id -- file.py` | File sẽ thay đổi |
| **Reset về commit trước (giữ code)** | `git reset --soft HEAD~1` | Giữ code |
| **Reset về commit trước (xóa code)** | `git reset --hard HEAD~1` | ⚠️ Xóa code |
| **Tạo branch từ commit cũ** | `git checkout -b branch 047de2d` | An toàn nhất |

---

## 💡 KHUYẾN NGHỊ

### ✅ Nên làm:
1. **Tạo branch mới** từ commit cũ khi muốn thử nghiệm
2. **Dùng `git restore`** khi sửa nhầm (chưa commit)
3. **Dùng `git reset --soft`** khi muốn sửa lại commit message

### ❌ Không nên:
1. **Dùng `git reset --hard`** trừ khi chắc chắn muốn xóa code
2. **Reset trên branch chính** khi đã push lên GitHub/GitLab

---

## 🆘 XỬ LÝ LỖI

### Lỗi: "Your local changes would be overwritten"
```bash
# Lưu thay đổi vào stash (tạm thời)
git stash

# Sau đó làm việc khác
git checkout commit-id

# Lấy lại thay đổi sau
git stash pop
```

---

## 📚 VÍ DỤ THỰC TẾ

### Ví dụ 1: Sửa nhầm và muốn quay lại
```bash
# 1. Xem đã sửa gì
git diff

# 2. Quay lại
git restore analyze_any_province_kpi.py

# 3. Kiểm tra lại
git status
```

### Ví dụ 2: Commit nhầm và muốn sửa lại
```bash
# 1. Xem commit
git log --oneline -3

# 2. Reset về commit trước (giữ code)
git reset --soft HEAD~1

# 3. Sửa code lại

# 4. Commit lại với message đúng
git commit -m "Message chính xác"
```

### Ví dụ 3: Muốn xem code cách đây 1 tuần
```bash
# 1. Tìm commit ID
git log --oneline --since="1 week ago"

# 2. Xem code ở commit đó
git show commit-id:file.py

# 3. Hoặc checkout về đó (tạm thời)
git checkout commit-id
# ... làm việc ...
# 4. Quay lại
git checkout master
```

---

## 🎓 TÓM TẮT NGẮN GỌN

**Quay lại code cũ khi:**
- ✅ Chưa commit → `git restore file.py`
- ✅ Đã commit → `git reset --soft HEAD~1` (giữ code) hoặc `git reset --hard HEAD~1` (xóa code)
- ✅ Muốn an toàn → Tạo branch mới từ commit cũ

**Luôn nhớ:**
- `git log` để xem lịch sử commit
- `git diff` để xem thay đổi
- `git status` để xem trạng thái hiện tại

---

**Chúc bạn thành công! 🎓**

