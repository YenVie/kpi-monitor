"""
PIPELINE TỰ ĐỘNG HÓA PHÁT HIỆN SUY GIẢM KPI
============================================
Workflow:
1. Đọc dữ liệu CSV và tạo pivot chart line (trend analysis)
2. Phát hiện KPI nào của tỉnh nào đang suy giảm mạnh
3. Tự động tải dữ liệu cấp huyện khi phát hiện vấn đề
4. Tạo báo cáo và alert
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Optional imports
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
    print("⚠️  seaborn không được cài đặt. Một số tính năng visualization có thể bị hạn chế.")

# Import các module hỗ trợ
try:
    from visualization_module import KPIVisualization
    from alert_system import AlertSystem
except ImportError:
    print("⚠️  Các module hỗ trợ chưa được import. Chạy file này trong cùng thư mục.")
    KPIVisualization = None
    AlertSystem = None

# Cấu hình
CONFIG = {
    'decline_threshold': 2.0,  # % suy giảm để trigger alert
    'days_lookback': 7,  # Số ngày để so sánh trend
    'critical_kpis': ['MTCL_2024', 'CSSR', 'CDR', 'ERAB_SR_2022', 'HOSR_4G_2024'],  # KPI quan trọng
    'output_dir': 'reports',
    'charts_dir': 'charts',
    # Quy tắc theo KPI: hướng tốt/xấu và ngưỡng mục tiêu
    # ví dụ theo file PDF: CDR <= 0.35% (tức là giá trị nhỏ hơn thì tốt)
    'kpi_rules': {
        'CDR': { 'direction': 'lower_better', 'limit': 0.35 },
        # Ví dụ thêm: 'CSSR': { 'direction': 'higher_better', 'limit': 99.0 }
    }
}


class KPIDeclineDetector:
    """Class chính để phát hiện suy giảm KPI"""
    
    def __init__(self, file_path: str, config: Dict = None):
        self.file_path = file_path
        self.config = config or CONFIG
        self.df = None
        self.province_trends = {}
        self.decline_alerts = []
        
    def _get_kpi_rule(self, kpi_column: str) -> Optional[Dict]:
        """Tìm rule theo tên KPI (match tiền tố, không phân biệt hoa/thường)."""
        rules = self.config.get('kpi_rules') or {}
        kpi_up = str(kpi_column).upper()
        for key, rule in rules.items():
            if key.upper() in kpi_up:
                return rule
        return None

    def _is_worsening(self, latest: float, compare: float, rule: Optional[Dict]) -> Tuple[bool, float]:
        """Xác định có xu hướng xấu đi theo hướng KPI.
        Trả về (is_worse, change_pct_directionsigned)
        """
        if compare is None or compare == 0:
            return False, 0.0
        change_pct = ((latest - compare) / compare) * 100.0
        if rule and rule.get('direction') == 'lower_better':
            # Tăng là xấu
            return change_pct > 0, change_pct
        # Mặc định: higher_better → giảm là xấu
        return change_pct < 0, change_pct

    def _is_limit_breached(self, value: float, rule: Optional[Dict]) -> Optional[bool]:
        """Kiểm tra có vi phạm ngưỡng hay không. None nếu không có rule/limit."""
        if not rule or 'limit' not in rule:
            return None
        limit = rule['limit']
        direction = rule.get('direction', 'higher_better')
        if direction == 'lower_better':
            return value > limit
        return value < limit

    def load_and_clean_data(self):
        """Đọc và làm sạch dữ liệu"""
        print("📖 Đang đọc dữ liệu...")
        
        # Đọc CSV
        self.df = pd.read_csv(self.file_path, encoding='utf-8')
        
        # Parse ngày
        self.df['Ngay7'] = pd.to_datetime(self.df['Ngay7'], format='%d/%m/%Y', errors='coerce')
        
        # Làm sạch các cột số
        numeric_cols = self._get_numeric_columns()
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = self._clean_numeric_column(self.df[col])
        
        # Lọc bỏ dòng không có tỉnh
        self.df = self.df[self.df['CTKD7'].notna()].copy()
        
        print(f"✅ Đã load {len(self.df)} dòng dữ liệu")
        print(f"   - Từ {self.df['Ngay7'].min().date()} đến {self.df['Ngay7'].max().date()}")
        print(f"   - Số tỉnh: {self.df['CTKD7'].nunique()}")
        
        return self.df
    
    def _get_numeric_columns(self) -> List[str]:
        """Lấy danh sách các cột số"""
        return [
            'MTCL_2024', 'MTCL_2024_Giamtru',
            'HTMT_QoS', 'DiemHTMT_KPI', 'DiemHTMT_KPI_Giamtru',
            'CSSR', 'CSSR_Giamtru', 'CDR', 'CDR_GiamTru',
            'ERAB_SR_2022', 'ERAB_SR_2022_GIAMTRU',
            'ERAB_DR_2022', 'ERAB_DR_2022_GIAMTRU',
            'HOSR_4G_2024', 'VN_CSSR', 'VN_CALL_DR',
            'ID4G_USR_DL_THP', 'ChatLuongVungPhu'
        ]
    
    def _clean_numeric_column(self, series: pd.Series) -> pd.Series:
        """Làm sạch cột số: xử lý dấu phẩy, dấu ngoặc kép"""
        series = series.astype(str)
        series = series.str.replace('"', '', regex=False)
        series = series.str.replace(',', '', regex=False)
        return pd.to_numeric(series, errors='coerce')
    
    def calculate_trends(self, kpi_column: str, province: str = None) -> pd.DataFrame:
        """
        Tính toán trend (xu hướng) cho KPI
        
        Args:
            kpi_column: Tên cột KPI cần phân tích
            province: Tên tỉnh (None = tất cả tỉnh)
        
        Returns:
            DataFrame với trend analysis
        """
        # Lọc dữ liệu (bỏ qua giá trị 0 và null)
        df_filtered = self.df.copy()
        if province:
            df_filtered = df_filtered[df_filtered['CTKD7'] == province]
        
        # QUAN TRỌNG: Bỏ qua các ngày có KPI = 0 hoặc null (không tính toán trend)
        df_filtered = df_filtered[
            (df_filtered[kpi_column].notna()) & 
            (df_filtered[kpi_column] != 0)
        ].copy()
        
        # Nhóm theo ngày và tỉnh
        if province:
            daily_avg = df_filtered.groupby('Ngay7')[kpi_column].mean().reset_index()
            daily_avg['CTKD7'] = province
        else:
            daily_avg = df_filtered.groupby(['Ngay7', 'CTKD7'])[kpi_column].mean().reset_index()
        
        # Tính toán các metrics
        daily_avg = daily_avg.sort_values('Ngay7')
        
        # Rate of change (tỷ lệ thay đổi)
        daily_avg['change_pct'] = daily_avg.groupby('CTKD7')[kpi_column].pct_change() * 100
        
        # Moving average (trung bình động)
        daily_avg['ma_7d'] = daily_avg.groupby('CTKD7')[kpi_column].transform(
            lambda x: x.rolling(window=7, min_periods=1).mean()
        )
        
        # Trend direction (xu hướng: tăng/giảm/ổn định)
        daily_avg['trend'] = daily_avg.groupby('CTKD7')['change_pct'].transform(
            lambda x: np.where(x > 0.5, 'Tăng', np.where(x < -0.5, 'Giảm', 'Ổn định'))
        )
        
        return daily_avg
    
    def detect_declines(self, kpi_column: str, lookback_days: int = None) -> List[Dict]:
        """
        Phát hiện các tỉnh có KPI suy giảm mạnh
        
        Args:
            kpi_column: Tên cột KPI
            lookback_days: Số ngày để so sánh (default: từ config)
        
        Returns:
            List các alert dict
        """
        lookback_days = lookback_days or self.config['days_lookback']
        threshold = self.config['decline_threshold']
        kpi_rule = self._get_kpi_rule(kpi_column)
        
        print(f"\n🔍 Đang phân tích suy giảm cho {kpi_column}...")
        
        alerts = []
        provinces = self.df['CTKD7'].unique()
        
        for province in provinces:
            # QUAN TRỌNG: Lấy dữ liệu của tỉnh, bỏ qua các ngày có KPI = 0 hoặc null
            province_data = self.df[
                (self.df['CTKD7'] == province) & 
                (self.df[kpi_column].notna()) &
                (self.df[kpi_column] != 0)  # Bỏ qua ngày có KPI = 0
            ].copy()
            
            if len(province_data) < 2:
                continue
            
            # Sắp xếp theo ngày
            province_data = province_data.sort_values('Ngay7')
            
            # Lấy ngày gần nhất
            latest_date = province_data['Ngay7'].max()
            latest_value = province_data[province_data['Ngay7'] == latest_date][kpi_column].values[0]
            
            # Bỏ qua nếu giá trị gần nhất = 0
            if latest_value == 0:
                continue
            
            # Lấy giá trị so sánh (lookback_days trước)
            compare_date = latest_date - timedelta(days=lookback_days)
            # Bỏ qua các ngày có KPI = 0 trong period so sánh
            compare_data = province_data[
                (province_data['Ngay7'] <= compare_date) &
                (province_data[kpi_column].notna()) &
                (province_data[kpi_column] != 0)  # Bỏ qua giá trị 0
            ]
            
            if len(compare_data) == 0:
                continue
            
            # Lấy giá trị trung bình của period trước (chỉ tính các ngày có KPI > 0)
            compare_value = compare_data[kpi_column].mean()
            
            # Đánh giá xu hướng xấu đi theo hướng KPI
            if compare_value > 0:
                is_worse, change_pct = self._is_worsening(latest_value, compare_value, kpi_rule)
                limit_breached = self._is_limit_breached(latest_value, kpi_rule)

                should_alert = False
                if kpi_rule and limit_breached is not None:
                    # Chỉ alert khi VỪA xấu đi VỪA vi phạm ngưỡng
                    if is_worse and abs(change_pct) >= threshold and limit_breached:
                        should_alert = True
                else:
                    # Không có rule → dùng logic cũ theo higher_better
                    if is_worse and abs(change_pct) >= threshold:
                        should_alert = True

                if should_alert:
                    # map decline_pct về hướng “xấu đi” âm như trước để giữ tương thích
                    decline_like_pct = -abs(change_pct)
                    alert = {
                        'province': province,
                        'kpi': kpi_column,
                        'latest_date': latest_date,
                        'latest_value': latest_value,
                        'compare_value': compare_value,
                        'decline_pct': round(decline_like_pct, 2),
                        'severity': self._get_severity(decline_like_pct),
                        'days_lookback': lookback_days,
                        'limit': kpi_rule.get('limit') if kpi_rule else None,
                        'limit_breached': bool(limit_breached) if limit_breached is not None else None,
                        'direction': kpi_rule.get('direction') if kpi_rule else 'higher_better'
                    }
                    alerts.append(alert)
        
        # Sắp xếp theo mức độ suy giảm
        alerts.sort(key=lambda x: x['decline_pct'])
        
        print(f"   ⚠️  Phát hiện {len(alerts)} tỉnh có suy giảm")
        
        return alerts
    
    def _get_severity(self, decline_pct: float) -> str:
        """Xác định mức độ nghiêm trọng"""
        if decline_pct < -10:
            return 'Cực kỳ nghiêm trọng'
        elif decline_pct < -5:
            return 'Nghiêm trọng'
        elif decline_pct < -2:
            return 'Cảnh báo'
        else:
            return 'Nhẹ'
    
    def analyze_all_kpis(self) -> Dict[str, List[Dict]]:
        """Phân tích tất cả KPI quan trọng"""
        print("\n" + "="*60)
        print("📊 PHÂN TÍCH TẤT CẢ KPI QUAN TRỌNG")
        print("="*60)
        
        all_alerts = {}
        
        for kpi in self.config['critical_kpis']:
            if kpi not in self.df.columns:
                print(f"⚠️  Không tìm thấy cột: {kpi}")
                continue
            
            alerts = self.detect_declines(kpi)
            if alerts:
                all_alerts[kpi] = alerts
        
        self.decline_alerts = all_alerts
        return all_alerts
    
    def generate_decline_report(self) -> pd.DataFrame:
        """Tạo báo cáo tổng hợp các suy giảm"""
        if not self.decline_alerts:
            print("ℹ️  Không có suy giảm nào được phát hiện")
            return None
        
        # Tạo DataFrame từ alerts
        report_data = []
        for kpi, alerts in self.decline_alerts.items():
            for alert in alerts:
                report_data.append({
                    'KPI': kpi,
                    'Tỉnh': alert['province'],
                    'Ngày': alert['latest_date'].strftime('%d/%m/%Y'),
                    'Giá trị hiện tại': round(alert['latest_value'], 2),
                    'Giá trị trước': round(alert['compare_value'], 2),
                    'Suy giảm (%)': alert['decline_pct'],
                    'Mức độ': alert['severity']
                })
        
        report_df = pd.DataFrame(report_data)
        report_df = report_df.sort_values('Suy giảm (%)')
        
        return report_df
    
    def create_trend_charts(self, kpi_column: str, provinces: List[str] = None, 
                           output_path: str = None, lookback_days: int = None,
                           start_date: str = None, end_date: str = None,
                           exclude_dates: List[str] = None,
                           date_range_filter: tuple = None):
        """
        Tạo line chart như pivot chart để xem trend
        
        Args:
            kpi_column: Tên cột KPI
            provinces: Danh sách tỉnh (None = tất cả)
            output_path: Đường dẫn lưu chart
            lookback_days: Số ngày gần nhất để highlight (None = dùng từ config)
            start_date: Ngày bắt đầu highlight (format: 'DD/MM/YYYY' hoặc 'YYYY-MM-DD') - ưu tiên hơn lookback_days
            end_date: Ngày kết thúc highlight (format: 'DD/MM/YYYY' hoặc 'YYYY-MM-DD') - ưu tiên hơn lookback_days
        """
        print(f"\n📈 Đang tạo trend chart cho {kpi_column}...")
        
        # Lấy lookback_days từ config nếu không được truyền vào
        if lookback_days is None and not start_date and not end_date:
            lookback_days = self.config['days_lookback']
        
        # Sử dụng visualization module nếu có
        if KPIVisualization:
            viz = KPIVisualization(output_dir=self.config['charts_dir'])
            # Truyền ngưỡng nếu có
            kpi_rule = self._get_kpi_rule(kpi_column)
            threshold_line = (kpi_rule.get('limit') if kpi_rule and 'limit' in kpi_rule else None)
            lower_better = (kpi_rule.get('direction') == 'lower_better') if kpi_rule else None
            fig, ax = viz.create_pivot_line_chart(
                df=self.df,
                kpi_column=kpi_column,
                group_by='CTKD7',
                provinces=provinces,
                lookback_days=lookback_days,
                start_date=start_date,
                end_date=end_date,
                exclude_dates=exclude_dates,
                date_range_filter=date_range_filter,
                threshold_line=threshold_line,
                lower_better=lower_better
            )
            filename = f"trend_{kpi_column}_{datetime.now().strftime('%Y%m%d')}.png"
            return viz.save_chart(fig, filename)
        else:
            # Fallback: tự tạo chart
            df_filtered = self.df.copy()
            if provinces:
                df_filtered = df_filtered[df_filtered['CTKD7'].isin(provinces)]
            
            # Tính trend
            trend_data = self.calculate_trends(kpi_column)
            
            if provinces:
                trend_data = trend_data[trend_data['CTKD7'].isin(provinces)]
            
            # Tạo chart đẹp hơn
            fig, ax = plt.subplots(figsize=(18, 10))
            
            # Màu sắc đẹp hơn
            colors = plt.cm.tab10(range(len(trend_data['CTKD7'].unique())))
            
            # Plot từng tỉnh với styling đẹp
            for idx, province in enumerate(trend_data['CTKD7'].unique()):
                province_trend = trend_data[trend_data['CTKD7'] == province]
                ax.plot(province_trend['Ngay7'], province_trend[kpi_column], 
                        marker='o', label=province, 
                        linewidth=3.5, markersize=12,
                        alpha=0.9, markerfacecolor='white',
                        markeredgewidth=2.5, color=colors[idx])
            
            # Format ngày
            from matplotlib.dates import DateFormatter, DayLocator
            from matplotlib.ticker import MaxNLocator, FuncFormatter
            ax.xaxis.set_major_locator(DayLocator(interval=1))
            ax.xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))
            ax.yaxis.set_major_locator(MaxNLocator(nbins=20))
            
            def format_y_axis(value, pos):
                return f'{value:.2f}'
            ax.yaxis.set_major_formatter(FuncFormatter(format_y_axis))
            
            ax.set_title(f'Trend Analysis: {kpi_column} theo Tỉnh', 
                        fontsize=18, fontweight='bold', pad=25, color='#2c3e50')
            ax.set_xlabel('Ngày', fontsize=14, fontweight='bold', color='#34495e', labelpad=15)
            ax.set_ylabel(kpi_column, fontsize=14, fontweight='bold', color='#34495e', labelpad=15)
            
            # Legend đẹp hơn
            ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', 
                     fontsize=11, framealpha=0.95, 
                     edgecolor='#34495e', fancybox=True, shadow=True)
            
            # Grid đẹp hơn
            ax.grid(True, alpha=0.4, linestyle='--', which='major', color='#95a5a6', linewidth=1.2)
            ax.grid(True, alpha=0.2, linestyle=':', which='minor', color='#bdc3c7')
            
            # Spines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#34495e')
            ax.spines['left'].set_linewidth(2)
            ax.spines['bottom'].set_color('#34495e')
            ax.spines['bottom'].set_linewidth(2)
            
            ax.set_facecolor('#ffffff')
            fig.patch.set_facecolor('#ffffff')
            
            plt.xticks(rotation=45, ha='right', fontsize=11)
            plt.yticks(fontsize=11)
            plt.tight_layout(rect=[0, 0, 0.96, 1])
            
            # Lưu chart
            if output_path is None:
                output_path = f"{self.config['charts_dir']}/trend_{kpi_column}_{datetime.now().strftime('%Y%m%d')}.png"
            
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✅ Đã lưu chart: {output_path}")
            
            plt.close()
            return output_path

    def create_trend_charts_interactive(self, kpi_column: str, provinces: List[str] = None,
                                         exclude_dates: List[str] = None,
                                         date_range_filter: tuple = None,
                                         output_filename: str = None):
        """Chế độ tương tác: click để loại bỏ ngày và lưu bằng phím 's'."""
        if KPIVisualization is None:
            print("⚠️  Visualization module không khả dụng")
            return None
        viz = KPIVisualization(output_dir=self.config['charts_dir'])
        fig, ax = viz.interactive_pivot_line_chart(
            df=self.df,
            kpi_column=kpi_column,
            group_by='CTKD7',
            provinces=provinces,
            exclude_dates=exclude_dates,
            date_range_filter=date_range_filter,
            output_filename=output_filename
        )
        return fig
    
    def should_fetch_district_data(self, province: str, kpi: str) -> bool:
        """
        Quyết định có cần tải dữ liệu cấp huyện không
        
        Logic: Nếu tỉnh có suy giảm nghiêm trọng → cần drill down
        """
        if kpi not in self.decline_alerts:
            return False
        
        # Kiểm tra xem tỉnh có trong alert không
        for alert in self.decline_alerts[kpi]:
            if alert['province'] == province and alert['severity'] in ['Nghiêm trọng', 'Cực kỳ nghiêm trọng']:
                return True
        
        return False
    
    def get_provinces_needing_district_data(self) -> List[Dict]:
        """Lấy danh sách tỉnh cần tải dữ liệu huyện"""
        provinces_needing = []
        
        for kpi, alerts in self.decline_alerts.items():
            for alert in alerts:
                if alert['severity'] in ['Nghiêm trọng', 'Cực kỳ nghiêm trọng']:
                    provinces_needing.append({
                        'province': alert['province'],
                        'kpi': kpi,
                        'decline_pct': alert['decline_pct'],
                        'severity': alert['severity']
                    })
        
        # Remove duplicates
        seen = set()
        unique_list = []
        for item in provinces_needing:
            key = (item['province'], item['kpi'])
            if key not in seen:
                seen.add(key)
                unique_list.append(item)
        
        return unique_list


class DistrictDataFetcher:
    """Class để tải dữ liệu cấp huyện"""
    
    def __init__(self, api_endpoint: str = None, file_path: str = None):
        self.api_endpoint = api_endpoint
        self.file_path = file_path
    
    def fetch_district_data(self, province: str, date: datetime = None) -> pd.DataFrame:
        """
        Tải dữ liệu cấp huyện cho tỉnh
        
        Args:
            province: Tên tỉnh
            date: Ngày cần lấy dữ liệu (None = ngày gần nhất)
        
        Returns:
            DataFrame với dữ liệu huyện
        """
        print(f"\n📥 Đang tải dữ liệu cấp huyện cho {province}...")
        
        # TODO: Implement actual data fetching logic
        # Có thể:
        # 1. Gọi API để lấy dữ liệu
        # 2. Đọc từ file CSV khác
        # 3. Query từ database
        
        # Placeholder: Tạo mock data structure
        # Trong thực tế, bạn sẽ implement logic fetch thật
        
        print(f"⚠️  Cần implement logic fetch dữ liệu huyện")
        print(f"   - Province: {province}")
        print(f"   - Date: {date or 'Latest'}")
        
        # Ví dụ cấu trúc dữ liệu huyện
        district_data_structure = {
            'Ngay7': [],
            'Tinh': [],
            'Huyen': [],
            'MTCL_2024': [],
            'CSSR': [],
            'CDR': [],
            # ... các KPI khác
        }
        
        return pd.DataFrame(district_data_structure)
    
    def analyze_district_decline(self, district_df: pd.DataFrame, 
                                 kpi: str) -> pd.DataFrame:
        """Phân tích suy giảm theo huyện"""
        print(f"\n🔍 Đang phân tích suy giảm theo huyện cho {kpi}...")
        
        # Group by huyện và tính trend
        district_analysis = district_df.groupby('Huyen').agg({
            kpi: ['mean', 'min', 'max', 'count']
        }).reset_index()
        
        district_analysis.columns = ['Huyen', 'mean', 'min', 'max', 'count']
        
        # Sắp xếp theo mean (từ thấp nhất)
        district_analysis = district_analysis.sort_values('mean')
        
        return district_analysis


def main():
    """Hàm chính chạy pipeline"""
    print("="*60)
    print("🚀 PIPELINE PHÁT HIỆN SUY GIẢM KPI")
    print("="*60)
    
    # Khởi tạo detector
    detector = KPIDeclineDetector('1.Ngày.csv')
    
    # Step 1: Load và clean data
    detector.load_and_clean_data()
    
    # Step 2: Phân tích tất cả KPI quan trọng
    all_alerts = detector.analyze_all_kpis()
    
    # Step 3: Tạo báo cáo
    if all_alerts:
        report_df = detector.generate_decline_report()
        print("\n" + "="*60)
        print("📋 BÁO CÁO SUY GIẢM KPI")
        print("="*60)
        print(report_df.to_string(index=False))
        
        # Lưu báo cáo (an toàn khi file đang bị mở/khóa bởi Excel)
        import os
        date_str = datetime.now().strftime('%Y%m%d')
        os.makedirs('reports', exist_ok=True)
        report_path = f"reports/decline_report_{date_str}.csv"
        try:
            report_df.to_csv(report_path, index=False, encoding='utf-8-sig')
            print(f"\n✅ Đã lưu báo cáo: {report_path}")
        except PermissionError:
            # Ghi sang thư mục theo ngày với tên có timestamp để tránh xung đột khóa file
            dated_dir = os.path.join('reports', date_str)
            os.makedirs(dated_dir, exist_ok=True)
            ts = datetime.now().strftime('%H%M%S')
            alt_path = os.path.join(dated_dir, f"decline_report_{date_str}_{ts}.csv")
            report_df.to_csv(alt_path, index=False, encoding='utf-8-sig')
            print(f"\n⚠️  File {report_path} đang bị khóa (có thể đang mở trong Excel).\n   → Đã lưu tạm vào: {alt_path}")
    else:
        print("\n✅ Không phát hiện suy giảm nghiêm trọng nào")
    
    # Step 4: Tạo trend charts cho các KPI có vấn đề
    print("\n" + "="*60)
    print("📊 TẠO TREND CHARTS")
    print("="*60)
    
    for kpi in detector.config['critical_kpis']:
        if kpi in all_alerts and all_alerts[kpi]:
            # Lấy danh sách tỉnh có vấn đề
            provinces_with_issues = [alert['province'] for alert in all_alerts[kpi]]
            detector.create_trend_charts(kpi, provinces_with_issues)
    
    # Step 5: Gửi alerts
    if AlertSystem:
        print("\n" + "="*60)
        print("📢 GỬI ALERTS")
        print("="*60)
        
        alert_system = AlertSystem()
        
        # Gửi alerts cho tất cả suy giảm
        for kpi, alerts in all_alerts.items():
            for alert in alerts:
                alert_system.send_decline_alert(
                    province=alert['province'],
                    kpi=alert['kpi'],
                    decline_pct=alert['decline_pct'],
                    latest_value=alert['latest_value'],
                    compare_value=alert['compare_value']
                )
    
    # Step 6: Xác định tỉnh cần tải dữ liệu huyện
    print("\n" + "="*60)
    print("📥 XÁC ĐỊNH TỈNH CẦN DỮ LIỆU HUYỆN")
    print("="*60)
    
    provinces_needing = detector.get_provinces_needing_district_data()
    
    if provinces_needing:
        print(f"\n⚠️  Có {len(provinces_needing)} tỉnh cần tải dữ liệu huyện:")
        for item in provinces_needing:
            print(f"   - {item['province']}: {item['kpi']} (suy giảm {item['decline_pct']}%)")
        
        # Khởi tạo fetcher
        fetcher = DistrictDataFetcher()
        
        # Tải dữ liệu cho từng tỉnh
        for item in provinces_needing:
            district_data = fetcher.fetch_district_data(
                item['province'],
                datetime.now()
            )
            
            # Phân tích suy giảm theo huyện
            if len(district_data) > 0:
                district_analysis = fetcher.analyze_district_decline(
                    district_data, 
                    item['kpi']
                )
                print(f"\n📊 Top 5 huyện có vấn đề ở {item['province']}:")
                print(district_analysis.head().to_string(index=False))
    else:
        print("\n✅ Không có tỉnh nào cần tải dữ liệu huyện")
    
    print("\n" + "="*60)
    print("✅ Pipeline hoàn thành!")
    print("="*60)
    
    return detector, all_alerts


if __name__ == "__main__":
    detector, alerts = main()

