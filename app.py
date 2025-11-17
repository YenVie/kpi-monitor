"""
STREAMLIT WEB APP - GIÁM SÁT KPI
=================================
Chạy trên laptop local, không cần server riêng!

Cách chạy:
1. Cài đặt: pip install streamlit
2. Chạy: streamlit run app.py
3. Mở trình duyệt: http://localhost:8501
"""

import streamlit as st
import pandas as pd
import sys
import os
import glob
import shutil
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
import unicodedata
from matplotlib.dates import DayLocator, DateFormatter
from matplotlib.ticker import MaxNLocator, FuncFormatter
matplotlib.use('Agg')  # Backend cho Streamlit

# ==== Tiện ích đọc/ghi và gộp dữ liệu (không ảnh hưởng flow hiện tại) ====
CSV_ENCODINGS = ['utf-8-sig', 'utf-8', 'cp1258', 'latin1']
DATA_FILE_PATH = '1.Ngày.csv'

def _read_csv_any(path: str) -> pd.DataFrame:
    last_err = None
    for enc in CSV_ENCODINGS:
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Không đọc được CSV: {path} ({last_err})")

def _normalize_text(s: str) -> str:
    if s is None:
        return ''
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    return s.upper().strip()

def format_dates_for_display(df: pd.DataFrame, date_cols=('Ngay7',)) -> pd.DataFrame:
    """
    Trả về bản sao DataFrame với các cột ngày được format DD/MM/YYYY để hiển thị (không ảnh hưởng dữ liệu gốc).
    """
    df_display = df.copy()
    for col in date_cols:
        if col in df_display.columns:
            series = pd.to_datetime(df_display[col], errors='coerce', dayfirst=True)
            df_display[col] = series.dt.strftime('%d/%m/%Y')
    return df_display

def merge_into_current(old_path: str, new_path: str) -> dict:
    """Gộp new_path vào old_path theo khóa (Ngay7 + CTKD7), cập nhật trùng, giữ thứ tự và đánh lại STT."""
    if not os.path.exists(old_path):
        df_new = _read_csv_any(new_path)
        df_new.to_csv(old_path, index=False, encoding='utf-8-sig')
        return {"rows_old": 0, "rows_new": len(df_new), "rows_added": len(df_new), "rows_updated": 0, "total_rows": len(df_new)}

    df_old = _read_csv_any(old_path)
    df_new = _read_csv_any(new_path)

    # Chuẩn hóa tên cột
    df_old.columns = [str(c).strip() for c in df_old.columns]
    df_new.columns = [str(c).strip() for c in df_new.columns]

    required = ['Ngay7', 'CTKD7']
    for col in required:
        if col not in df_old.columns or col not in df_new.columns:
            raise ValueError(f"Thiếu cột bắt buộc '{col}' trong file cần gộp.")

    # Chuẩn hóa ngày và khóa gộp
    def _prep(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['Ngay7_parsed'] = pd.to_datetime(df['Ngay7'], format='%d/%m/%Y', errors='coerce')
        if df['Ngay7_parsed'].isna().all():
            df['Ngay7_parsed'] = pd.to_datetime(df['Ngay7'], dayfirst=True, errors='coerce')
        df['_key'] = df['Ngay7_parsed'].dt.strftime('%Y-%m-%d') + '||' + df['CTKD7'].astype(str).str.strip().str.upper()
        return df

    df_old_p = _prep(df_old)
    df_new_p = _prep(df_new)

    # Xử lý duplicate _key trong cùng file (giữ lại dòng cuối cùng nếu có duplicate)
    # Điều này tránh lỗi "cannot reindex on an axis with duplicate labels"
    if df_old_p['_key'].duplicated().any():
        df_old_p = df_old_p.drop_duplicates(subset='_key', keep='last')
    
    if df_new_p['_key'].duplicated().any():
        df_new_p = df_new_p.drop_duplicates(subset='_key', keep='last')

    old_idx = df_old_p.set_index('_key')
    new_idx = df_new_p.set_index('_key')

    matching = old_idx.index.intersection(new_idx.index)
    new_only = new_idx.index.difference(old_idx.index)

    rows_updated = len(matching)
    if rows_updated > 0:
        # Cập nhật các dòng trùng: chỉ update các cột có trong file mới, giữ lại các cột cũ
        old_idx.update(new_idx.loc[matching])
    
    # Lấy lại dữ liệu cũ đã được cập nhật (bao gồm cả các dòng không trùng)
    df_old_u = old_idx.reset_index()
    
    # Lấy các dòng mới (chỉ những dòng không có trong file cũ)
    df_new_only = new_idx.loc[new_only].reset_index()

    # Đảm bảo tất cả các cột từ cả hai file đều có trong kết quả
    # Lấy union của tất cả các cột (loại bỏ các cột phụ trợ tạm thời)
    temp_cols = ['Ngay7_parsed', '_key']
    all_columns = [c for c in df_old_u.columns if c not in temp_cols] + \
                  [c for c in df_new_only.columns if c not in temp_cols and c not in df_old_u.columns]
    
    # Đảm bảo cả hai DataFrame có cùng các cột (thêm NaN cho cột thiếu)
    for col in all_columns:
        if col not in df_old_u.columns:
            df_old_u[col] = None
        if col not in df_new_only.columns:
            df_new_only[col] = None
    
    # Sắp xếp lại cột theo thứ tự ban đầu của file cũ, sau đó thêm các cột mới
    old_cols_order = [c for c in df_old.columns if c in all_columns]
    new_cols = [c for c in all_columns if c not in old_cols_order]
    final_cols_order = old_cols_order + new_cols
    
    # Chỉ lấy các cột cần thiết (loại bỏ cột phụ trợ)
    df_old_u_clean = df_old_u[[c for c in all_columns if c in df_old_u.columns]]
    df_new_only_clean = df_new_only[[c for c in all_columns if c in df_new_only.columns]]

    # Hợp nhất, giữ thứ tự: cũ trước, mới thêm nối sau
    df_merged = pd.concat([df_old_u_clean, df_new_only_clean], ignore_index=True, sort=False)

    # Sắp xếp lại cột theo thứ tự đã định
    df_merged = df_merged[final_cols_order]

    # Làm sạch cột phụ trợ trước khi sắp xếp
    for col in ['Ngay7_parsed', '_key']:
        if col in df_merged.columns:
            df_merged = df_merged.drop(columns=[col])

    # Sắp xếp lại theo ngày (tăng dần) để đảm bảo thứ tự đúng
    if 'Ngay7' in df_merged.columns:
        # Chuyển đổi ngày về datetime để sắp xếp
        df_merged['Ngay7_temp'] = pd.to_datetime(df_merged['Ngay7'], format='%d/%m/%Y', errors='coerce', dayfirst=True)
        # Sắp xếp theo ngày tăng dần, sau đó theo CTKD7 nếu có
        if 'CTKD7' in df_merged.columns:
            df_merged = df_merged.sort_values(['Ngay7_temp', 'CTKD7'], na_position='last')
        else:
            df_merged = df_merged.sort_values('Ngay7_temp', na_position='last')
        # Xóa cột tạm và reset index sau khi sắp xếp
        df_merged = df_merged.drop(columns=['Ngay7_temp'])
        df_merged = df_merged.reset_index(drop=True)

    # Đánh lại STT nếu có cột liên quan (sau khi đã sắp xếp)
    stt_candidates = [c for c in df_merged.columns if any(k in _normalize_text(c) for k in ['STT', 'SO THU TU', 'TEXTBOX164', 'TEXTBOX'])]
    if stt_candidates:
        stt_col = stt_candidates[0]
        df_merged[stt_col] = range(1, len(df_merged) + 1)

    # Chuẩn lại định dạng ngày (sau khi sắp xếp)
    if 'Ngay7' in df_merged.columns:
        df_merged['Ngay7'] = pd.to_datetime(df_merged['Ngay7'], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')

    df_merged.to_csv(old_path, index=False, encoding='utf-8-sig')
    return {
        "rows_old": len(df_old),
        "rows_new": len(df_new),
        "rows_added": len(df_new_only),
        "rows_updated": rows_updated,
        "total_rows": len(df_merged),
    }

# Import các module hiện có
try:
    from kpi_decline_detection_pipeline import KPIDeclineDetector
    from analyze_any_province_kpi import analyze_province_kpi, fuzzy_match_kpi
except ImportError as e:
    st.error(f"❌ Lỗi import: {e}")
    st.stop()

# Cấu hình trang
st.set_page_config(
    page_title="Giám sát KPI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">📊 HỆ THỐNG GIÁM SÁT KPI</div>', unsafe_allow_html=True)

# Sidebar: Upload file và cấu hình
st.sidebar.header("📁 Cấu hình")

# Upload file CSV
uploaded_file = st.sidebar.file_uploader(
    "Chọn file CSV dữ liệu KPI",
    type=['csv'],
    help="Upload file CSV chứa dữ liệu KPI",
    key="csv_uploader"
)

# Tùy chọn gộp nhanh (không ảnh hưởng flow upload hiện tại)
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Gộp dữ liệu mới vào file hiện tại")
append_file = st.sidebar.file_uploader(
    "Chọn file CSV cần gộp",
    type=['csv'],
    help="Chọn file ngày mới để gộp thẳng vào 1.Ngày.csv",
    key="csv_append_uploader"
)
do_merge = st.sidebar.button("Gộp vào file hiện tại", help="Gộp file vừa chọn vào dữ liệu đang dùng")

# Khởi tạo detector với cache nhưng có thể clear (ĐỊNH NGHĨA TRƯỚC)
@st.cache_data(ttl=3600)  # Cache 1 giờ, nhưng có thể clear bằng button
def load_data(file_path):
    """Load và cache dữ liệu"""
    detector = KPIDeclineDetector(file_path)
    df = detector.load_and_clean_data()
    
    # Hiển thị thông tin dữ liệu
    date_col = 'Ngay7'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], format='%d/%m/%Y', errors='coerce')
        min_date = df[date_col].min()
        max_date = df[date_col].max()
        st.sidebar.info(f"📅 Khoảng thời gian: {min_date.strftime('%d/%m/%Y')} - {max_date.strftime('%d/%m/%Y')}")
    
    return detector, df

# Lưu file path và hash để detect thay đổi
file_path = None
file_changed = False

# Nếu bấm nút gộp
if do_merge and append_file is not None:
    try:
        tmp_path = f"__tmp_merge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(tmp_path, 'wb') as ftmp:
            ftmp.write(append_file.getbuffer())
        # Tìm file đích: ưu tiên DATA_FILE_PATH, nếu không có thì tìm file "1.Ngày*.csv"
        target_path = None
        if os.path.exists(DATA_FILE_PATH):
            target_path = DATA_FILE_PATH
        else:
            # Tìm file có tên bắt đầu bằng "1.Ngày" và kết thúc bằng ".csv"
            matching_files = glob.glob('1.Ngày*.csv')
            if matching_files:
                # Ưu tiên file "1.Ngày.csv", sau đó là file mới nhất
                if '1.Ngày.csv' in matching_files:
                    target_path = '1.Ngày.csv'
                else:
                    # Chọn file mới nhất dựa trên thời gian sửa đổi
                    target_path = max(matching_files, key=os.path.getmtime)
            else:
                target_path = '1.Ngày.csv'
        
        # Kiểm tra và thông báo file đích
        if not os.path.exists(target_path):
            st.sidebar.warning(f"⚠️ File đích '{target_path}' chưa tồn tại. File mới sẽ được tạo.")
        else:
            # Đọc file cũ để kiểm tra số dòng
            try:
                df_check = _read_csv_any(target_path)
                st.sidebar.info(f"📄 Đang gộp vào file: {target_path} (có {len(df_check):,} dòng)")
            except:
                pass
        
        stats = merge_into_current(target_path, tmp_path)
        os.remove(tmp_path)
        load_data.clear()
        st.sidebar.success("✅ Đã gộp dữ liệu mới vào file hiện tại!")
        st.sidebar.info(
            f"""📊 Thống kê gộp:
- Dòng cũ: {stats['rows_old']:,}
- Dòng mới: {stats['rows_new']:,}
- Cập nhật: {stats['rows_updated']:,}
- Thêm mới: {stats['rows_added']:,}
- Tổng sau gộp: {stats['total_rows']:,}"""
        )
        file_path = target_path
    except Exception as e:
        st.sidebar.error(f"❌ Lỗi khi gộp: {e}")
        import traceback
        st.sidebar.error(traceback.format_exc())

elif uploaded_file is not None:
    # Tìm file đích: ưu tiên DATA_FILE_PATH, nếu không có thì tìm file "1.Ngày*.csv"
    target_path = None
    if os.path.exists(DATA_FILE_PATH):
        target_path = DATA_FILE_PATH
    else:
        # Tìm file có tên bắt đầu bằng "1.Ngày" và kết thúc bằng ".csv"
        matching_files = glob.glob('1.Ngày*.csv')
        if matching_files:
            # Ưu tiên file "1.Ngày.csv", sau đó là file mới nhất
            if '1.Ngày.csv' in matching_files:
                target_path = '1.Ngày.csv'
            else:
                # Chọn file mới nhất dựa trên thời gian sửa đổi
                target_path = max(matching_files, key=os.path.getmtime)
        else:
            target_path = '1.Ngày.csv'
    
    file_path = target_path
    
    try:
        # Lưu file upload tạm thời
        tmp_path = f"__tmp_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(tmp_path, 'wb') as ftmp:
            ftmp.write(uploaded_file.getbuffer())
    
        # Kiểm tra file đích
        if not os.path.exists(target_path):
            # Nếu file đích chưa tồn tại, chỉ cần copy file upload
            shutil.copy2(tmp_path, target_path)
            total_rows_old = 0
            total_rows_new = len(_read_csv_any(tmp_path))
            stats = {
                "rows_old": 0,
                "rows_new": total_rows_new,
                "rows_added": total_rows_new,
                "rows_updated": 0,
                "total_rows": total_rows_new
            }
        else:
            # Đọc file cũ để kiểm tra số dòng
            try:
                df_check = _read_csv_any(target_path)
                total_rows_old = len(df_check)
                st.sidebar.info(f"📄 File hiện tại có {total_rows_old:,} dòng, đang gộp dữ liệu mới...")
            except:
                total_rows_old = 0
            
            # 🔄 GỘP DỮ LIỆU thay vì thay thế
            stats = merge_into_current(target_path, tmp_path)
            total_rows_new = stats['rows_new']
        
        # Dọn dẹp file tạm
        os.remove(tmp_path)
        
        # Clear cache
        load_data.clear()
        
        st.sidebar.success(f"✅ Đã gộp dữ liệu mới vào file! ({uploaded_file.size:,} bytes)")
        st.sidebar.info(f"📄 Tên file: {uploaded_file.name}")
        st.sidebar.info(
            f"""📊 Thống kê gộp:
- Dòng cũ: {stats['rows_old']:,}
- Dòng mới: {stats['rows_new']:,}
- Cập nhật: {stats['rows_updated']:,}
- Thêm mới: {stats['rows_added']:,}
- Tổng sau gộp: {stats['total_rows']:,}"""
        )
    except Exception as e:
        st.sidebar.error(f"❌ Lỗi khi upload file: {e}")
        import traceback
        st.sidebar.error(traceback.format_exc())
elif os.path.exists('1.Ngày.csv'):
    file_path = '1.Ngày.csv'
    file_size = os.path.getsize(file_path)
    st.sidebar.success(f"✅ Đang sử dụng file: 1.Ngày.csv ({file_size:,} bytes)")
else:
    st.sidebar.warning("⚠️ Chưa có file CSV. Vui lòng upload file.")
    st.stop()

# Cấu hình
st.sidebar.subheader("⚙️ Cấu hình phân tích")
lookback_days = st.sidebar.slider("Số ngày so sánh", 1, 30, 7)
decline_threshold = st.sidebar.slider("Ngưỡng suy giảm (%)", 0.1, 10.0, 2.0, 0.1)

# Nút reload data
if st.sidebar.button("🔄 Reload dữ liệu", help="Tải lại dữ liệu từ file CSV"):
    load_data.clear()
    st.sidebar.success("✅ Đã reload dữ liệu!")
    st.rerun()

try:
    detector, df = load_data(file_path)
    
    # Hiển thị thông tin dữ liệu đã load
    st.sidebar.info(f"📊 Số dòng: {len(df):,} | Số tỉnh: {len(df['CTKD7'].dropna().unique())}")
    
except Exception as e:
    st.error(f"❌ Lỗi khi load dữ liệu: {str(e)}")
    st.exception(e)
    st.stop()

# Tab chính
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview", 
    "🔍 Phân tích tỉnh", 
    "📈 Tất cả tỉnh", 
    "🚨 Alerts"
])

# TAB 1: OVERVIEW
with tab1:
    st.header("📊 Tổng quan dữ liệu")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Số tỉnh", len(df['CTKD7'].unique()))
    
    with col2:
        st.metric("Số điểm dữ liệu", len(df))
    
    with col3:
        date_range = pd.to_datetime(df['Ngay7']).max() - pd.to_datetime(df['Ngay7']).min()
        st.metric("Khoảng thời gian", f"{date_range.days} ngày")
    
    with col4:
        # Đếm số KPI (bao gồm các KPI mới: vùng phủ & sự cố)
        kpi_cols = [c for c in df.columns if any(k in c.upper() 
                   for k in ['MTCL', 'CSSR', 'CDR', 'HOSR', 'ERAB', 'DATA', 'VN', 'QOS', 'SR', 'DR', 'COVERAGE', 'CHATLUONG', 'SUCO', 'SU_CO'])]
        st.metric("Số KPI", len(kpi_cols))
    
    # Hiển thị dữ liệu với phân trang
    st.subheader("📋 Xem dữ liệu")
    
    # Tùy chọn hiển thị
    col_view1, col_view2 = st.columns(2)
    
    with col_view1:
        show_all = st.checkbox("Hiển thị toàn bộ dữ liệu", value=False, help="Bỏ chọn để xem từng trang")
    
    with col_view2:
        if not show_all:
            rows_per_page = st.selectbox(
                "Số dòng mỗi trang",
                options=[10, 25, 50, 100, 200],
                index=0,
                help="Chọn số dòng hiển thị mỗi trang"
            )
        else:
            rows_per_page = len(df)
    
    # Phân trang
    if not show_all and rows_per_page < len(df):
        total_rows = len(df)
        total_pages = (total_rows + rows_per_page - 1) // rows_per_page
        
        # Session state để lưu trang hiện tại
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1
        
        # Hiển thị dữ liệu theo trang
        start_idx = (st.session_state.current_page - 1) * rows_per_page
        end_idx = start_idx + rows_per_page
        page_data = df.iloc[start_idx:end_idx]
        
        # Hiển thị bảng trước
        page_data_display = format_dates_for_display(page_data)
        st.dataframe(page_data_display, use_container_width=True, height=400)
        
        # Điều hướng trang (di chuyển xuống dưới bảng)
        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
        
        with col_nav1:
            if st.button("⏮️ Trang đầu", use_container_width=True):
                st.session_state.current_page = 1
                st.rerun()
            if st.button("◀️ Trang trước", use_container_width=True):
                if st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    st.rerun()
        
        with col_nav2:
            current_page = st.session_state.current_page
            st.info(f"📄 Trang {current_page} / {total_pages} | Dòng {(current_page-1)*rows_per_page + 1} - {min(current_page*rows_per_page, total_rows)} / {total_rows}")
        
        with col_nav3:
            if st.button("▶️ Trang sau", use_container_width=True):
                if st.session_state.current_page < total_pages:
                    st.session_state.current_page += 1
                    st.rerun()
            if st.button("⏭️ Trang cuối", use_container_width=True):
                st.session_state.current_page = total_pages
                st.rerun()
    else:
        # Hiển thị toàn bộ dữ liệu
        df_display = format_dates_for_display(df)
        st.dataframe(df_display, use_container_width=True, height=600)

# TAB 2: PHÂN TÍCH TỈNH
with tab2:
    st.header("🔍 Phân tích theo tỉnh và KPI")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Dropdown chọn tỉnh
        provinces = sorted([p for p in df['CTKD7'].dropna().unique()])
        province = st.selectbox(
            "Chọn tỉnh",
            provinces,
            help="Chọn tỉnh cần phân tích"
        )
        
        # Tìm kiếm tỉnh
        search_province = st.text_input("🔍 Tìm kiếm tỉnh (nhập một phần tên)")
        if search_province:
            filtered_provinces = [p for p in provinces if search_province.lower() in str(p).lower()]
            if filtered_provinces:
                province = st.selectbox("Tỉnh tìm thấy", filtered_provinces)
    
    with col2:
        # Dropdown chọn KPI (hiển thị tên thân thiện)
        def _norm(s: str) -> str:
            s = unicodedata.normalize('NFD', str(s))
            s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
            s = s.upper().replace(' ', '').replace('-', '').replace('.', '').replace('_', '_')
            return s
        tokens = ['MTCL', 'CSSR', 'CDR', 'HOSR', 'ERAB', 'DATA', 'VN', 'QOS', 'SR', 'DR', 'COVERAGE', 'CHATLUONG', 'SUCO', 'SU_CO', 'SCL', 'SCNT1', 'SCRNT']
        kpi_cols_raw = [c for c in df.columns if any(t in _norm(c) for t in tokens)]
        # Map tên hiển thị thân thiện
        alias_display_map = {
            'ID4G_USR_DL_THP': '4G_USR_DL_THP',  # hiển thị đẹp
        }
        # Thêm alias hiển thị cho các cột sự cố nếu tên gốc là tiếng Việt có dấu
        for c in df.columns:
            cn = _norm(c)
            if 'SUCOLON' == cn or cn == 'SCL':
                alias_display_map[c] = 'SuCoLon'
            elif 'SUCONGHIEMTRONG' == cn or cn == 'SCNT1':
                alias_display_map[c] = 'SuCoNghiemTrong'
            elif 'SUCORATNGHIEMTRONG' == cn or cn == 'SCRNT':
                alias_display_map[c] = 'SuCoRatNghiemTrong'
            elif 'COVERAGE4G' == cn or 'CHATLUONGVUNGPHU' == cn:
                alias_display_map[c] = 'ChatLuongVungPhu'
        kpi_display_options = [alias_display_map.get(c, c) for c in kpi_cols_raw]
        selected_kpi_display = st.selectbox(
            "Chọn KPI",
            kpi_display_options,
            help="Chọn KPI cần phân tích"
        )
        # Map ngược về tên cột thực tế
        if selected_kpi_display == '4G_USR_DL_THP':
            if '4G_USR_DL_THP' in df.columns:
                kpi = '4G_USR_DL_THP'
            else:
                kpi = 'ID4G_USR_DL_THP'
        else:
            # Tìm ngược theo alias nếu là sự cố hoặc vùng phủ
            reverse_map = {v: k for k, v in alias_display_map.items()}
            if selected_kpi_display in reverse_map:
                kpi = reverse_map[selected_kpi_display]
            else:
                kpi = selected_kpi_display
        
        # Tìm kiếm KPI
        search_kpi = st.text_input("🔍 Tìm kiếm KPI (nhập một phần tên)")
        if search_kpi:
            matched_kpi, candidates = fuzzy_match_kpi(search_kpi, df.columns)
            if matched_kpi:
                kpi = st.selectbox("KPI tìm thấy", [matched_kpi] + candidates[:5])
    
    # Lọc ngày - Tính năng loại bỏ ngày bị lỗi (giống như tab "Tất cả tỉnh")
    st.subheader("🔧 Lọc ngày")
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        # Lấy danh sách ngày có dữ liệu (chuẩn hóa theo datetime để sắp xếp đúng)
        all_dates_dt = pd.to_datetime(df['Ngay7'], format='%d/%m/%Y', errors='coerce').dropna()
        all_dates_dt = all_dates_dt.sort_values().unique()
        all_dates = [d.strftime('%d/%m/%Y') for d in all_dates_dt]
        all_dates_str = all_dates
        
        # Multi-select để chọn ngày cần loại bỏ
        excluded_dates_province = st.multiselect(
            "❌ Chọn ngày cần loại bỏ (ngày bị lỗi)",
            options=all_dates_str,
            help="Chọn các ngày có dữ liệu lỗi để loại bỏ khỏi biểu đồ",
            default=[],
            key="exclude_dates_province"
        )
    
    with col_filter2:
        # Chọn khoảng ngày để hiển thị (giống như tab "Tất cả tỉnh")
        if len(all_dates) > 0:
            # Convert dates for date_input
            try:
                date_min_prov = pd.to_datetime(all_dates[0], format='%d/%m/%Y', errors='coerce')
                date_max_prov = pd.to_datetime(all_dates[-1], format='%d/%m/%Y', errors='coerce')
                
                if pd.notna(date_min_prov) and pd.notna(date_max_prov):
                    date_range_province = st.date_input(
                        "📅 Chọn khoảng ngày hiển thị",
                        value=(date_min_prov.date(), date_max_prov.date()),
                        min_value=date_min_prov.date(),
                        max_value=date_max_prov.date(),
                        help="Chọn khoảng ngày muốn xem trong biểu đồ",
                        key="date_range_province"
                    )
                else:
                    date_range_province = None
            except:
                date_range_province = None
        else:
            date_range_province = None
    
    # Hiển thị biểu đồ ngay khi chọn tỉnh và KPI
    if province and kpi:
        province_data = df[df['CTKD7'] == province].copy()
        if len(province_data) > 0 and kpi in province_data.columns:
            kpi_data = province_data[['Ngay7', kpi]].copy()
            kpi_data = kpi_data[(kpi_data[kpi].notna()) & (kpi_data[kpi] != 0)]
            
            # Loại bỏ ngày được chọn
            if excluded_dates_province:
                kpi_data = kpi_data[~kpi_data['Ngay7'].isin(excluded_dates_province)]
            
            # Lọc theo khoảng ngày nếu có
            if date_range_province and len(date_range_province) == 2:
                kpi_data['Ngay7_dt'] = pd.to_datetime(kpi_data['Ngay7'], format='%d/%m/%Y', errors='coerce')
                start_date_prov = pd.Timestamp(date_range_province[0])
                end_date_prov = pd.Timestamp(date_range_province[1])
                kpi_data = kpi_data[
                    (kpi_data['Ngay7_dt'] >= start_date_prov) & 
                    (kpi_data['Ngay7_dt'] <= end_date_prov)
                ]
                kpi_data = kpi_data.drop('Ngay7_dt', axis=1)
            
            if len(kpi_data) > 0:
                st.subheader("📈 Biểu đồ xu hướng")
                kpi_data['Ngay7'] = pd.to_datetime(kpi_data['Ngay7'], format='%d/%m/%Y', errors='coerce')
                kpi_data = kpi_data.sort_values('Ngay7')
                
                # Biểu đồ tương tác Streamlit (giữ định dạng YYYY-MM-DD như trước)
                kpi_data_display = kpi_data.copy()
                kpi_data_display['Ngay7'] = kpi_data_display['Ngay7'].dt.strftime('%Y-%m-%d')
                chart_data = kpi_data_display.set_index('Ngay7')[kpi].to_frame()
                chart_data.columns = [f'{kpi} - {province}']
                st.line_chart(chart_data)
                
                # Thông báo nếu có ngày bị loại bỏ
                if excluded_dates_province:
                    st.info(f"⚠️ Đã loại bỏ {len(excluded_dates_province)} ngày: {', '.join(excluded_dates_province[:5])}{'...' if len(excluded_dates_province) > 5 else ''}")
                
                # Thống kê nhanh
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Giá trị mới nhất", f"{kpi_data[kpi].iloc[-1]:.2f}")
                with col2:
                    st.metric("Trung bình", f"{kpi_data[kpi].mean():.2f}")
                with col3:
                    change_pct = ((kpi_data[kpi].iloc[-1] - kpi_data[kpi].iloc[0]) / kpi_data[kpi].iloc[0]) * 100
                    st.metric("Thay đổi tổng", f"{change_pct:.2f}%")
    
    # Nút phân tích
    if st.button("🚀 Phân tích chi tiết", type="primary", use_container_width=True):
        with st.spinner("Đang phân tích..."):
            try:
                # Gọi hàm phân tích
                result = analyze_province_kpi(
                    province, 
                    kpi, 
                    file_path=file_path,
                    lookback_days=lookback_days,
                    decline_threshold=decline_threshold
                )
                
                if result:
                    detector_result, alerts, matched_province = result
                    
                    # Hiển thị kết quả
                    st.success(f"✅ Phân tích hoàn thành cho {matched_province} - {kpi}")
                    
                    # Thống kê
                    province_data = df[df['CTKD7'] == matched_province].copy()
                    kpi_data = province_data[['Ngay7', kpi]].copy()
                    kpi_data = kpi_data.sort_values('Ngay7')
                    kpi_data = kpi_data[(kpi_data[kpi].notna()) & (kpi_data[kpi] != 0)]
                    
                    # Loại bỏ ngày được chọn
                    if excluded_dates_province:
                        kpi_data = kpi_data[~kpi_data['Ngay7'].isin(excluded_dates_province)]
                    
                    # Lọc theo khoảng ngày nếu có
                    if date_range_province and len(date_range_province) == 2:
                        kpi_data['Ngay7_dt'] = pd.to_datetime(kpi_data['Ngay7'], format='%d/%m/%Y', errors='coerce')
                        start_date_prov = pd.Timestamp(date_range_province[0])
                        end_date_prov = pd.Timestamp(date_range_province[1])
                        kpi_data = kpi_data[
                            (kpi_data['Ngay7_dt'] >= start_date_prov) & 
                            (kpi_data['Ngay7_dt'] <= end_date_prov)
                        ]
                        kpi_data = kpi_data.drop('Ngay7_dt', axis=1)
                    
                    if len(kpi_data) > 0:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Min", f"{kpi_data[kpi].min():.2f}")
                        with col2:
                            st.metric("Max", f"{kpi_data[kpi].max():.2f}")
                        with col3:
                            st.metric("Trung bình", f"{kpi_data[kpi].mean():.2f}")
                        with col4:
                            st.metric("Giá trị mới nhất", f"{kpi_data[kpi].iloc[-1]:.2f}")
                    
                    # Hiển thị alerts nếu có
                    if alerts:
                        st.warning(f"⚠️ Phát hiện {len(alerts)} cảnh báo suy giảm:")
                        for alert in alerts:
                            st.error(f"""
                            **Tỉnh**: {alert['province']}  
                            **KPI**: {alert['kpi']}  
                            **Ngày**: {alert['latest_date'].strftime('%d/%m/%Y')}  
                            **Suy giảm**: {alert['decline_pct']:.2f}%  
                            **Mức độ**: {alert['severity']}
                            """)
                    else:
                        st.info("✅ Không phát hiện suy giảm mạnh")
                    
                    # Hiển thị biểu đồ
                    st.subheader("📈 Biểu đồ xu hướng KPI")
                    
                    if len(kpi_data) > 0:
                        # Chuẩn hóa ngày
                        kpi_data['Ngay7'] = pd.to_datetime(kpi_data['Ngay7'], format='%d/%m/%Y', errors='coerce')
                        kpi_data = kpi_data.sort_values('Ngay7')
                        
                        # Tạo biểu đồ
                        fig, ax = plt.subplots(figsize=(14, 6))
                        ax.plot(kpi_data['Ngay7'], kpi_data[kpi], marker='o', linewidth=2, markersize=4)
                        ax.set_title(f'{kpi} - {matched_province}', fontsize=14, fontweight='bold')
                        ax.set_xlabel('Ngày', fontsize=12)
                        ax.set_ylabel('', fontsize=12)  # Bỏ label trục Y
                        ax.grid(True, alpha=0.3)
                        
                        # Hiển thị tất cả các ngày trên trục x (bất kỳ khoảng ngày nào)
                        ax.xaxis.set_major_locator(DayLocator(interval=1))  # Luôn hiển thị tất cả các ngày
                        ax.xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))
                        ax.tick_params(axis='x', rotation=45)
                        
                        # Đảm bảo trục Y luôn hiển thị đầy đủ số khi phóng to
                        ax.tick_params(axis='y', which='both', labelsize=10)
                        ax.yaxis.set_minor_locator(plt.NullLocator())  # Tắt minor ticks
                        # Force hiển thị tối thiểu số tick trên trục Y
                        ax.yaxis.set_major_locator(MaxNLocator(nbins=10, integer=False))
                        # Format 2 chữ số thập phân cho trục Y
                        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f"{y:.2f}"))
                        # Tăng margin bên trái để có chỗ hiển thị số
                        fig.subplots_adjust(left=0.10, right=0.95, top=0.93, bottom=0.15)
                        
                        # Điều chỉnh layout để tránh nhãn bị cắt
                        plt.setp(ax.xaxis.get_majorticklabels(), ha='right')
                        
                        # Tăng kích thước biểu đồ khi có nhiều ngày để hiển thị đầy đủ
                        num_days = len(kpi_data)
                        if num_days > 30:
                            fig.set_size_inches(18, 6)
                        elif num_days > 20:
                            fig.set_size_inches(16, 6)
                        else:
                            fig.set_size_inches(14, 6)
                        
                        # Highlight lookback days
                        if lookback_days and len(kpi_data) >= lookback_days:
                            latest_date = kpi_data['Ngay7'].iloc[-1]
                            lookback_date = latest_date - pd.Timedelta(days=lookback_days)
                            mask = kpi_data['Ngay7'] >= lookback_date
                            ax.plot(kpi_data[mask]['Ngay7'], kpi_data[mask][kpi], 
                                   marker='o', linewidth=3, markersize=6, 
                                   color='red', label=f'{lookback_days} ngày gần nhất')
                            ax.legend()
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                        
                        # Thêm biểu đồ tương tác bằng Streamlit (YYYY-MM-DD)
                        st.subheader("📊 Biểu đồ tương tác")
                        kpi_data_display = kpi_data.copy()
                        kpi_data_display['Ngay7'] = kpi_data_display['Ngay7'].dt.strftime('%Y-%m-%d')
                        st.line_chart(kpi_data_display.set_index('Ngay7')[kpi])
                    else:
                        st.warning("⚠️ Không có dữ liệu để vẽ biểu đồ")
                        
            except Exception as e:
                st.error(f"❌ Lỗi khi phân tích: {str(e)}")
                st.exception(e)

# TAB 3: TẤT CẢ TỈNH
with tab3:
    st.header("📈 Phân tích tất cả tỉnh")
    
    # Chọn KPI (hiển thị tên thân thiện) - tính độc lập để không phụ thuộc biến trước đó
    def _norm2(s: str) -> str:
        import unicodedata as _ud
        s = _ud.normalize('NFD', str(s))
        s = ''.join(ch for ch in s if _ud.category(ch) != 'Mn')
        return s.upper().replace(' ', '').replace('-', '').replace('.', '')
    # Bổ sung các mã cột sự cố dạng viết tắt: SCL, SCNT1, SCRNT
    tokens_all = ['MTCL', 'CSSR', 'CDR', 'HOSR', 'ERAB', 'DATA', 'VN', 'QOS', 'SR', 'DR', 'COVERAGE', 'CHATLUONG', 'SUCO', 'SU_CO', 'SCL', 'SCNT1', 'SCRNT']
    kpi_cols_raw_all = [c for c in df.columns if any(t in _norm2(c) for t in tokens_all)]
    alias_display_map_all = {'ID4G_USR_DL_THP': '4G_USR_DL_THP'}
    # Bổ sung alias cho sự cố và vùng phủ
    for c in kpi_cols_raw_all:
        cn = _norm2(c)
        if cn in ('SUCOLON', 'SCL'):
            alias_display_map_all[c] = 'SuCoLon'
        elif cn in ('SUCONGHIEMTRONG', 'SCNT1'):
            alias_display_map_all[c] = 'SuCoNghiemTrong'
        elif cn in ('SUCORATNGHIEMTRONG', 'SCRNT'):
            alias_display_map_all[c] = 'SuCoRatNghiemTrong'
        elif cn in ('COVERAGE4G', 'CHATLUONGVUNGPHU'):
            alias_display_map_all[c] = 'ChatLuongVungPhu'
    kpi_display_options_all = [alias_display_map_all.get(c, c) for c in kpi_cols_raw_all]
    selected_kpi_all_display = st.selectbox(
        "Chọn KPI để phân tích cho tất cả tỉnh",
        kpi_display_options_all
    )
    if selected_kpi_all_display == '4G_USR_DL_THP':
        if '4G_USR_DL_THP' in df.columns:
            kpi_all = '4G_USR_DL_THP'
        else:
            kpi_all = 'ID4G_USR_DL_THP'
    else:
        reverse_map_all = {v: k for k, v in alias_display_map_all.items()}
        if selected_kpi_all_display in reverse_map_all:
            kpi_all = reverse_map_all[selected_kpi_all_display]
        else:
            kpi_all = selected_kpi_all_display
    
    # Lọc ngày - Tính năng loại bỏ ngày bị lỗi
    st.subheader("🔧 Lọc ngày")
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        # Lấy danh sách ngày có dữ liệu (chuẩn hóa theo datetime để sắp xếp đúng)
        all_dates_dt = pd.to_datetime(df['Ngay7'], format='%d/%m/%Y', errors='coerce').dropna()
        all_dates_dt = all_dates_dt.sort_values().unique()
        # Format ngày theo D/M/Y (bỏ giờ)
        all_dates_str = [d.strftime('%d/%m/%Y') for d in all_dates_dt]
        
        # Multi-select để chọn ngày cần loại bỏ
        excluded_dates = st.multiselect(
            "❌ Chọn ngày cần loại bỏ (ngày bị lỗi)",
            options=all_dates_str,
            help="Chọn các ngày có dữ liệu lỗi để loại bỏ khỏi biểu đồ",
            default=[]
        )
    
    with col_filter2:
        # Chọn khoảng ngày để hiển thị (dựa trên min/max datetime thực tế)
        if len(all_dates_dt) > 0:
            try:
                date_min = pd.to_datetime(all_dates_dt.min(), errors='coerce')
                date_max = pd.to_datetime(all_dates_dt.max(), errors='coerce')
                
                if pd.notna(date_min) and pd.notna(date_max):
                    date_range = st.date_input(
                        "📅 Chọn khoảng ngày hiển thị",
                        value=(date_min.date(), date_max.date()),
                        min_value=date_min.date(),
                        max_value=date_max.date(),
                        help="Chọn khoảng ngày muốn xem trong biểu đồ"
                    )
                else:
                    date_range = None
            except:
                date_range = None
        else:
            date_range = None
    
    # Hiển thị biểu đồ tất cả tỉnh ngay khi chọn KPI
    if kpi_all:
        st.subheader("📊 Biểu đồ so sánh tất cả tỉnh")
        
        # Lấy dữ liệu cho tất cả tỉnh
        all_provinces_data = []
        provinces_list = sorted([p for p in df['CTKD7'].dropna().unique()])
        
        for province_name in provinces_list:
            province_data = df[df['CTKD7'] == province_name].copy()
            if len(province_data) > 0 and kpi_all in province_data.columns:
                kpi_data = province_data[['Ngay7', kpi_all]].copy()
                kpi_data = kpi_data[(kpi_data[kpi_all].notna()) & (kpi_data[kpi_all] != 0)]
                
                # Loại bỏ ngày được chọn
                if excluded_dates:
                    kpi_data = kpi_data[~kpi_data['Ngay7'].isin(excluded_dates)]
                
                # Lọc theo khoảng ngày nếu có
                if date_range and len(date_range) == 2:
                    kpi_data['Ngay7_dt'] = pd.to_datetime(kpi_data['Ngay7'], format='%d/%m/%Y', errors='coerce')
                    start_date = pd.Timestamp(date_range[0])
                    end_date = pd.Timestamp(date_range[1])
                    kpi_data = kpi_data[
                        (kpi_data['Ngay7_dt'] >= start_date) & 
                        (kpi_data['Ngay7_dt'] <= end_date)
                    ]
                    kpi_data = kpi_data.drop('Ngay7_dt', axis=1)
                
                if len(kpi_data) > 0:
                    kpi_data['Ngay7'] = pd.to_datetime(kpi_data['Ngay7'], format='%d/%m/%Y', errors='coerce')
                    kpi_data = kpi_data.sort_values('Ngay7')
                    kpi_data['Tỉnh'] = province_name
                    all_provinces_data.append(kpi_data[['Ngay7', kpi_all, 'Tỉnh']])
        
        if all_provinces_data:
            # Tạo DataFrame tổng hợp
            combined_df = pd.concat(all_provinces_data, ignore_index=True)  # giữ datetime
            
            # Pivot để có mỗi tỉnh là một cột và vẽ bằng Streamlit
            pivot_df = combined_df.pivot_table(
                index='Ngay7', 
                columns='Tỉnh', 
                values=kpi_all,
                aggfunc='first'
            )
            if len(pivot_df) > 0:
                # Định dạng index về chuỗi YYYY-MM-DD như trước
                pivot_df = pivot_df.copy()
                pivot_df.index = pivot_df.index.strftime('%Y-%m-%d')
                st.line_chart(pivot_df)
                
                # Thông báo nếu có ngày bị loại bỏ
                if excluded_dates:
                    st.info(f"⚠️ Đã loại bỏ {len(excluded_dates)} ngày: {', '.join(excluded_dates[:5])}{'...' if len(excluded_dates) > 5 else ''}")
            else:
                st.warning("⚠️ Không còn dữ liệu sau khi lọc. Vui lòng điều chỉnh bộ lọc.")
            
            # Thống kê nhanh
            st.subheader("📊 Thống kê nhanh")
            stats_cols = st.columns(min(4, len(provinces_list)))
            
            for idx, province_name in enumerate(provinces_list[:4]):
                with stats_cols[idx]:
                    province_data = df[df['CTKD7'] == province_name].copy()
                    if len(province_data) > 0 and kpi_all in province_data.columns:
                        kpi_data = province_data[['Ngay7', kpi_all]].copy()
                        kpi_data = kpi_data[(kpi_data[kpi_all].notna()) & (kpi_data[kpi_all] != 0)]
                        if len(kpi_data) > 0:
                            latest_value = kpi_data[kpi_all].iloc[-1]
                            st.metric(province_name[:20], f"{latest_value:.2f}")
    
    if st.button("🔍 Phân tích chi tiết tất cả tỉnh", type="primary"):
        with st.spinner("Đang phân tích tất cả tỉnh..."):
            try:
                alerts = detector.detect_declines(kpi_all, lookback_days=lookback_days)
                
                if alerts:
                    st.warning(f"⚠️ Phát hiện {len(alerts)} tỉnh có suy giảm {kpi_all}")
                    
                    # Tạo DataFrame để hiển thị
                    alerts_df = pd.DataFrame(alerts)
                    alerts_df = alerts_df[['province', 'kpi', 'latest_date', 'latest_value', 
                                         'compare_value', 'decline_pct', 'severity']]
                    alerts_df['latest_date'] = alerts_df['latest_date'].dt.strftime('%d/%m/%Y')
                    alerts_df.columns = ['Tỉnh', 'KPI', 'Ngày', 'Giá trị hiện tại', 
                                        'Giá trị trước', 'Suy giảm (%)', 'Mức độ']
                    
                    alerts_df_display = format_dates_for_display(alerts_df, ('Ngày',))
                    st.dataframe(alerts_df_display, use_container_width=True)
                    
                    # Vẽ biểu đồ cho các tỉnh có vấn đề
                    st.subheader("📈 Biểu đồ các tỉnh có suy giảm")
                    
                    if len(alerts) > 0:
                        # Lấy danh sách tỉnh có vấn đề
                        provinces_with_issues = [a['province'] for a in alerts]
                        
                        # Tạo biểu đồ matplotlib
                        fig, ax = plt.subplots(figsize=(14, 8))
                        
                        for province_name in provinces_with_issues:
                            province_data = df[df['CTKD7'] == province_name].copy()
                            if len(province_data) > 0 and kpi_all in province_data.columns:
                                kpi_data = province_data[['Ngay7', kpi_all]].copy()
                                kpi_data = kpi_data[(kpi_data[kpi_all].notna()) & (kpi_data[kpi_all] != 0)]
                                
                                # Loại bỏ ngày được chọn
                                if excluded_dates:
                                    kpi_data = kpi_data[~kpi_data['Ngay7'].isin(excluded_dates)]
                                
                                # Lọc theo khoảng ngày nếu có
                                if date_range and len(date_range) == 2:
                                    kpi_data['Ngay7_dt'] = pd.to_datetime(kpi_data['Ngay7'], format='%d/%m/%Y', errors='coerce')
                                    start_date = pd.Timestamp(date_range[0])
                                    end_date = pd.Timestamp(date_range[1])
                                    kpi_data = kpi_data[
                                        (kpi_data['Ngay7_dt'] >= start_date) & 
                                        (kpi_data['Ngay7_dt'] <= end_date)
                                    ]
                                    kpi_data = kpi_data.drop('Ngay7_dt', axis=1)
                                
                                if len(kpi_data) > 0:
                                    kpi_data['Ngay7'] = pd.to_datetime(kpi_data['Ngay7'], format='%d/%m/%Y', errors='coerce')
                                    kpi_data = kpi_data.sort_values('Ngay7')
                                    
                                    # Tìm mức độ nghiêm trọng
                                    alert = next((a for a in alerts if a['province'] == province_name), None)
                                    if alert:
                                        severity = alert['severity']
                                        if severity == 'Cực kỳ nghiêm trọng':
                                            color = 'red'
                                            linewidth = 3
                                        elif severity == 'Nghiêm trọng':
                                            color = 'orange'
                                            linewidth = 2.5
                                        elif severity == 'Cảnh báo':
                                            color = 'yellow'
                                            linewidth = 2
                                        else:
                                            color = 'blue'
                                            linewidth = 1.5
                                    else:
                                        color = 'gray'
                                        linewidth = 1.5
                                    
                                    ax.plot(kpi_data['Ngay7'], kpi_data[kpi_all], 
                                           marker='o', linewidth=linewidth, markersize=3,
                                           label=f"{province_name} ({severity if alert else 'OK'})",
                                           color=color, alpha=0.7)
                        
                        ax.set_title(f'{kpi_all} - Các tỉnh có suy giảm', fontsize=16, fontweight='bold')
                        ax.set_xlabel('Ngày', fontsize=12)
                        ax.set_ylabel('', fontsize=12)  # Bỏ label trục Y
                        ax.grid(True, alpha=0.3)
                        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
                        
                        # Hiển thị tất cả các ngày trên trục x (bất kỳ khoảng ngày nào)
                        ax.xaxis.set_major_locator(DayLocator(interval=1))  # Luôn hiển thị tất cả các ngày
                        ax.xaxis.set_major_formatter(DateFormatter('%d/%m/%Y'))
                        ax.tick_params(axis='x', rotation=45)
                        plt.setp(ax.xaxis.get_majorticklabels(), ha='right')
                        
                        # Đảm bảo trục Y luôn hiển thị đầy đủ số khi phóng to
                        ax.tick_params(axis='y', which='both', labelsize=10)
                        ax.yaxis.set_minor_locator(plt.NullLocator())  # Tắt minor ticks
                        # Force hiển thị tối thiểu số tick trên trục Y
                        ax.yaxis.set_major_locator(MaxNLocator(nbins=10, integer=False))
                        # Format 2 chữ số thập phân cho trục Y
                        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f"{y:.2f}"))
                        # Tăng margin bên trái để có chỗ hiển thị số (đặc biệt khi có legend bên phải)
                        fig.subplots_adjust(left=0.10, right=0.85, top=0.93, bottom=0.15)
                        
                        # Tính số ngày và tăng kích thước biểu đồ khi có nhiều ngày
                        all_dates_in_chart = set()
                        for province_name in provinces_with_issues:
                            province_data_temp = df[df['CTKD7'] == province_name].copy()
                            if len(province_data_temp) > 0 and kpi_all in province_data_temp.columns:
                                kpi_data_temp = province_data_temp[['Ngay7', kpi_all]].copy()
                                kpi_data_temp = kpi_data_temp[(kpi_data_temp[kpi_all].notna()) & (kpi_data_temp[kpi_all] != 0)]
                                if excluded_dates:
                                    kpi_data_temp = kpi_data_temp[~kpi_data_temp['Ngay7'].isin(excluded_dates)]
                                all_dates_in_chart.update(kpi_data_temp['Ngay7'].unique())
                        
                        num_days = len(all_dates_in_chart)
                        if num_days > 30:
                            fig.set_size_inches(20, 8)
                        elif num_days > 20:
                            fig.set_size_inches(18, 8)
                        else:
                            fig.set_size_inches(16, 8)
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                    
                    # Download CSV
                    csv = alerts_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Download báo cáo CSV",
                        data=csv,
                        file_name=f"alerts_{kpi_all}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.success("✅ Không phát hiện suy giảm nào cho tất cả tỉnh")
                    
                    # Vẫn hiển thị biểu đồ tất cả tỉnh (đã lọc)
                    st.subheader("📈 Biểu đồ tất cả tỉnh")
                    if all_provinces_data:
                        # Rebuild với filter nếu cần
                        filtered_all_provinces_data = []
                        for province_name in provinces_list:
                            province_data = df[df['CTKD7'] == province_name].copy()
                            if len(province_data) > 0 and kpi_all in province_data.columns:
                                kpi_data = province_data[['Ngay7', kpi_all]].copy()
                                kpi_data = kpi_data[(kpi_data[kpi_all].notna()) & (kpi_data[kpi_all] != 0)]
                                
                                # Loại bỏ ngày được chọn
                                if excluded_dates:
                                    kpi_data = kpi_data[~kpi_data['Ngay7'].isin(excluded_dates)]
                                
                                # Lọc theo khoảng ngày nếu có
                                if date_range and len(date_range) == 2:
                                    kpi_data['Ngay7_dt'] = pd.to_datetime(kpi_data['Ngay7'], format='%d/%m/%Y', errors='coerce')
                                    start_date = pd.Timestamp(date_range[0])
                                    end_date = pd.Timestamp(date_range[1])
                                    kpi_data = kpi_data[
                                        (kpi_data['Ngay7_dt'] >= start_date) & 
                                        (kpi_data['Ngay7_dt'] <= end_date)
                                    ]
                                    kpi_data = kpi_data.drop('Ngay7_dt', axis=1)
                                
                                if len(kpi_data) > 0:
                                    kpi_data['Ngay7'] = pd.to_datetime(kpi_data['Ngay7'], format='%d/%m/%Y', errors='coerce')
                                    kpi_data = kpi_data.sort_values('Ngay7')
                                    kpi_data['Tỉnh'] = province_name
                                    filtered_all_provinces_data.append(kpi_data[['Ngay7', kpi_all, 'Tỉnh']])
                        
                        if filtered_all_provinces_data:
                            combined_df = pd.concat(filtered_all_provinces_data, ignore_index=True)  # giữ datetime
                            pivot_df = combined_df.pivot_table(index='Ngay7', columns='Tỉnh', values=kpi_all, aggfunc='first')
                            pivot_df = pivot_df.copy()
                            pivot_df.index = pivot_df.index.strftime('%Y-%m-%d')
                            st.line_chart(pivot_df)
                    
            except Exception as e:
                st.error(f"❌ Lỗi: {str(e)}")
                st.exception(e)

# TAB 4: ALERTS
with tab4:
    st.header("🚨 Hệ thống cảnh báo")
    
    st.info("""
    **Tính năng này sẽ hiển thị tất cả cảnh báo suy giảm KPI.**
    
    - Quét tất cả KPI quan trọng
    - Phát hiện suy giảm theo ngưỡng đã cấu hình
    - Hiển thị danh sách cảnh báo chi tiết
    """)
    
    critical_kpis = st.multiselect(
        "Chọn KPI quan trọng cần giám sát",
        kpi_cols,
        default=['MTCL_2024', 'CSSR', 'CDR', 'HOSR_4G_2024'] if all(k in kpi_cols for k in ['MTCL_2024', 'CSSR', 'CDR', 'HOSR_4G_2024']) else kpi_cols[:4]
    )
    
    if st.button("🔍 Quét cảnh báo", type="primary"):
        with st.spinner("Đang quét tất cả KPI..."):
            all_alerts = []
            
            for kpi in critical_kpis:
                try:
                    alerts = detector.detect_declines(kpi, lookback_days=lookback_days)
                    all_alerts.extend(alerts)
                except Exception as e:
                    st.warning(f"⚠️ Lỗi khi phân tích {kpi}: {str(e)}")
            
            if all_alerts:
                st.error(f"🚨 Phát hiện {len(all_alerts)} cảnh báo!")
                
                # Nhóm theo mức độ
                severity_counts = {}
                for alert in all_alerts:
                    sev = alert['severity']
                    severity_counts[sev] = severity_counts.get(sev, 0) + 1
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Cực kỳ nghiêm trọng", severity_counts.get('Cực kỳ nghiêm trọng', 0))
                with col2:
                    st.metric("Nghiêm trọng", severity_counts.get('Nghiêm trọng', 0))
                with col3:
                    st.metric("Cảnh báo", severity_counts.get('Cảnh báo', 0))
                with col4:
                    st.metric("Nhẹ", severity_counts.get('Nhẹ', 0))
                
                # Hiển thị chi tiết
                alerts_df = pd.DataFrame(all_alerts)
                alerts_df = alerts_df.sort_values('decline_pct', ascending=False)
                alerts_df_display = format_dates_for_display(alerts_df, ('latest_date', 'Ngay7', 'Ngày'))
                st.dataframe(alerts_df_display, use_container_width=True)
            else:
                st.success("✅ Không có cảnh báo nào!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>📊 Hệ thống Giám sát KPI | Chạy trên laptop local</p>
    <p>Phiên bản 1.0 | Sử dụng Streamlit</p>
</div>
""", unsafe_allow_html=True)