# HƯỚNG DẪN SỬ DỤNG PHÂN TÍCH TỔNG QUÁT

## 📋 Tổng quan

Script `analyze_any_province_kpi.py` cho phép phân tích **bất kỳ tỉnh nào** và **bất kỳ KPI nào**, không chỉ riêng Ninh Thuận hay HOSR_4G_2024.

## 🚀 Cách sử dụng

### Cách 1: Chạy từ Command Line

```bash
# Phân tích một tỉnh + một KPI
python analyze_any_province_kpi.py "Ninh thuan" "HOSR_4G_2024"

# Với số ngày so sánh tùy chỉnh
python analyze_any_province_kpi.py "Tp Ho Chi Minh" "MTCL_2024" 14
```

### Cách 2: Chạy Menu Tương tác

```bash
python analyze_any_province_kpi.py
```

Menu sẽ hiển thị:
```
1. Phân tích một tỉnh + một KPI
2. Phân tích một KPI cho tất cả tỉnh
3. Phân tích tất cả KPI quan trọng (pipeline đầy đủ)
0. Thoát
```

### Cách 3: Import trong Python

```python
from analyze_any_province_kpi import analyze_province_kpi, analyze_all_provinces_for_kpi

# Phân tích một tỉnh
detector, alerts, province = analyze_province_kpi(
    province_name="Ninh thuan",
    kpi_name="HOSR_4G_2024",
    lookback_days=7
)

# Phân tích tất cả tỉnh cho một KPI
alerts = analyze_all_provinces_for_kpi(
    kpi_name="MTCL_2024",
    lookback_days=7
)
```

## 📊 Ví dụ sử dụng

### Ví dụ 1: Phân tích Ninh Thuận với HOSR_4G_2024

```bash
python analyze_any_province_kpi.py "Ninh thuan" "HOSR_4G_2024"
```

### Ví dụ 2: Phân tích Tp Ho Chi Minh với MTCL_2024

```bash
python analyze_any_province_kpi.py "Tp Ho Chi Minh" "MTCL_2024"
```

### Ví dụ 3: Phân tích tất cả tỉnh có suy giảm CSSR

```python
from analyze_any_province_kpi import analyze_all_provinces_for_kpi

alerts = analyze_all_provinces_for_kpi("CSSR", lookback_days=7)
```

### Ví dụ 4: Phân tích nhiều tỉnh cùng lúc

```python
from analyze_any_province_kpi import analyze_province_kpi

provinces = ["Ninh thuan", "Tp Ho Chi Minh", "Ba ria Vung tau"]
kpi = "HOSR_4G_2024"

for province in provinces:
    analyze_province_kpi(province, kpi)
```

## 📋 Danh sách KPI có sẵn

Các KPI quan trọng trong file:
- `MTCL_2024`: Mục tiêu chất lượng năm 2024
- `CSSR`: Call Setup Success Rate
- `CDR`: Call Drop Rate
- `ERAB_SR_2022`: ERAB Success Rate
- `ERAB_DR_2022`: ERAB Drop Rate
- `HOSR_4G_2024`: Handover Success Rate 4G
- `VN_CSSR`: CSSR Việt Nam
- `VN_CALL_DR`: Call Drop Rate Việt Nam
- `ID4G_USR_DL_THP`: Throughput 4G
- Và nhiều KPI khác...

## 📋 Danh sách tỉnh

Các tỉnh trong file bao gồm:
- Tp Ho Chi Minh
- Ba ria Vung tau
- Binh duong
- Ninh thuan
- Tay Ninh
- An Giang
- Can Tho
- Và nhiều tỉnh khác...

## ⚙️ Tham số

### `analyze_province_kpi()`
- `province_name`: Tên tỉnh (không phân biệt hoa thường, có thể viết tắt)
- `kpi_name`: Tên KPI chính xác
- `file_path`: Đường dẫn file CSV (mặc định: '1.Ngày.csv')
- `lookback_days`: Số ngày để so sánh (mặc định: 7)
- `decline_threshold`: Ngưỡng suy giảm % (mặc định: 2.0)

## 📈 Output

Mỗi lần chạy sẽ:
1. ✅ Hiển thị thông tin tỉnh và KPI
2. ✅ Phát hiện suy giảm (nếu có)
3. ✅ Tạo trend chart và lưu vào `charts/`
4. ✅ Hiển thị thống kê (min, max, mean, latest, first)

## 🔄 So sánh với script test

| Tính năng | `test_hosr_ninh_thuan.py` | `analyze_any_province_kpi.py` |
|-----------|---------------------------|-------------------------------|
| Tỉnh | Chỉ Ninh Thuận | Bất kỳ tỉnh nào |
| KPI | Chỉ HOSR_4G_2024 | Bất kỳ KPI nào |
| Tự động tìm tỉnh | ❌ | ✅ (case-insensitive) |
| Menu tương tác | ❌ | ✅ |
| Batch analysis | ❌ | ✅ |

## 💡 Tips

1. **Tên tỉnh**: Có thể viết tắt hoặc không đúng chính tả, script sẽ tự động tìm
   - Ví dụ: "Ninh Thuận", "ninh thuan", "Ninh" đều được

2. **Tên KPI**: Phải chính xác, viết đúng như trong file CSV

3. **Xem danh sách**: Nếu nhập sai, script sẽ hiển thị danh sách tỉnh/KPI có sẵn

4. **So sánh nhiều ngày**: Tăng `lookback_days` để so sánh với period dài hơn

## 🎯 Workflow khuyến nghị

1. **Chạy pipeline đầy đủ** để xem tổng quan:
   ```bash
   python kpi_decline_detection_pipeline.py
   ```

2. **Phân tích chi tiết** tỉnh có vấn đề:
   ```bash
   python analyze_any_province_kpi.py "Tỉnh có vấn đề" "KPI suy giảm"
   ```

3. **Tạo báo cáo** từ kết quả trong `reports/` và `charts/`

