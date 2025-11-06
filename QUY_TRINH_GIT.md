# 🔄 QUY TRÌNH LÀM VIỆC VỚI GIT (Mỗi lần sửa code)

## ⚠️ QUAN TRỌNG: Git KHÔNG tự động lưu!

**Mỗi lần bạn sửa code, bạn phải tự làm các bước sau:**

---

## 📋 QUY TRÌNH 3 BƯỚC (BẮT BUỘC)

### Bước 1: Sửa code ✏️
```bash
# Bạn tự sửa code trong file
# Ví dụ: thêm hàm mới, sửa bug, cải thiện code...
```

### Bước 2: Thêm vào staging 📦
```bash
git add .
# hoặc
git add tên-file-cụ-thể.py
```

### Bước 3: Commit (lưu lại) 💾
```bash
git commit -m "Mô tả thay đổi của bạn"
```

---

## 🎯 VÍ DỤ THỰC TẾ

### Tình huống: Bạn vừa sửa bug trong `analyze_any_province_kpi.py`

```bash
# 1. Xem file nào đã thay đổi
git status

# 2. Xem chi tiết thay đổi (tùy chọn)
git diff analyze_any_province_kpi.py

# 3. Thêm file vào staging
git add analyze_any_province_kpi.py
# hoặc thêm tất cả: git add .

# 4. Commit với message rõ ràng
git commit -m "Fix bug: Sửa lỗi fuzzy matching khi tìm KPI"

# 5. Kiểm tra lại
git log --oneline -1
```

---

## ⚙️ CÓ THỂ TỰ ĐỘNG HÓA KHÔNG?

### ❌ KHÔNG NÊN:
- **Tự động commit mỗi khi sửa code** → Rất nguy hiểm!
  - Có thể commit code lỗi
  - Commit quá nhiều, khó quản lý
  - Không có cơ hội review trước khi commit

### ✅ CÓ THỂ TỰ ĐỘNG HÓA MỘT PHẦN:
Bạn có thể tạo script để hỗ trợ, nhưng vẫn phải tự quyết định commit:

**Script helper (git_commit_helper.bat trên Windows):**
```batch
@echo off
echo ========================================
echo    GIT COMMIT HELPER
echo ========================================
echo.
git status
echo.
echo Bạn muốn commit thay đổi không? (Y/N)
set /p confirm=
if /i "%confirm%"=="Y" (
    echo Nhập message commit:
    set /p message=
    git add .
    git commit -m "%message%"
    git log --oneline -1
    echo.
    echo ✅ Đã commit thành công!
) else (
    echo ❌ Hủy commit
)
```

---

## 🔍 KIỂM TRA NHANH

### Sau khi sửa code, chạy:
```bash
git status
```

### Kết quả có thể là:

**1. "Working tree clean"** → Không có thay đổi
```
On branch master
nothing to commit, working tree clean
```

**2. "Changes not staged"** → Có thay đổi nhưng chưa add
```
Changes not staged for commit:
  modified:   analyze_any_province_kpi.py

no changes added to commit
```
→ **PHẢI LÀM**: `git add .` rồi `git commit`

**3. "Changes to be committed"** → Đã add nhưng chưa commit
```
Changes to be committed:
  modified:   analyze_any_province_kpi.py
```
→ **PHẢI LÀM**: `git commit -m "..."`

---

## 💡 KHUYẾN NGHỊ

### ✅ Làm thường xuyên:
1. Sau mỗi tính năng nhỏ hoàn thành → Commit ngay
2. Sau khi fix bug → Commit ngay
3. Cuối ngày làm việc → Commit tất cả thay đổi

### ✅ Commit message tốt:
- ✅ "Thêm tính năng phân tích theo ngày cụ thể"
- ✅ "Fix lỗi crash khi file CSV rỗng"
- ✅ "Cải thiện performance khi load file lớn"
- ❌ "Update" (quá mơ hồ)
- ❌ "abc" (không có ý nghĩa)

---

## 🎓 TÓM TẮT

| Hành động | Tự động? | Bạn phải làm gì? |
|-----------|----------|------------------|
| Sửa code | ✅ Tự động | Chỉ cần sửa trong editor |
| Git phát hiện thay đổi | ✅ Tự động | Chỉ cần chạy `git status` |
| **Thêm vào staging** | ❌ **KHÔNG** | **Phải chạy `git add`** |
| **Commit** | ❌ **KHÔNG** | **Phải chạy `git commit`** |

**→ Git là công cụ giúp bạn, nhưng bạn phải tự quyết định khi nào lưu!**

---

## 🆘 NHỚ KHI NÀO?

**Mỗi lần bạn:**
- ✅ Sửa code xong → `git add .` + `git commit`
- ✅ Thêm file mới → `git add .` + `git commit`
- ✅ Xóa file → `git add .` + `git commit`
- ✅ Test code chạy OK → Commit ngay!

**NHƯNG NHỚ:**
- ⚠️ Chỉ commit khi code đã **test OK**
- ⚠️ Chỉ commit khi bạn **chắc chắn** muốn lưu
- ⚠️ Không commit code lỗi hoặc code thử nghiệm

