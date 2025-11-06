# 📝 HƯỚNG DẪN THỰC HÀNH - TỰ LÀM THEO

## 🎯 BẠN SẼ TỰ THỰC HIỆN CÁC BƯỚC SAU:

---

## ✅ BƯỚC 1: ĐÃ HOÀN THÀNH
- ✅ Đã tạo thay đổi trong code
- ✅ Đã kiểm tra git status
- ✅ Đã xem git diff

---

## 🎓 BƯỚC 2: BẠN TỰ LÀM - Thêm file vào staging

### Mở Terminal/PowerShell và chạy:

```bash
git add analyze_any_province_kpi.py
```

**Hoặc thêm tất cả file:**
```bash
git add .
```

### Sau đó kiểm tra lại:
```bash
git status
```

### Kết quả mong đợi:
Bạn sẽ thấy:
```
Changes to be committed:
  modified:   analyze_any_province_kpi.py
```

**👉 Hãy tự chạy lệnh này và xem kết quả!**

---

## 🎓 BƯỚC 3: BẠN TỰ LÀM - Commit (lưu lại)

### Chạy lệnh commit:
```bash
git commit -m "Thêm comment thực hành Git"
```

**Lưu ý**: Bạn có thể thay đổi message thành bất kỳ mô tả nào bạn muốn!

### Kết quả mong đợi:
Bạn sẽ thấy:
```
[master xxxxxxx] Thêm comment thực hành Git
 1 file changed, 2 insertions(+)
```

**👉 Hãy tự chạy lệnh này và xem kết quả!**

---

## 🎓 BƯỚC 4: BẠN TỰ LÀM - Xác nhận commit thành công

### Kiểm tra status:
```bash
git status
```

### Kết quả mong đợi:
```
On branch master
nothing to commit, working tree clean
```

### Xem lịch sử commit:
```bash
git log --oneline -3
```

### Kết quả mong đợi:
Bạn sẽ thấy commit mới nhất của bạn ở đầu danh sách!

**👉 Hãy tự chạy các lệnh này và xem kết quả!**

---

## 💡 LƯU Ý

1. **Nếu gặp lỗi**: Đọc thông báo lỗi và thử lại
2. **Nếu không chắc**: Chạy `git status` để xem trạng thái hiện tại
3. **Nếu muốn hủy**: Dùng `git reset` để hủy staging

---

## 🎉 SAU KHI HOÀN THÀNH

Bạn đã học được cách:
- ✅ Kiểm tra thay đổi (git status)
- ✅ Xem chi tiết thay đổi (git diff)
- ✅ Thêm file vào staging (git add)
- ✅ Commit thay đổi (git commit)
- ✅ Xem lịch sử commit (git log)

**→ Đây là quy trình bạn sẽ làm mỗi lần sửa code!**

---

## 🔄 THỰC HÀNH THÊM

Sau khi học xong, hãy:
1. Xóa dòng comment "[TẠO THAY ĐỔI ĐỂ THỰC HÀNH GIT]"
2. Làm lại tất cả các bước từ đầu
3. Commit với message: "Xóa dòng comment thực hành"

**→ Đây là cách bạn sẽ làm việc với Git hàng ngày!**

