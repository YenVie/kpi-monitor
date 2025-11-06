"""
SCRIPT PHÂN TÍCH TỔNG QUÁT: Bất kỳ tỉnh nào và KPI nào
======================================================
Cho phép phân tích suy giảm cho bất kỳ tỉnh và KPI nào

Sử dụng Git để quản lý phiên bản code.
Version: 1.0

[TẠO THAY ĐỔI ĐỂ THỰC HÀNH GIT] - Bạn có thể xóa dòng này sau khi học xong
"""

import pandas as pd
import sys
from datetime import datetime
from typing import List
from kpi_decline_detection_pipeline import KPIDeclineDetector
from visualization_module import KPIVisualization

def _normalize_token(text: str) -> str:
    """Chuẩn hóa tên KPI để so khớp: bỏ khoảng trắng, dấu gạch, gạch dưới và viết hoa."""
    import re
    return re.sub(r"[^A-Z0-9]", "", str(text).upper())

def fuzzy_match_kpi(kpi_input: str, columns: list) -> tuple:
    """Trả về (matched_kpi, candidates)
    Ưu tiên: exact (case-insensitive) → exact-normalized → startswith → contains.
    Nếu có nhiều candidates, giữ nguyên danh sách để hiển thị cho người dùng.
    """
    if not kpi_input:
        return None, []
    k_in = str(kpi_input)
    cols = [str(c) for c in columns]
    up = k_in.upper()
    norm_in = _normalize_token(k_in)

    # 1) exact (case-insensitive)
    for c in cols:
        if up == str(c).upper():
            return c, [c]
    # 2) exact normalized (handle VN-CSSR vs VN_CSSR)
    exact_norm = [c for c in cols if _normalize_token(c) == norm_in]
    if len(exact_norm) == 1:
        return exact_norm[0], exact_norm
    if len(exact_norm) > 1:
        return exact_norm[0], exact_norm
    # 3) startswith
    starts = [c for c in cols if str(c).upper().startswith(up)]
    if len(starts) == 1:
        return starts[0], starts
    # 4) contains (ưu tiên chứa nguyên cụm VN nếu input có VN)
    cont = [c for c in cols if up in str(c).upper() or str(c).upper() in up]
    if len(cont) == 1:
        return cont[0], cont
    if len(cont) > 1:
        # Ưu tiên cột có token 'VN' nếu input có 'VN'
        if 'VN' in up:
            vn_first = [c for c in cont if 'VN' in str(c).upper()]
            if vn_first:
                return vn_first[0], cont
        # Ưu tiên tên dài hơn (thường cụ thể hơn)
        cont_sorted = sorted(cont, key=lambda x: len(str(x)), reverse=True)
        return cont_sorted[0], cont
    return None, []

def analyze_province_kpi(province_name: str, kpi_name: str, 
                         file_path: str = '1.Ngày.csv',
                         lookback_days: int = 7,
                         decline_threshold: float = 2.0,
                         start_date: str = None,
                         end_date: str = None):
    """
    Phân tích suy giảm KPI cho một tỉnh cụ thể
    
    Args:
        province_name: Tên tỉnh (ví dụ: 'Ninh thuan', 'Tp Ho Chi Minh')
        kpi_name: Tên KPI (ví dụ: 'HOSR_4G_2024', 'MTCL_2024', 'CSSR')
        file_path: Đường dẫn file CSV
        lookback_days: Số ngày gần nhất để so sánh (chỉ dùng nếu không có start_date/end_date)
        decline_threshold: Ngưỡng suy giảm (%)
        start_date: Ngày bắt đầu so sánh (format: 'DD/MM/YYYY' hoặc 'YYYY-MM-DD') - ưu tiên hơn lookback_days
        end_date: Ngày kết thúc so sánh (format: 'DD/MM/YYYY' hoặc 'YYYY-MM-DD') - ưu tiên hơn lookback_days
    """
    print("="*60)
    print(f"🔍 PHÂN TÍCH: {province_name} - {kpi_name}")
    print("="*60)
    
    # Step 1: Load data
    print("\n📖 Bước 1: Đang load dữ liệu...")
    detector = KPIDeclineDetector(file_path)
    df = detector.load_and_clean_data()
    
    # Step 2: Kiểm tra tỉnh có trong data không
    print(f"\n🔍 Bước 2: Kiểm tra tỉnh '{province_name}'...")
    all_provinces = df['CTKD7'].unique()
    all_provinces_clean = [p for p in all_provinces if pd.notna(p)]
    
    # Tìm tỉnh (case-insensitive, có thể viết tắt)
    matched_province = None
    for p in all_provinces_clean:
        if province_name.lower() in p.lower() or p.lower() in province_name.lower():
            matched_province = p
            break
    
    if matched_province is None:
        print(f"❌ Không tìm thấy tỉnh '{province_name}'!")
        print(f"\n📋 Danh sách tỉnh có trong file:")
        for i, p in enumerate(sorted(all_provinces_clean), 1):
            print(f"   {i}. {p}")
        return None
    
    print(f"✅ Tìm thấy: {matched_province}")
    province_data = df[df['CTKD7'] == matched_province].copy()
    print(f"   Số dòng dữ liệu: {len(province_data)}")
    
    # Step 3: Kiểm tra KPI có trong data không (tự động tìm gần đúng)
    print(f"\n🔍 Bước 3: Kiểm tra KPI '{kpi_name}'...")
    
    # Tìm KPI chính xác hoặc gần đúng (ưu tiên exact/normalized)
    matched_kpi, kpi_candidates = fuzzy_match_kpi(kpi_name, list(df.columns))
    
    if matched_kpi is None:
        print(f"❌ Không tìm thấy KPI '{kpi_name}'!")
        print(f"\n📋 Danh sách KPI có trong file (một phần):")
        kpi_cols = [c for c in df.columns if any(keyword in c.upper() 
                   for keyword in ['MTCL', 'CSSR', 'CDR', 'HOSR', 'ERAB', 'DATA', 'VN', 'QOS', 'SR', 'DR'])]
        for i, kpi in enumerate(sorted(kpi_cols)[:30], 1):
            print(f"   {i}. {kpi}")
        print(f"\n💡 Tip: Bạn có thể nhập một phần tên KPI, ví dụ: 'HOSR' sẽ tìm 'HOSR_4G_2024'")
        return None
    
    if matched_kpi != kpi_name:
        print(f"⚠️  Không tìm thấy '{kpi_name}', dùng KPI khớp tốt nhất: '{matched_kpi}'")
        if len(kpi_candidates) > 1:
            print("   Ứng viên khác:")
            for c in kpi_candidates[:10]:
                if c != matched_kpi:
                    print(f"   - {c}")
    else:
        print(f"✅ Tìm thấy KPI: {matched_kpi}")
    
    kpi_name = matched_kpi  # Cập nhật để dùng tên chính xác
    
    # Step 4: Phân tích suy giảm
    print(f"\n🔍 Bước 4: Phân tích suy giảm...")
    alerts = detector.detect_declines(kpi_name, lookback_days=lookback_days)
    
    # Lọc alerts cho tỉnh này
    province_alerts = [a for a in alerts if a['province'] == matched_province]
    
    if province_alerts:
        print(f"\n⚠️  PHÁT HIỆN SUY GIẢM!")
        for alert in province_alerts:
            print(f"\n   Tỉnh: {alert['province']}")
            print(f"   KPI: {alert['kpi']}")
            print(f"   Ngày: {alert['latest_date'].strftime('%d/%m/%Y')}")
            print(f"   Giá trị hiện tại: {alert['latest_value']:.2f}")
            print(f"   Giá trị trước ({alert['days_lookback']} ngày): {alert['compare_value']:.2f}")
            print(f"   Suy giảm: {alert['decline_pct']:.2f}%")
            print(f"   Mức độ: {alert['severity']}")
    else:
        print(f"\n✅ Không phát hiện suy giảm mạnh cho {matched_province}")
        print(f"   (có thể suy giảm < {decline_threshold}% hoặc không có dữ liệu đủ)")
    
    # Step 5: Tạo trend chart với lookback_days hoặc ngày cụ thể
    if start_date and end_date:
        print(f"\n📈 Bước 5: Tạo trend chart (highlight từ {start_date} đến {end_date})...")
    else:
        print(f"\n📈 Bước 5: Tạo trend chart (so sánh {lookback_days} ngày gần nhất)...")
    try:
        # Cập nhật config để dùng lookback_days đúng (nếu không có ngày cụ thể)
        if not start_date or not end_date:
            detector.config['days_lookback'] = lookback_days
        
        chart_path = detector.create_trend_charts(
            kpi_name,
            provinces=[matched_province],
            lookback_days=lookback_days if not start_date or not end_date else None,
            start_date=start_date,
            end_date=end_date
        )
        print(f"✅ Đã tạo chart: {chart_path}")
        if start_date and end_date:
            print(f"   Chart highlight khoảng: {start_date} - {end_date}")
        else:
            print(f"   Chart highlight {lookback_days} ngày gần nhất")
    except Exception as e:
        print(f"⚠️  Lỗi khi tạo chart: {str(e)}")
    
    # Step 6: Thống kê
    print(f"\n📊 Bước 6: Thống kê {kpi_name} của {matched_province}...")
    # QUAN TRỌNG: Bỏ qua các ngày có KPI = 0 hoặc null khi tính thống kê
    province_kpi_data = province_data[['Ngay7', kpi_name]].copy()
    province_kpi_data = province_kpi_data.sort_values('Ngay7')
    province_kpi_data = province_kpi_data[
        (province_kpi_data[kpi_name].notna()) & 
        (province_kpi_data[kpi_name] != 0)  # Bỏ qua ngày có KPI = 0
    ]
    
    if len(province_kpi_data) > 0:
        stats = {
            'Min': province_kpi_data[kpi_name].min(),
            'Max': province_kpi_data[kpi_name].max(),
            'Mean': province_kpi_data[kpi_name].mean(),
            'Latest': province_kpi_data[kpi_name].iloc[-1],
            'First': province_kpi_data[kpi_name].iloc[0],
            'Count': len(province_kpi_data)
        }
        
        print(f"\n   Số điểm dữ liệu: {stats['Count']}")
        print(f"   Min: {stats['Min']:.2f}")
        print(f"   Max: {stats['Max']:.2f}")
        print(f"   Mean: {stats['Mean']:.2f}")
        print(f"   First (đầu): {stats['First']:.2f}")
        print(f"   Latest (cuối): {stats['Latest']:.2f}")
        
        total_change = ((stats['Latest'] - stats['First']) / stats['First']) * 100
        print(f"   Thay đổi tổng: {total_change:.2f}%")
    
    print("\n" + "="*60)
    print("✅ Phân tích hoàn thành!")
    print("="*60)
    
    return detector, province_alerts, matched_province


def analyze_all_provinces_for_kpi(kpi_name: str, 
                                  file_path: str = '1.Ngày.csv',
                                  lookback_days: int = 7,
                                  start_date: str = None,
                                  end_date: str = None):
    """
    Phân tích một KPI cho tất cả các tỉnh
    """
    print("="*60)
    print(f"🔍 PHÂN TÍCH TẤT CẢ TỈNH - KPI: {kpi_name}")
    print("="*60)
    
    detector = KPIDeclineDetector(file_path)
    df = detector.load_and_clean_data()
    
    # Tìm KPI chính xác hoặc gần đúng (ưu tiên exact/normalized)
    matched_kpi, kpi_candidates = fuzzy_match_kpi(kpi_name, list(df.columns))
    
    if matched_kpi is None:
        print(f"❌ Không tìm thấy KPI '{kpi_name}'!")
        print(f"\n📋 Danh sách KPI có trong file (một phần):")
        kpi_cols = [c for c in df.columns if any(keyword in c.upper() 
                   for keyword in ['MTCL', 'CSSR', 'CDR', 'HOSR', 'ERAB', 'DATA', 'VN', 'QOS', 'SR', 'DR'])]
        for i, kpi in enumerate(sorted(kpi_cols)[:30], 1):
            print(f"   {i}. {kpi}")
        return []
    
    if matched_kpi != kpi_name:
        print(f"⚠️  Không tìm thấy '{kpi_name}', dùng KPI khớp tốt nhất: '{matched_kpi}'")
        if len(kpi_candidates) > 1:
            print("   Ứng viên khác:")
            for c in kpi_candidates[:10]:
                if c != matched_kpi:
                    print(f"   - {c}")
    
    # Phát hiện suy giảm cho tất cả tỉnh
    alerts = detector.detect_declines(matched_kpi, lookback_days=lookback_days)
    
    if alerts:
        print(f"\n⚠️  Phát hiện {len(alerts)} tỉnh có suy giảm {matched_kpi}:")
        print("\n" + "-"*60)
        for i, alert in enumerate(alerts, 1):
            print(f"{i}. {alert['province']}: {alert['decline_pct']:.2f}% ({alert['severity']})")
        
        # Tạo chart cho tất cả tỉnh có vấn đề
        provinces_with_issues = [a['province'] for a in alerts]
        detector.create_trend_charts(matched_kpi, provinces=provinces_with_issues, 
                                     lookback_days=lookback_days if not start_date or not end_date else None,
                                     start_date=start_date,
                                     end_date=end_date)
    else:
        print("\n✅ Không phát hiện suy giảm nào")
    
    return alerts


def interactive_menu():
    """
    Menu tương tác để chọn tỉnh và KPI
    """
    print("="*60)
    print("📊 MENU PHÂN TÍCH KPI")
    print("="*60)
    print("\n1. Biểu đồ tương tác: Một tỉnh + một KPI (click để loại ngày)")
    print("2. Biểu đồ tương tác: Một KPI cho tất cả tỉnh (click để loại ngày)")
    print("3. Phân tích tất cả KPI quan trọng (pipeline đầy đủ)")
    print("0. Thoát")
    
    choice = input("\nChọn chức năng (0-3): ").strip()
    
    if choice == '1':
        province = input("Nhập tên tỉnh: ").strip()
        kpi = input("Nhập tên KPI: ").strip()
        print("\n➡️  Cửa sổ biểu đồ sẽ mở.\n - Click vào điểm để chọn/bỏ một ngày\n - Nhấn r để vẽ lại theo ngày đã chọn\n - Nhấn s để lưu chart và đóng\n - Nhấn q để thoát")
        # Mở trực tiếp chế độ tương tác, có fuzzy matching
        local_file = '1.Ngày.csv'
        detector = KPIDeclineDetector(local_file)
        df_int = detector.load_and_clean_data()
        # Fuzzy match KPI
        matched_kpi = kpi
        if matched_kpi not in df_int.columns:
            kup = kpi.upper()
            for col in df_int.columns:
                if kup in str(col).upper() or str(col).upper() in kup:
                    matched_kpi = col
                    break
        # Fuzzy match province
        matched_prov = None
        for p in df_int['CTKD7'].dropna().unique():
            if province.lower() in str(p).lower() or str(p).lower() in province.lower():
                matched_prov = p
                break
        prov_list = [matched_prov] if matched_prov else None
        detector.create_trend_charts_interactive(
            matched_kpi,
            provinces=prov_list,
            exclude_dates=None,
            date_range_filter=None
        )
        
    elif choice == '2':
        kpi = input("Nhập tên KPI: ").strip()
        print("\n➡️  Cửa sổ biểu đồ sẽ mở.\n - Click vào điểm để chọn/bỏ một ngày\n - Nhấn r để vẽ lại theo ngày đã chọn\n - Nhấn s để lưu chart và đóng\n - Nhấn q để thoát")
        local_file = '1.Ngày.csv'
        detector = KPIDeclineDetector(local_file)
        df_int = detector.load_and_clean_data()
        # Fuzzy match KPI
        matched_kpi = kpi
        if matched_kpi not in df_int.columns:
            kup = kpi.upper()
            for col in df_int.columns:
                if kup in str(col).upper() or str(col).upper() in kup:
                    matched_kpi = col
                    break
        # Lấy danh sách tỉnh có vấn đề (nếu có) để tập trung
        alerts = detector.detect_declines(matched_kpi, lookback_days=7)
        provinces_with_issues = [a['province'] for a in alerts] if alerts else None
        detector.create_trend_charts_interactive(
            matched_kpi,
            provinces=provinces_with_issues,
            exclude_dates=None,
            date_range_filter=None
        )
        
    elif choice == '3':
        from kpi_decline_detection_pipeline import main
        main()
        
    elif choice == '0':
        print("Tạm biệt!")
    else:
        print("Lựa chọn không hợp lệ!")


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        # Chạy từ command line: python analyze_any_province_kpi.py <tỉnh> <KPI>
        province = sys.argv[1]
        kpi = sys.argv[2]
        lookback = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        
        analyze_province_kpi(province, kpi, lookback_days=lookback)
    else:
        # Chạy menu tương tác
        interactive_menu()

