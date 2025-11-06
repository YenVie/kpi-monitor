"""
MODULE TẠO VISUALIZATION (Pivot Chart Line)
===========================================
Tạo các biểu đồ line chart giống pivot chart trong Excel
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Optional
import os
import sys

# Optional hover tooltips
try:
    import mplcursors
    HAS_MPLCURSORS = True
except ImportError:
    HAS_MPLCURSORS = False

# Optional seaborn
try:
    import seaborn as sns
    HAS_SEABORN = True
    sns.set_palette("husl")
except ImportError:
    HAS_SEABORN = False
    # Không hiển thị warning nữa

# Set style
try:
    plt.style.use('seaborn-v0_8-darkgrid')
except (OSError, ValueError):
    # Fallback nếu style không tồn tại
    try:
        plt.style.use('seaborn-darkgrid')
    except (OSError, ValueError):
        plt.style.use('default')

class KPIVisualization:
    """Class tạo các biểu đồ KPI"""
    
    def __init__(self, output_dir: str = 'charts'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def create_pivot_line_chart(self, df: pd.DataFrame, 
                                kpi_column: str,
                                group_by: str = 'CTKD7',
                                date_column: str = 'Ngay7',
                                provinces: Optional[List[str]] = None,
                                title: Optional[str] = None,
                                figsize: tuple = (16, 10),
                                lookback_days: Optional[int] = None,
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None,
                                exclude_dates: Optional[List[str]] = None,
                                date_range_filter: Optional[tuple] = None,
                                threshold_line: Optional[float] = None,
                                lower_better: Optional[bool] = None,
                                enable_hover: bool = True):
        """
        Tạo line chart giống pivot chart trong Excel
        
        Args:
            df: DataFrame với dữ liệu
            kpi_column: Tên cột KPI cần vẽ
            group_by: Cột để group (thường là CTKD7 - tỉnh)
            date_column: Cột ngày
            provinces: Danh sách tỉnh cần vẽ (None = tất cả)
            title: Tiêu đề chart
            figsize: Kích thước figure
            lookback_days: Số ngày gần nhất để highlight (None = không highlight)
            start_date: Ngày bắt đầu highlight (format: 'DD/MM/YYYY' hoặc 'YYYY-MM-DD') - ưu tiên hơn lookback_days
            end_date: Ngày kết thúc highlight (format: 'DD/MM/YYYY' hoặc 'YYYY-MM-DD') - ưu tiên hơn lookback_days
            exclude_dates: Danh sách ngày cần loại bỏ thủ công (format: ['DD/MM/YYYY', ...] hoặc ['YYYY-MM-DD', ...])
                          Ví dụ: ['16/10/2025', '20/10/2025'] hoặc ['2025-10-16', '2025-10-20']
            date_range_filter: Tuple (start, end) để chỉ hiển thị khoảng ngày này (format: ('DD/MM/YYYY', 'DD/MM/YYYY'))
                              Ví dụ: ('01/10/2025', '31/10/2025')
        """
        # Lọc dữ liệu (bỏ qua giá trị 0 và null)
        # QUAN TRỌNG: Đảm bảo df được copy và filter từ đầu
        df_filtered = df.copy()
        
        # Đảm bảo cột ngày là datetime
        if not pd.api.types.is_datetime64_any_dtype(df_filtered[date_column]):
            df_filtered[date_column] = pd.to_datetime(df_filtered[date_column], format='%d/%m/%Y', errors='coerce')
        
        # Bước 0: Lọc theo khoảng ngày (nếu có date_range_filter)
        if date_range_filter:
            start_filter, end_filter = date_range_filter
            try:
                # Thử parse format DD/MM/YYYY
                try:
                    start_dt = pd.to_datetime(start_filter, format='%d/%m/%Y')
                    end_dt = pd.to_datetime(end_filter, format='%d/%m/%Y')
                except ValueError:
                    # Thử parse format YYYY-MM-DD
                    start_dt = pd.to_datetime(start_filter, format='%Y-%m-%d')
                    end_dt = pd.to_datetime(end_filter, format='%Y-%m-%d')
                
                before_range = len(df_filtered)
                df_filtered = df_filtered[
                    (df_filtered[date_column] >= start_dt) & 
                    (df_filtered[date_column] <= end_dt)
                ].copy()
                after_range = len(df_filtered)
                print(f"📅 Lọc theo khoảng ngày: {start_filter} - {end_filter}")
                print(f"   Dữ liệu: {before_range} → {after_range} dòng")
            except Exception as e:
                print(f"⚠️  Lỗi parse date_range_filter: {e}. Bỏ qua filter này.")
        
        # Bước 0.5: Loại bỏ các ngày được chỉ định thủ công (nếu có exclude_dates)
        if exclude_dates:
            from datetime import datetime
            excluded_count = 0
            for exclude_date_str in exclude_dates:
                try:
                    # Thử parse format DD/MM/YYYY
                    try:
                        exclude_dt = pd.to_datetime(exclude_date_str, format='%d/%m/%Y')
                    except ValueError:
                        # Thử parse format YYYY-MM-DD
                        exclude_dt = pd.to_datetime(exclude_date_str, format='%Y-%m-%d')
                    
                    before_exclude = len(df_filtered)
                    df_filtered = df_filtered[df_filtered[date_column].dt.date != exclude_dt.date()].copy()
                    after_exclude = len(df_filtered)
                    excluded_count += (before_exclude - after_exclude)
                    print(f"🚫 Đã loại bỏ ngày {exclude_date_str}: {before_exclude - after_exclude} dòng")
                except Exception as e:
                    print(f"⚠️  Lỗi parse exclude_date '{exclude_date_str}': {e}. Bỏ qua.")
            
            if excluded_count > 0:
                print(f"✅ Tổng cộng đã loại bỏ {excluded_count} dòng từ {len(exclude_dates)} ngày được chỉ định")
        
        # Đảm bảo cột KPI là numeric (convert nếu cần)
        if df_filtered[kpi_column].dtype == 'object':
            df_filtered[kpi_column] = pd.to_numeric(df_filtered[kpi_column], errors='coerce')
        
        if provinces:
            df_filtered = df_filtered[df_filtered[group_by].isin(provinces)]
        
        # QUAN TRỌNG: Nếu một ngày có BẤT KỲ dòng nào KPI = 0 hoặc null, bỏ qua TOÀN BỘ ngày đó
        # 
        # Lý do loại bỏ:
        # 1. Ngày có KPI = 0 thường là ngày lỗi dữ liệu, số liệu không ổn định
        # 2. Pattern lỗi dữ liệu: Giá trị giảm đột ngột 1 ngày (100 → 55) rồi ngày sau tăng lại (55 → 100)
        #    → Đây KHÔNG phải suy giảm thực sự, mà là LỖI DỮ LIỆU
        #    → Nếu không loại bỏ sẽ dẫn đến nhầm lẫn trong phân tích suy giảm
        # 
        # Ví dụ thực tế:
        # - Ngày 15/10: CSSR = 100 (bình thường)
        # - Ngày 16/10: CSSR = 0, 55, 99 (lỗi dữ liệu, có giá trị = 0)
        # - Ngày 17/10: CSSR = 100 (bình thường)
        # → Ngày 16/10 sẽ bị loại bỏ hoàn toàn để tránh hiển thị "suy giảm" giả
        # 
        # Phương pháp: Kiểm tra từng nhóm (ngày + tỉnh) và loại bỏ nếu có BẤT KỲ giá trị = 0, null, hoặc <= 0
        
        # Bước 1: Convert cột KPI sang numeric để đảm bảo so sánh đúng
        df_filtered[kpi_column] = pd.to_numeric(df_filtered[kpi_column], errors='coerce')
        
        print(f"🔍 Đang kiểm tra {len(df_filtered)} dòng để tìm các ngày có KPI = 0...")
        
        # Bước 2: Kiểm tra từng nhóm (ngày + tỉnh) một cách chặt chẽ
        # Tạo một hàm kiểm tra để đảm bảo TẤT CẢ giá trị trong nhóm đều > 0 và không null
        def is_group_valid(group_series):
            """
            Kiểm tra xem nhóm có hợp lệ không
            Nhóm hợp lệ = TẤT CẢ giá trị phải > 0 và không null
            
            QUAN TRỌNG: Nếu có BẤT KỲ giá trị = 0, null, hoặc <= 0 → LOẠI BỎ
            Lý do: Ngày có KPI = 0 thường là ngày lỗi dữ liệu
            Ví dụ: Ngày giảm đột ngột (100 → 55) rồi ngày sau tăng lại (55 → 100)
            → Đây là lỗi dữ liệu, không phải suy giảm thực sự → Cần loại bỏ
            """
            # Chuyển sang numeric nếu chưa
            numeric_values = pd.to_numeric(group_series, errors='coerce')
            
            # Kiểm tra có null không (bao gồm cả NaN sau khi convert)
            if numeric_values.isna().any():
                return False
            
            # Kiểm tra có giá trị = 0 không (chặt chẽ nhất)
            # Đây là dấu hiệu rõ ràng nhất của lỗi dữ liệu
            if (numeric_values == 0).any():
                return False
            
            # Kiểm tra có giá trị < 0 không
            if (numeric_values < 0).any():
                return False
            
            # Kiểm tra có giá trị <= 0 không (double check)
            if (numeric_values <= 0).any():
                return False
            
            # Kiểm tra tất cả giá trị phải > 0 (final check)
            if not (numeric_values > 0).all():
                return False
            
            # Kiểm tra min value phải > 0
            if numeric_values.min() <= 0:
                return False
            
            return True
        
        # Groupby và kiểm tra từng nhóm
        groups_validity = df_filtered.groupby([date_column, group_by])[kpi_column].apply(
            is_group_valid
        ).reset_index(name='is_valid')
        
        # Lấy danh sách các nhóm hợp lệ
        valid_groups = groups_validity[groups_validity['is_valid']][[date_column, group_by]]
        
        # Lấy danh sách các nhóm không hợp lệ để debug
        invalid_groups = groups_validity[~groups_validity['is_valid']]
        
        if len(invalid_groups) > 0:
            print(f"\n⚠️  Đã loại bỏ {len(invalid_groups)} nhóm (ngày + tỉnh) có KPI = 0 hoặc null:")
            for _, row in invalid_groups.head(30).iterrows():
                date_str = row[date_column].strftime('%d/%m/%Y') if hasattr(row[date_column], 'strftime') else str(row[date_column])
                # Lấy dữ liệu thực tế của nhóm này để debug
                group_data = df_filtered[
                    (df_filtered[date_column] == row[date_column]) & 
                    (df_filtered[group_by] == row[group_by])
                ][kpi_column]
                group_values = pd.to_numeric(group_data, errors='coerce')
                
                reasons = []
                null_count = group_values.isna().sum()
                zero_count = (group_values == 0).sum()
                negative_count = (group_values < 0).sum()
                
                if null_count > 0:
                    reasons.append(f"{null_count} null")
                if zero_count > 0:
                    reasons.append(f"{zero_count} giá trị = 0")
                if negative_count > 0:
                    reasons.append(f"{negative_count} giá trị < 0")
                
                unique_values = sorted(group_values.dropna().unique())
                print(f"   - {date_str} ({row[group_by]}): {', '.join(reasons) if reasons else 'không hợp lệ'}")
                print(f"     Giá trị trong nhóm: {unique_values[:10]}")
                print(f"     Mean nếu không filter: {group_values.mean():.2f}")
                
                # Đặc biệt chú ý nếu có KPI = 0 nhưng mean > 0
                # Trường hợp này: Ngày có lỗi dữ liệu, một số giá trị = 0, một số > 0
                # Ví dụ: Ngày 16/10 có giá trị 0, 55, 99 → mean = 51.33 > 0
                # Nhưng ngày 15/10 = 100, ngày 17/10 = 100 → Đây là lỗi dữ liệu, không phải suy giảm thực sự
                # → Cần loại bỏ toàn bộ ngày để đảm bảo tính nhất quán và tránh nhầm lẫn
                if zero_count > 0 and group_values.mean() > 0:
                    print(f"     ⚠️  CẢNH BÁO: Có {zero_count} giá trị = 0 nhưng mean = {group_values.mean():.2f} > 0")
                    print(f"     → Đây là ngày lỗi dữ liệu (số liệu không ổn định)")
                    print(f"     → Pattern: Giảm đột ngột 1 ngày rồi ngày sau trở lại bình thường = LỖI DỮ LIỆU")
                    print(f"     → Nhóm này SẼ BỊ LOẠI BỎ để tránh nhầm lẫn với suy giảm thực sự")
        
        print(f"✅ Tìm thấy {len(valid_groups)} nhóm (ngày + tỉnh) hợp lệ")
        
        # Bước 3: Chỉ giữ các nhóm hợp lệ
        if len(valid_groups) > 0:
            # Đảm bảo kiểu dữ liệu khớp nhau trước khi merge
            for col in [date_column, group_by]:
                if df_filtered[col].dtype != valid_groups[col].dtype:
                    if pd.api.types.is_datetime64_any_dtype(df_filtered[col]):
                        valid_groups[col] = pd.to_datetime(valid_groups[col])
                    else:
                        valid_groups[col] = valid_groups[col].astype(df_filtered[col].dtype)
            
            # Merge để chỉ giữ các nhóm hợp lệ
            before_merge = len(df_filtered)
            df_filtered = pd.merge(
                df_filtered,
                valid_groups,
                on=[date_column, group_by],
                how='inner'  # Chỉ giữ các nhóm hợp lệ
            )
            after_merge = len(df_filtered)
            print(f"📊 Sau khi merge: {before_merge} → {after_merge} dòng (loại bỏ {before_merge - after_merge} dòng)")
            
            # Kiểm tra sau merge: Đảm bảo không còn giá trị 0 hoặc <= 0
            kpi_numeric = pd.to_numeric(df_filtered[kpi_column], errors='coerce')
            has_zero_after_merge = (kpi_numeric == 0).any()
            has_negative_after_merge = (kpi_numeric < 0).any()
            has_null_after_merge = kpi_numeric.isna().any()
            
            if has_zero_after_merge or has_negative_after_merge or has_null_after_merge:
                print(f"\n❌ LỖI NGHIÊM TRỌNG: Sau merge vẫn còn giá trị không hợp lệ!")
                if has_zero_after_merge:
                    zero_count = (kpi_numeric == 0).sum()
                    print(f"   - Có {zero_count} giá trị = 0")
                    # Lấy các nhóm có giá trị 0
                    zero_groups = df_filtered[kpi_numeric == 0][[date_column, group_by]].drop_duplicates()
                    for _, z_row in zero_groups.head(10).iterrows():
                        date_str = z_row[date_column].strftime('%d/%m/%Y') if hasattr(z_row[date_column], 'strftime') else str(z_row[date_column])
                        print(f"     * {date_str} ({z_row[group_by]})")
                if has_negative_after_merge:
                    print(f"   - Có {(kpi_numeric < 0).sum()} giá trị < 0")
                if has_null_after_merge:
                    print(f"   - Có {kpi_numeric.isna().sum()} giá trị null")
                # Loại bỏ chúng ngay lập tức
                df_filtered = df_filtered[
                    (kpi_numeric.notna()) & 
                    (kpi_numeric > 0)
                ].copy()
                print(f"   ✅ Đã loại bỏ các giá trị không hợp lệ, còn {len(df_filtered)} dòng")
            else:
                print(f"✅ Xác nhận: Sau merge, TẤT CẢ {len(df_filtered)} dòng đều có giá trị > 0 và không null")
        else:
            # Nếu không có nhóm hợp lệ nào, tạo DataFrame rỗng
            df_filtered = df_filtered.iloc[0:0].copy()
            print(f"⚠️  Không có nhóm hợp lệ nào")
        
        # Bước 4: Final check - đảm bảo chỉ giữ các dòng có giá trị > 0 (double check)
        before_final = len(df_filtered)
        df_filtered = df_filtered[
            (df_filtered[kpi_column].notna()) & 
            (pd.to_numeric(df_filtered[kpi_column], errors='coerce') > 0)
        ].copy()
        after_final = len(df_filtered)
        if before_final != after_final:
            print(f"⚠️  Final check loại bỏ thêm {before_final - after_final} dòng")
        
        print(f"✅ Sau khi filter: còn {len(df_filtered)} dòng hợp lệ")
        
        # Nhóm theo ngày và tỉnh - chỉ tính mean của các ngày đã được validate
        if len(df_filtered) > 0:
            pivot_data = df_filtered.groupby([date_column, group_by])[kpi_column].mean().reset_index()
            
            # Convert sang numeric để đảm bảo so sánh đúng
            pivot_data[kpi_column] = pd.to_numeric(pivot_data[kpi_column], errors='coerce')
            
            # QUAN TRỌNG: Sau khi groupby, vẫn phải bỏ qua các ngày có mean = 0, <= 0, hoặc null
            before_final_filter = len(pivot_data)
            pivot_data = pivot_data[
                (pivot_data[kpi_column].notna()) & 
                (pivot_data[kpi_column] > 0)  # Đảm bảo mean > 0 (chặt chẽ hơn != 0)
            ].copy()
            after_final_filter = len(pivot_data)
            if before_final_filter != after_final_filter:
                print(f"⚠️  Final filter sau groupby loại bỏ thêm {before_final_filter - after_final_filter} ngày")
            
            # Debug: Kiểm tra xem có ngày nào có giá trị = 0, <= 0, hoặc null không (sau khi đã filter)
            invalid_values = pivot_data[
                (pivot_data[kpi_column].isna()) |
                (pivot_data[kpi_column] == 0) | 
                (pivot_data[kpi_column] <= 0)
            ]
            if len(invalid_values) > 0:
                print(f"\n❌ LỖI NGHIÊM TRỌNG: Vẫn còn {len(invalid_values)} ngày có giá trị không hợp lệ sau khi filter:")
                for _, row in invalid_values.head(10).iterrows():
                    date_str = row[date_column].strftime('%d/%m/%Y') if hasattr(row[date_column], 'strftime') else str(row[date_column])
                    print(f"   - {date_str} ({row[group_by]}): mean={row[kpi_column]}")
                # Loại bỏ chúng ngay lập tức
                pivot_data = pivot_data[~pivot_data.index.isin(invalid_values.index)].copy()
                print(f"   ✅ Đã loại bỏ {len(invalid_values)} ngày không hợp lệ")
            
            # Final verification: Đảm bảo KHÔNG CÒN giá trị nào <= 0 hoặc null
            final_check = pivot_data[
                (pivot_data[kpi_column].isna()) |
                (pivot_data[kpi_column] <= 0)
            ]
            if len(final_check) > 0:
                print(f"\n❌❌❌ LỖI NGHIÊM TRỌNG: Vẫn còn {len(final_check)} ngày không hợp lệ sau final check!")
                sys.exit(1)
            else:
                print(f"✅ Xác nhận: Tất cả {len(pivot_data)} ngày trong pivot_data đều có giá trị > 0")
        else:
            # Nếu không có dữ liệu hợp lệ, tạo DataFrame rỗng
            pivot_data = pd.DataFrame(columns=[date_column, group_by, kpi_column])
            print("⚠️  Không có dữ liệu hợp lệ để vẽ chart")
        
        # Tính toán khoảng highlight: ưu tiên start_date/end_date, nếu không có thì dùng lookback_days
        highlight_start_date = None
        highlight_end_date = None
        
        if len(pivot_data) > 0:
            from datetime import datetime, timedelta
            
            # Nếu có start_date và end_date, dùng ngày cụ thể
            if start_date and end_date:
                try:
                    # Thử parse format DD/MM/YYYY
                    try:
                        highlight_start_date = datetime.strptime(start_date, '%d/%m/%Y')
                        highlight_end_date = datetime.strptime(end_date, '%d/%m/%Y')
                    except ValueError:
                        # Thử parse format YYYY-MM-DD
                        highlight_start_date = datetime.strptime(start_date, '%Y-%m-%d')
                        highlight_end_date = datetime.strptime(end_date, '%Y-%m-%d')
                    
                    # Đảm bảo start_date <= end_date
                    if highlight_start_date > highlight_end_date:
                        highlight_start_date, highlight_end_date = highlight_end_date, highlight_start_date
                    
                    print(f"✅ Highlight khoảng: {highlight_start_date.strftime('%d/%m/%Y')} - {highlight_end_date.strftime('%d/%m/%Y')}")
                except ValueError as e:
                    print(f"⚠️  Lỗi parse ngày: {e}. Sử dụng lookback_days thay thế.")
                    start_date = None
                    end_date = None
            
            # Nếu không có ngày cụ thể, dùng lookback_days
            if not start_date and not end_date and lookback_days:
                max_date = pivot_data[date_column].max()
                highlight_end_date = max_date
                # Tính toán để highlight đúng số ngày: từ (max_date - lookback_days + 1) đến max_date
                # Ví dụ: nếu lookback_days=14 và max_date=31/10, thì từ 18/10 đến 31/10 = 14 ngày
                highlight_start_date = max_date - timedelta(days=lookback_days - 1)
        
        # Tạo chart với kích thước lớn hơn
        fig, ax = plt.subplots(figsize=(18, 10))
        
        # Màu sắc riêng cho từng tỉnh (đủ nhiều màu)
        provinces_list = list(pivot_data[group_by].unique())
        n_colors = max(1, len(provinces_list))
        if HAS_SEABORN:
            palette = sns.color_palette('tab20', n_colors=n_colors)
        else:
            cmap = plt.cm.get_cmap('tab20', n_colors)
            palette = [cmap(i) for i in range(n_colors)]
        
        # Vẽ line cho từng tỉnh với styling đẹp hơn
        line_artists = []
        # Cache cho hover nhanh (không tốn CPU mỗi khi di chuột)
        hover_cache = []  # list[{label, xnum, xraw, y}]
        for idx, province in enumerate(provinces_list):
            province_data = pivot_data[pivot_data[group_by] == province].copy()
            province_data = province_data.sort_values(date_column)
            
            # QUAN TRỌNG: Lọc lại một lần nữa trước khi vẽ để đảm bảo không có giá trị 0 hoặc <= 0
            province_data = province_data[
                (province_data[kpi_column].notna()) & 
                (province_data[kpi_column] != 0) &
                (province_data[kpi_column] > 0)  # Đảm bảo giá trị > 0
            ].copy()
            
            if len(province_data) == 0:
                continue  # Bỏ qua tỉnh này nếu không có dữ liệu hợp lệ
            
            # Vẽ line với marker đẹp hơn
            line = ax.plot(province_data[date_column], 
                   province_data[kpi_column],
                   marker='o', 
                   label=province,
                   linewidth=3.5,
                   markersize=12,
                   alpha=0.9,
                   markerfacecolor='white',
                   markeredgewidth=2.5,
                   markeredgecolor=palette[idx],
                   color=palette[idx],
                   zorder=3)
            try:
                line[0].set_pickradius(8)
                line_artists.append(line[0])
                # Chuẩn bị cache cho motion event
                import matplotlib.dates as mdates
                xraw = province_data[date_column].values
                try:
                    xnum = mdates.date2num(pd.to_datetime(xraw))
                except Exception:
                    xnum = np.asarray(xraw, dtype=float)
                yval = province_data[kpi_column].values.astype(float)
                hover_cache.append({'label': province, 'xnum': xnum, 'xraw': xraw, 'y': yval})
            except Exception:
                pass
        
        # Formatting đẹp hơn
        title_text = title or f'Trend Analysis: {kpi_column}'
        ax.set_title(title_text, fontsize=18, fontweight='bold', pad=25, color='#2c3e50')
        ax.set_xlabel('Ngày', fontsize=14, fontweight='bold', color='#34495e', labelpad=15)
        ax.set_ylabel(kpi_column, fontsize=14, fontweight='bold', color='#34495e', labelpad=15)
        
        # Vẽ đường ngưỡng nếu có
        if threshold_line is not None:
            ax.axhline(threshold_line, color='#e74c3c', linestyle='--', linewidth=1.8, alpha=0.9, zorder=2)
            label_txt = f"Ngưỡng: {threshold_line}"
            if lower_better is True:
                label_txt += " (thấp hơn tốt)"
            elif lower_better is False:
                label_txt += " (cao hơn tốt)"
            ax.text(0.99, 0.02, label_txt, transform=ax.transAxes, fontsize=9, color='#e74c3c', ha='right', va='bottom')
        
        # Format ngày trên trục X chi tiết hơn
        from matplotlib.dates import DateFormatter, DayLocator, AutoDateLocator
        ax.xaxis.set_major_locator(DayLocator(interval=1))  # Hiển thị mỗi ngày
        ax.xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))  # Format: DD/MM/YYYY
        
        # Format chi tiết trục Y - nhiều ticks hơn
        from matplotlib.ticker import MaxNLocator, FuncFormatter, MultipleLocator
        # Tự động tạo nhiều ticks trên trục Y
        ax.yaxis.set_major_locator(MaxNLocator(nbins=20))  # Tăng lên 20 ticks
        
        # Format số trên trục Y cố định 2 chữ số thập phân
        from matplotlib.ticker import FuncFormatter
        def format_y_axis(value, pos):
            return f'{value:.2f}'
        ax.yaxis.set_major_formatter(FuncFormatter(format_y_axis))
        
        # Thêm minor ticks cho trục Y
        ax.yaxis.set_minor_locator(MaxNLocator(nbins=40))
        
        # Legend đẹp hơn
        legend = ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', 
                 fontsize=11, framealpha=0.95, 
                 edgecolor='#34495e', fancybox=True, shadow=True,
                 title='Tỉnh/Thành phố', title_fontsize=12)
        legend.get_frame().set_facecolor('#f8f9fa')
        legend.get_frame().set_linewidth(1.5)
        
        # Grid chi tiết và đẹp hơn
        ax.grid(True, alpha=0.4, linestyle='--', which='major', 
               color='#95a5a6', linewidth=1.2)
        ax.grid(True, alpha=0.2, linestyle=':', which='minor', 
               color='#bdc3c7', linewidth=0.8)
        
        # Spines (viền) đẹp hơn
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#34495e')
        ax.spines['left'].set_linewidth(2)
        ax.spines['bottom'].set_color('#34495e')
        ax.spines['bottom'].set_linewidth(2)
        
        # Background màu trắng sạch
        ax.set_facecolor('#ffffff')
        fig.patch.set_facecolor('#ffffff')
        
        # Rotate x-axis labels để hiển thị rõ hơn
        plt.xticks(rotation=45, ha='right', fontsize=11)
        plt.yticks(fontsize=11)
        
        # Thêm padding cho tick labels
        ax.tick_params(axis='x', pad=8)
        ax.tick_params(axis='y', pad=8)
        
        # Highlight khoảng so sánh nếu có lookback_days (chỉ vùng màu vàng và đường thẳng, không có text)
        if highlight_start_date and highlight_end_date:
            # Tô màu vùng so sánh (nền vàng nhạt) - đặt sau line
            y_min, y_max = ax.get_ylim()
            ax.axvspan(highlight_start_date, highlight_end_date, 
                      alpha=0.2, color='#ffd700', 
                      zorder=0)  # Đặt ở zorder thấp nhất
            
            # Thêm đường thẳng đánh dấu rõ ràng hơn - đặt sau line
            ax.axvline(x=highlight_start_date, color='#ff8c00', 
                      linestyle='--', linewidth=3, alpha=0.8,
                      zorder=2)  # Sau line (zorder=3)
            ax.axvline(x=highlight_end_date, color='#dc3545', 
                      linestyle='--', linewidth=3, alpha=0.8,
                      zorder=2)  # Sau line (zorder=3)
        
        # Cố định padding/subplot theo thiết lập người dùng yêu cầu
        try:
            fig.subplots_adjust(left=0.097, right=0.823, top=0.895, bottom=0.16, wspace=0.2, hspace=0.2)
        except Exception:
            plt.tight_layout(rect=[0, 0, 0.96, 1])

        # Hover tooltip (nếu có mplcursors)
        if enable_hover and HAS_MPLCURSORS and line_artists:
            cursor = mplcursors.cursor(line_artists, hover=True)
            @cursor.connect("add")
            def _(sel):
                art = sel.artist
                x, y = art.get_data()
                i = sel.index
                try:
                    date_str = pd.to_datetime(x[i]).strftime('%d/%m/%Y')
                except Exception:
                    date_str = str(x[i])
                province_name = art.get_label()
                sel.annotation.set(text=f"{province_name}\n{date_str}\n{kpi_column}: {y[i]:.2f}")
                sel.annotation.get_bbox_patch().set(alpha=0.9)
                # Đồng bộ trạng thái toolbar theo điểm được chọn (nhẹ, không chạy trên mọi motion)
                toolbar = getattr(fig.canvas, 'toolbar', None)
                if toolbar and hasattr(toolbar, 'set_message'):
                    toolbar.set_message(f"(x, y) = ({date_str}, {y[i]:.2f}) | {province_name}")

        # Thêm handler nhẹ: khi rê gần bất kỳ đường line nào → hiện tỉnh + (ngày, giá trị)
        cache_by_label = {it['label']: it for it in hover_cache}
        def _status_on_line(event):
            if event.inaxes is not ax:
                return
            toolbar = getattr(fig.canvas, 'toolbar', None)
            if not (toolbar and hasattr(toolbar, 'set_message')):
                return
            try:
                for ln in line_artists:
                    hit, _ = ln.contains(event)
                    if hit:
                        label = ln.get_label()
                        item = cache_by_label.get(label)
                        if item is not None and event.xdata is not None:
                            # Trên trục ngày, event.xdata đã ở dạng date2num → dùng trực tiếp để tránh sai lệch
                            try:
                                xevt = float(event.xdata)
                            except Exception:
                                xevt = None
                            idx = int(np.argmin(np.abs(item['xnum'] - xevt)))
                            try:
                                date_str = pd.to_datetime(item['xraw'][idx]).strftime('%d/%m/%Y')
                            except Exception:
                                date_str = str(item['xraw'][idx])
                            yv = float(item['y'][idx])
                            toolbar.set_message(f"(x, y) = ({date_str}, {yv:.2f}) | {label}")
                        else:
                            toolbar.set_message(f"Line: {label}")
                        return
                # nếu không trúng line nào, giữ nguyên hoặc xoá message tùy backend
            except Exception:
                pass
        fig.canvas.mpl_connect('motion_notify_event', _status_on_line)
        
        return fig, ax

    def interactive_pivot_line_chart(self, df: pd.DataFrame,
                                     kpi_column: str,
                                     group_by: str = 'CTKD7',
                                     date_column: str = 'Ngay7',
                                     provinces: Optional[List[str]] = None,
                                     title: Optional[str] = None,
                                     exclude_dates: Optional[List[str]] = None,
                                     date_range_filter: Optional[tuple] = None,
                                     output_filename: Optional[str] = None):
        """
        Chế độ tương tác: click vào điểm để loại bỏ ngày lỗi trực tiếp trên biểu đồ.
        - Chuột trái: chọn/bỏ chọn ngày tại điểm đang click
        - Phím r: vẽ lại biểu đồ với các ngày đã loại bỏ
        - Phím s: lưu chart (PNG) và đóng
        - Phím q hoặc đóng cửa sổ: thoát (không lưu nếu chưa nhấn s)
        """
        # Dùng pipeline filter giống create_pivot_line_chart, nhưng giữ lại pivot_data ban đầu
        base_fig, base_ax = self.create_pivot_line_chart(
            df=df,
            kpi_column=kpi_column,
            group_by=group_by,
            date_column=date_column,
            provinces=provinces,
            title=title,
            lookback_days=None,
            start_date=None,
            end_date=None,
            exclude_dates=exclude_dates,
            date_range_filter=date_range_filter
        )
        # Thu nhỏ kích thước cho chế độ tương tác (vừa phải hơn)
        try:
            base_fig.set_size_inches(12, 7, forward=True)
            # Giữ đúng thông số subplot theo yêu cầu
            base_fig.subplots_adjust(left=0.097, right=0.823, top=0.895, bottom=0.16, wspace=0.2, hspace=0.2)
        except Exception:
            pass

        # Thu thập dữ liệu hiển thị để xác định ngày khi click
        lines = base_ax.get_lines()
        for ln in lines:
            ln.set_picker(5)
            try:
                ln.set_pickradius(8)
            except Exception:
                pass

        # Hover tooltip cho chế độ tương tác
        if HAS_MPLCURSORS and lines:
            cur = mplcursors.cursor(lines, hover=True)
            @cur.connect("add")
            def _(sel):
                art = sel.artist
                x, y = art.get_data()
                i = sel.index
                try:
                    date_str = pd.to_datetime(x[i]).strftime('%d/%m/%Y')
                except Exception:
                    date_str = str(x[i])
                province_name = art.get_label()
                ylabel = base_ax.get_ylabel() or 'KPI'
                sel.annotation.set(text=f"{province_name}\n{date_str}\n{ylabel}: {y[i]:.2f}")
                sel.annotation.get_bbox_patch().set(alpha=0.9)
                toolbar = getattr(base_fig.canvas, 'toolbar', None)
                if toolbar and hasattr(toolbar, 'set_message'):
                    toolbar.set_message(f"(x, y) = ({date_str}, {y[i]:.2f}) | {province_name}")

        # Hiển thị tên tỉnh + (ngày, giá trị) khi rê gần line trong chế độ tương tác
        def _status_on_line_interactive(event):
            if event.inaxes is not base_ax:
                return
            toolbar = getattr(base_fig.canvas, 'toolbar', None)
            if not (toolbar and hasattr(toolbar, 'set_message')):
                return
            try:
                for ln in lines:
                    hit, _ = ln.contains(event)
                    if hit:
                        label = ln.get_label()
                        xdata = ln.get_xdata()
                        ydata = ln.get_ydata()
                        if event.xdata is not None:
                            # event.xdata đã là date2num nếu trục là ngày
                            try:
                                xevt = float(event.xdata)
                            except Exception:
                                xevt = None
                            try:
                                import matplotlib.dates as mdates
                                xnum = mdates.date2num(pd.to_datetime(xdata))
                            except Exception:
                                xnum = np.asarray(xdata, dtype=float)
                            idx = int(np.argmin(np.abs(xnum - xevt)))
                            try:
                                date_str = pd.to_datetime(xdata[idx]).strftime('%d/%m/%Y')
                            except Exception:
                                date_str = str(xdata[idx])
                            toolbar.set_message(f"(x, y) = ({date_str}, {float(ydata[idx]):.2f}) | {label}")
                        else:
                            toolbar.set_message(f"Line: {label}")
                        return
            except Exception:
                pass
        base_fig.canvas.mpl_connect('motion_notify_event', _status_on_line_interactive)

        selected_dates = set()
        highlight_artists = []

        def toggle_highlight(xdate):
            # Vẽ nền mờ cho ngày đang chọn
            import matplotlib.dates as mdates
            span = base_ax.axvspan(xdate, xdate, color='#ffeb3b', alpha=0.35, zorder=0)
            highlight_artists.append(span)
            base_fig.canvas.draw_idle()

        def clear_highlights():
            while highlight_artists:
                artist = highlight_artists.pop()
                artist.remove()

        def on_pick(event):
            # Lấy ngày tại chỉ số điểm được pick
            line = event.artist
            ind = event.ind[0]
            xdata = line.get_xdata()
            if ind < len(xdata):
                xdate = xdata[ind]
                # Toggle
                if xdate in selected_dates:
                    selected_dates.remove(xdate)
                else:
                    selected_dates.add(xdate)
                clear_highlights()
                for d in selected_dates:
                    toggle_highlight(d)

                base_ax.set_title((title or f'Trend Analysis: {kpi_column}') + 
                                   f"  |  Đã chọn loại bỏ: {len(selected_dates)} ngày",
                                   fontsize=18, fontweight='bold', pad=25, color='#2c3e50')
                base_fig.canvas.draw_idle()

        def on_key(event):
            if event.key == 'r':
                # Vẽ lại với exclude_dates = selected_dates
                clear_highlights()
                for artist in base_ax.lines + base_ax.collections:
                    try:
                        artist.remove()
                    except Exception:
                        pass
                # Tạo chart mới với exclude
                exclude_strs = []
                for d in sorted(selected_dates):
                    try:
                        exclude_strs.append(pd.to_datetime(d).strftime('%d/%m/%Y'))
                    except Exception:
                        exclude_strs.append(str(d))
                print(f"🚫 Loại bỏ tạm thời các ngày: {exclude_strs}")
                # Gọi lại create_pivot_line_chart để vẽ lại trục và line
                plt.close(base_fig)
                fig2, ax2 = self.create_pivot_line_chart(
                    df=df,
                    kpi_column=kpi_column,
                    group_by=group_by,
                    date_column=date_column,
                    provinces=provinces,
                    title=title,
                    exclude_dates=exclude_strs,
                    date_range_filter=date_range_filter
                )
                try:
                    fig2.set_size_inches(12, 7, forward=True)
                    fig2.subplots_adjust(left=0.097, right=0.823, top=0.895, bottom=0.16, wspace=0.2, hspace=0.2)
                except Exception:
                    pass
                fig2.canvas.mpl_connect('pick_event', on_pick)
                fig2.canvas.mpl_connect('key_press_event', on_key)
                fig2.show()
            elif event.key == 's':
                if output_filename is None:
                    filename = f"trend_{kpi_column}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
                else:
                    filename = output_filename
                self.save_chart(base_fig, filename)
                print(f"✅ Đã lưu chart (interactive): {os.path.join(self.output_dir, filename)}")
                plt.close(base_fig)
            elif event.key == 'q':
                plt.close(base_fig)

        cid1 = base_fig.canvas.mpl_connect('pick_event', on_pick)
        cid2 = base_fig.canvas.mpl_connect('key_press_event', on_key)

        # Hướng dẫn nhanh
        base_ax.text(0.01, 1.02,
                     "Click điểm để chọn/bỏ ngày | r: vẽ lại | s: lưu | q: thoát",
                     transform=base_ax.transAxes, fontsize=10, color='#555555')

        plt.show()
        return base_fig, base_ax
    
    def create_comparison_chart(self, df: pd.DataFrame,
                               kpi_column: str,
                               compare_dates: List[str],
                               group_by: str = 'CTKD7'):
        """
        Tạo chart so sánh giữa các ngày
        
        Args:
            df: DataFrame
            kpi_column: Tên cột KPI
            compare_dates: Danh sách ngày cần so sánh
            group_by: Cột group
        """
        # Lọc dữ liệu theo các ngày
        df_filtered = df[df['Ngay7'].isin(compare_dates)].copy()
        
        # Pivot để có ngày làm cột
        pivot_table = df_filtered.pivot_table(
            values=kpi_column,
            index=group_by,
            columns='Ngay7',
            aggfunc='mean'
        )
        
        # Tạo bar chart
        fig, ax = plt.subplots(figsize=(14, 8))
        
        pivot_table.plot(kind='bar', ax=ax, width=0.8)
        
        ax.set_title(f'So sánh {kpi_column} giữa các ngày', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel(group_by, fontsize=12)
        ax.set_ylabel(kpi_column, fontsize=12)
        ax.legend(title='Ngày', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        return fig, ax
    
    def create_decline_alert_chart(self, alerts: List[dict],
                                   kpi_column: str):
        """
        Tạo chart highlight các tỉnh có suy giảm
        
        Args:
            alerts: List các alert dict
            kpi_column: Tên KPI
        """
        if not alerts:
            return None
        
        # Tạo DataFrame từ alerts
        alert_df = pd.DataFrame(alerts)
        
        # Tạo bar chart
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Sort by decline percentage
        alert_df = alert_df.sort_values('decline_pct')
        
        # Color by severity
        colors = []
        for severity in alert_df['severity']:
            if 'Cực kỳ' in severity:
                colors.append('#d32f2f')  # Red
            elif 'Nghiêm trọng' in severity:
                colors.append('#f57c00')  # Orange
            elif 'Cảnh báo' in severity:
                colors.append('#fbc02d')  # Yellow
            else:
                colors.append('#689f38')  # Green
        
        bars = ax.barh(alert_df['province'], alert_df['decline_pct'], color=colors)
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, alert_df['decline_pct'])):
            ax.text(value - 0.5, i, f'{value:.2f}%', 
                   va='center', fontsize=9, fontweight='bold')
        
        ax.set_title(f'Các tỉnh có suy giảm {kpi_column}', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Suy giảm (%)', fontsize=12)
        ax.set_ylabel('Tỉnh', fontsize=12)
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        
        return fig, ax
    
    def save_chart(self, fig, filename: str):
        """Lưu chart vào charts/YYYYMMDD/filename để quản lý gọn gàng."""
        date_folder = pd.Timestamp.now().strftime('%Y%m%d')
        out_dir = os.path.join(self.output_dir, date_folder)
        os.makedirs(out_dir, exist_ok=True)
        filepath = os.path.join(out_dir, filename)
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"✅ Đã lưu chart: {filepath}")
        plt.close(fig)
        return filepath

