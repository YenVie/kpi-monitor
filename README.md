# 🚀 PIPELINE TỰ ĐỘNG HÓA PHÁT HIỆN SUY GIẢM KPI

## 📋 Mô tả

Pipeline này tự động hóa quy trình giám sát KPI thủ công của bạn:

1. **Tạo pivot chart line** để xem trend KPI theo tỉnh
2. **Phát hiện suy giảm mạnh** (> threshold) cho từng KPI và tỉnh
3. **Tự động tải dữ liệu cấp huyện** khi phát hiện vấn đề nghiêm trọng
4. **Tạo báo cáo và alert** tự động

## 🎯 Workflow

```
┌─────────────────┐
│  Load CSV Data  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Calculate      │
│  Trends         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Detect         │
│  Declines       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Generate       │─────▶│  Create      │
│  Report         │      │  Charts      │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│  Send Alerts    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Fetch District │
│  Data (if needed)│
└─────────────────┘
```

## 📁 Cấu trúc project

```
project/
├── kpi_decline_detection_pipeline.py  # Pipeline chính
├── visualization_module.py            # Module tạo charts
├── alert_system.py                    # Hệ thống cảnh báo
├── run_pipeline_example.py            # Ví dụ sử dụng
├── 1.Ngày.csv                         # File dữ liệu đầu vào
├── PHÂN_TÍCH_TỰ_ĐỘNG_HÓA.md           # Tài liệu phân tích
├── HUONG_DAN_SU_DUNG.md               # Hướng dẫn chi tiết
├── example_pipeline.py                # Ví dụ pipeline cơ bản
├── reports/                           # Thư mục báo cáo (tự động tạo)
├── charts/                            # Thư mục charts (tự động tạo)
└── alerts/                            # Thư mục alerts (tự động tạo)
```

## 🚀 Quick Start

### 1. Cài đặt dependencies

```bash
pip install pandas numpy matplotlib seaborn
```

### 2. Chạy pipeline đầy đủ

```python
from kpi_decline_detection_pipeline import main

# Chạy pipeline
detector, alerts = main()
```

### 3. Hoặc chạy từ command line

```bash
python kpi_decline_detection_pipeline.py
```

## 📊 Tính năng chính

### ✅ Phát hiện suy giảm KPI
- So sánh giá trị hiện tại với period trước (mặc định: 7 ngày)
- Phát hiện suy giảm > threshold (mặc định: 2%)
- Phân loại mức độ: Nhẹ, Cảnh báo, Nghiêm trọng, Cực kỳ nghiêm trọng

### ✅ Tạo trend charts
- Line chart giống pivot chart trong Excel
- Hiển thị trend theo tỉnh theo thời gian
- Tự động highlight các tỉnh có vấn đề

### ✅ Tự động tải dữ liệu huyện
- Khi phát hiện suy giảm nghiêm trọng → tự động trigger fetch district data
- Phân tích suy giảm theo huyện để xác định huyện cụ thể

### ✅ Alert system
- Gửi alerts khi phát hiện suy giảm
- Lưu alerts vào file JSON
- Hỗ trợ email/Slack (cần config)

### ✅ Báo cáo tự động
- CSV report với tất cả suy giảm
- Charts PNG với độ phân giải cao
- Alert logs

## ⚙️ Cấu hình

### Thay đổi threshold và parameters

```python
CONFIG = {
    'decline_threshold': 2.0,  # % suy giảm để trigger
    'days_lookback': 7,        # Số ngày so sánh
    'critical_kpis': [         # KPI quan trọng cần theo dõi
        'MTCL_2024', 
        'CSSR', 
        'CDR', 
        'ERAB_SR_2022'
    ],
    'output_dir': 'reports',
    'charts_dir': 'charts'
}

detector = KPIDeclineDetector('1.Ngày.csv', config=CONFIG)
```

## 📖 Ví dụ sử dụng

### Ví dụ 1: Phát hiện suy giảm cho 1 KPI

```python
from kpi_decline_detection_pipeline import KPIDeclineDetector

detector = KPIDeclineDetector('1.Ngày.csv')
detector.load_and_clean_data()

# Phát hiện suy giảm MTCL_2024
alerts = detector.detect_declines('MTCL_2024', lookback_days=7)

for alert in alerts:
    print(f"{alert['province']}: {alert['decline_pct']:.2f}%")
```

### Ví dụ 2: Tạo trend chart

```python
# Chart cho tất cả tỉnh
detector.create_trend_charts('MTCL_2024')

# Hoặc cho một số tỉnh
detector.create_trend_charts(
    'MTCL_2024',
    provinces=['Tp Ho Chi Minh', 'Ba ria Vung tau']
)
```

### Ví dụ 3: Phân tích đầy đủ

```python
# Phân tích tất cả KPI quan trọng
all_alerts = detector.analyze_all_kpis()

# Tạo báo cáo
report_df = detector.generate_decline_report()
print(report_df)
```

Xem thêm ví dụ trong `run_pipeline_example.py`

## 📚 Tài liệu

- **HUONG_DAN_SU_DUNG.md**: Hướng dẫn chi tiết cách sử dụng
- **PHÂN_TÍCH_TỰ_ĐỘNG_HÓA.md**: Phân tích khả năng tự động hóa

## 🔄 Tự động hóa (Scheduling)

### Windows Task Scheduler

1. Tạo file `run_pipeline.bat`:
```batch
@echo off
cd "D:\Mobifone (PVT)\Giám sát KPI thủ công\Thứ tự thu thập dữ liệu"
python kpi_decline_detection_pipeline.py
```

2. Tạo task trong Task Scheduler:
   - Trigger: Daily at 8:00 AM
   - Action: Run `run_pipeline.bat`

### Python Schedule

```python
import schedule
import time
from kpi_decline_detection_pipeline import main

schedule.every().day.at("08:00").do(main)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## 📥 Output Files

### Reports
- **Location**: `reports/decline_report_YYYYMMDD.csv`
- **Format**: CSV với encoding UTF-8-sig

### Charts
- **Location**: `charts/trend_{KPI}_{YYYYMMDD}.png`
- **Format**: PNG, 300 DPI

### Alerts
- **Location**: `alerts/alerts.json`
- **Format**: JSON

## 🎯 KPI được theo dõi

- **MTCL_2024**: Mục tiêu chất lượng năm 2024
- **CSSR**: Call Setup Success Rate
- **CDR**: Call Drop Rate
- **ERAB_SR_2022**: ERAB Success Rate
- Và các KPI khác trong file CSV

## ⚠️ Lưu ý

1. **District Data Fetcher**: Cần implement logic tải dữ liệu huyện thực tế trong `DistrictDataFetcher.fetch_district_data()`

2. **Alert System**: Cần config email/Slack webhook để gửi alerts thực tế

3. **Font tiếng Việt**: Nếu charts không hiển thị tiếng Việt, cài font hỗ trợ tiếng Việt

4. **File encoding**: Đảm bảo file CSV là UTF-8

## 🐛 Troubleshooting

### Lỗi: "File not found"
- Kiểm tra đường dẫn file CSV
- Đảm bảo file có tên đúng: `1.Ngày.csv`

### Lỗi: "Column not found"
- Kiểm tra tên cột trong file CSV
- Có thể cần điều chỉnh `critical_kpis` trong config

### Charts không hiển thị
- Kiểm tra matplotlib đã cài đặt
- Thử chạy với `plt.show()` để xem

## 📞 Hỗ trợ

Nếu có vấn đề:
1. Kiểm tra logs trong console
2. Xem file `alerts/alerts.json`
3. Kiểm tra file reports để xem chi tiết

---

**Tác giả**: Auto-generated pipeline  
**Ngày tạo**: 2025  
**Version**: 1.0

