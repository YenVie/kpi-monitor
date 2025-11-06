# HƯỚNG DẪN SỬ DỤNG PIPELINE PHÁT HIỆN SUY GIẢM KPI

## 📋 Tổng quan

Pipeline này tự động hóa quy trình:
1. **Phân tích trend** KPI theo tỉnh (giống pivot chart line)
2. **Phát hiện suy giảm** mạnh (> threshold)
3. **Tự động tải dữ liệu huyện** khi phát hiện vấn đề nghiêm trọng
4. **Tạo báo cáo và alert**

## 🚀 Cài đặt

### Yêu cầu
```bash
pip install pandas numpy matplotlib seaborn
```

### Cấu trúc thư mục
```
project/
├── kpi_decline_detection_pipeline.py  # Pipeline chính
├── visualization_module.py            # Module tạo charts
├── alert_system.py                    # Hệ thống cảnh báo
├── 1.Ngày.csv                         # File dữ liệu
├── reports/                           # Thư mục báo cáo
├── charts/                            # Thư mục charts
└── alerts/                            # Thư mục alerts
```

## 📖 Sử dụng cơ bản

### 1. Chạy pipeline đầy đủ

```python
from kpi_decline_detection_pipeline import main

# Chạy pipeline
detector, alerts = main()
```

### 2. Sử dụng từng module riêng lẻ

#### A. Phát hiện suy giảm cho 1 KPI

```python
from kpi_decline_detection_pipeline import KPIDeclineDetector

# Khởi tạo
detector = KPIDeclineDetector('1.Ngày.csv')
detector.load_and_clean_data()

# Phát hiện suy giảm cho MTCL_2024
alerts = detector.detect_declines('MTCL_2024', lookback_days=7)

# Xem kết quả
for alert in alerts:
    print(f"{alert['province']}: suy giảm {alert['decline_pct']}%")
```

#### B. Tạo trend chart

```python
# Tạo chart cho tất cả tỉnh
detector.create_trend_charts('MTCL_2024')

# Hoặc cho một số tỉnh cụ thể
detector.create_trend_charts(
    'MTCL_2024', 
    provinces=['Tp Ho Chi Minh', 'Ba ria Vung tau']
)
```

#### C. Sử dụng visualization module

```python
from visualization_module import KPIVisualization
import pandas as pd

# Load data
df = pd.read_csv('1.Ngày.csv')
df['Ngay7'] = pd.to_datetime(df['Ngay7'], format='%d/%m/%Y')

# Tạo chart
viz = KPIVisualization()
fig, ax = viz.create_pivot_line_chart(
    df=df,
    kpi_column='MTCL_2024',
    group_by='CTKD7',
    provinces=['Tp Ho Chi Minh', 'Ba ria Vung tau']
)

# Lưu chart
viz.save_chart(fig, 'mtcl_trend.png')
```

#### D. Gửi alert

```python
from alert_system import AlertSystem

# Khởi tạo alert system
alert_system = AlertSystem()

# Gửi alert đơn lẻ
alert_system.send_decline_alert(
    province='Tp Ho Chi Minh',
    kpi='MTCL_2024',
    decline_pct=-5.2,
    latest_value=92.5,
    compare_value=97.7
)

# Hoặc gửi batch alerts
alerts = [
    {'province': 'Tp Ho Chi Minh', 'kpi': 'MTCL_2024', 
     'decline_pct': -5.2, 'latest_value': 92.5, 'compare_value': 97.7},
    {'province': 'Ba ria Vung tau', 'kpi': 'CSSR',
     'decline_pct': -3.1, 'latest_value': 96.8, 'compare_value': 99.9}
]
alert_system.send_batch_alerts(alerts)
```

## ⚙️ Cấu hình

### Thay đổi threshold và parameters

```python
from kpi_decline_detection_pipeline import KPIDeclineDetector

# Custom config
CONFIG = {
    'decline_threshold': 3.0,  # % suy giảm để trigger (mặc định: 2.0)
    'days_lookback': 14,        # Số ngày so sánh (mặc định: 7)
    'critical_kpis': ['MTCL_2024', 'CSSR', 'CDR'],  # KPI quan trọng
    'output_dir': 'reports',
    'charts_dir': 'charts'
}

detector = KPIDeclineDetector('1.Ngày.csv', config=CONFIG)
```

### Cấu hình Alert System

```python
from alert_system import AlertSystem

ALERT_CONFIG = {
    'email_enabled': True,
    'email_recipients': ['manager@company.com'],
    'slack_enabled': True,
    'slack_webhook': 'https://hooks.slack.com/...',
    'save_to_file': True,
    'alert_file': 'alerts/alerts.json'
}

alert_system = AlertSystem(config=ALERT_CONFIG)
```

## 🔄 Tự động hóa (Scheduling)

### Option 1: Windows Task Scheduler

1. Tạo file `run_pipeline.bat`:
```batch
@echo off
cd "D:\Mobifone (PVT)\Giám sát KPI thủ công\Thứ tự thu thập dữ liệu"
python kpi_decline_detection_pipeline.py
```

2. Tạo task trong Windows Task Scheduler:
   - Trigger: Daily at 8:00 AM
   - Action: Run `run_pipeline.bat`

### Option 2: Python Schedule

```python
import schedule
import time
from kpi_decline_detection_pipeline import main

def run_pipeline():
    print("Running scheduled pipeline...")
    main()

# Chạy hàng ngày lúc 8:00
schedule.every().day.at("08:00").do(run_pipeline)

# Chạy hàng giờ
# schedule.every().hour.do(run_pipeline)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Option 3: Apache Airflow (Production)

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def run_kpi_pipeline():
    from kpi_decline_detection_pipeline import main
    main()

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'kpi_decline_detection',
    default_args=default_args,
    description='Detect KPI declines daily',
    schedule_interval='0 8 * * *',  # 8 AM daily
)

run_pipeline = PythonOperator(
    task_id='detect_kpi_declines',
    python_callable=run_kpi_pipeline,
    dag=dag,
)
```

## 📊 Tích hợp với dữ liệu huyện

### Implement DistrictDataFetcher

Bạn cần implement logic tải dữ liệu huyện trong `DistrictDataFetcher.fetch_district_data()`:

```python
class DistrictDataFetcher:
    def fetch_district_data(self, province: str, date: datetime):
        # Option 1: Đọc từ file CSV
        district_file = f"data/district_{province}_{date.strftime('%Y%m%d')}.csv"
        if os.path.exists(district_file):
            return pd.read_csv(district_file)
        
        # Option 2: Gọi API
        # response = requests.get(f"https://api.example.com/district/{province}")
        # return pd.DataFrame(response.json())
        
        # Option 3: Query từ database
        # query = f"SELECT * FROM district_data WHERE province='{province}' AND date='{date}'"
        # return pd.read_sql(query, connection)
        
        return pd.DataFrame()
```

## 📈 Output Files

### Báo cáo CSV
- **Location**: `reports/decline_report_YYYYMMDD.csv`
- **Columns**: KPI, Tỉnh, Ngày, Giá trị hiện tại, Giá trị trước, Suy giảm (%), Mức độ

### Charts
- **Location**: `charts/YYYYMMDD/trend_{KPI}_{YYYYMMDD}.png`
- **Format**: PNG, 300 DPI

## 🛠️ Chạy bằng CLI (không cần menu)

Ví dụ phân tích một tỉnh + một KPI:

```
python analyze_any_province_kpi.py --province "Binh Dinh" --kpi CSSR --lookback 14 --exclude-dates 16/10/2025 --charts-dir charts
```

Phân tích một KPI cho toàn bộ tỉnh:

```
python analyze_any_province_kpi.py --kpi HOSR --lookback 7 --date-range 01/10/2025-31/10/2025
```

Tham số:

- `--province`: tên tỉnh (tuỳ chọn)
- `--kpi`: tên KPI (khớp gần đúng, không phân biệt hoa thường)
- `--lookback`: số ngày so sánh (mặc định 7)
- `--start-date`, `--end-date`: khoảng ngày cụ thể (ưu tiên hơn lookback)
- `--exclude-dates`: danh sách ngày loại bỏ, phân cách bằng dấu phẩy
- `--date-range`: khoảng ngày hiển thị dạng `start-end`
- `--charts-dir`: thư mục lưu chart
- `--debug`: bật log chi tiết

## ⚙️ Cấu hình ngoài (`config.yaml`)

Tạo file `config.yaml` để cấu hình nhanh:

```yaml
decline_threshold: 2.0
days_lookback: 7
critical_kpis:
  - MTCL_2024
  - CSSR
  - CDR
  - ERAB_SR_2022
  - HOSR_4G_2024
charts_dir: charts
output_dir: reports
logs_dir: logs
```

CLI/ENV có thể override các giá trị trong file cấu hình.

### Alerts
- **Location**: `alerts/alerts.json`
- **Format**: JSON với timestamp và severity

## 🎯 Workflow hoàn chỉnh

```
1. Load CSV → Clean data
   ↓
2. Calculate trends cho tất cả KPI
   ↓
3. Detect declines (so sánh với 7 ngày trước)
   ↓
4. Generate report
   ↓
5. Create trend charts cho KPI có vấn đề
   ↓
6. Send alerts cho suy giảm nghiêm trọng
   ↓
7. Identify provinces cần district data
   ↓
8. Fetch district data (nếu có)
   ↓
9. Analyze district-level declines
```

## 🔍 Troubleshooting

### Lỗi: "File not found"
- Kiểm tra đường dẫn file CSV
- Đảm bảo file có tên đúng: `1.Ngày.csv`

### Lỗi: "Column not found"
- Kiểm tra tên cột trong file CSV
- Có thể cần điều chỉnh `critical_kpis` trong config

### Charts không hiển thị tiếng Việt
- Cài font tiếng Việt cho matplotlib:
```python
plt.rcParams['font.family'] = 'Arial Unicode MS'  # hoặc font khác hỗ trợ tiếng Việt
```

## 📞 Hỗ trợ

Nếu cần hỗ trợ, kiểm tra:
1. Logs trong console output
2. File `alerts/alerts.json` để xem alerts
3. File reports để xem chi tiết suy giảm

