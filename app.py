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
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
import unicodedata
from matplotlib.dates import DayLocator, DateFormatter
from matplotlib.ticker import MaxNLocator, FuncFormatter
matplotlib.use('Agg')  # Backend cho Streamlit

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
st.sidebar.subheader("📁 Quản lý dữ liệu")

# Chế độ upload: Replace hoặc Append
upload_mode = st.sidebar.radio(
    "Chế độ upload:",
    ["🔄 Thay thế file (Replace)", "➕ Gộp dữ liệu mới (Append)"],
    help="Replace: Thay thế toàn bộ file cũ\nAppend: Tự động gộp dữ liệu mới vào file cũ (tiết kiệm thời gian)",
    index=1
)

uploaded_file = st.sidebar.file_uploader(
    "Chọn file CSV dữ liệu KPI",
    type=['csv'],
    help="Upload file CSV chứa dữ liệu KPI",
    key="csv_uploader"
)

# Hàm merge dữ liệu mới vào file cũ - GIỮ NGUYÊN THỨ TỰ
def merge_data_files(old_file_path, new_file_path, output_path):
    """
    Gộp dữ liệu mới vào file cũ, loại bỏ duplicate, GIỮ NGUYÊN THỨ TỰ BAN ĐẦU
    
    Args:
        old_file_path: Đường dẫn file cũ
        new_file_path: Đường dẫn file mới (upload)
        output_path: Đường dẫn file output (thường là old_file_path)
    
    Returns:
        dict: Thông tin về quá trình merge
    """
    try:
        # Đọc file cũ (nếu có)
        if os.path.exists(old_file_path):
            df_old = pd.read_csv(old_file_path, encoding='utf-8-sig', low_memory=False)
            # Chuẩn hóa tên cột
            df_old.columns = [str(c).strip() for c in df_old.columns]
            # Giữ nguyên thứ tự ban đầu bằng cách thêm cột index gốc
            df_old['_original_index'] = range(len(df_old))
        else:
            df_old = pd.DataFrame()
        
        # Đọc file mới
        df_new = pd.read_csv(new_file_path, encoding='utf-8-sig', low_memory=False)
        df_new.columns = [str(c).strip() for c in df_new.columns]
        
        # Kiểm tra cột bắt buộc
        required_cols = ['Ngay7', 'CTKD7']
        missing_cols = [c for c in required_cols if c not in df_new.columns]
        if missing_cols:
            raise ValueError(f"File mới thiếu cột: {', '.join(missing_cols)}")
        
        # Nếu file cũ rỗng, chỉ cần lưu file mới
        if df_old.empty:
            df_merged = df_new.copy()
            duplicates_removed = 0
        else:
            # Kiểm tra cột có giống nhau không
            old_cols = set(df_old.columns) - {'_original_index'}
            new_cols = set(df_new.columns)
            if old_cols != new_cols:
                # Cảnh báo nhưng vẫn merge với cột chung
                common_cols = old_cols & new_cols
                st.sidebar.warning(f"⚠️ File có số cột khác nhau. Chỉ merge {len(common_cols)} cột chung.")
                df_old = df_old[list(common_cols) + ['_original_index']]
                df_new = df_new[list(common_cols)]
            
            # Xử lý duplicate thông minh: giữ nguyên thứ tự file cũ
            date_col = 'Ngay7'
            province_col = 'CTKD7'
            
            if date_col in df_old.columns and date_col in df_new.columns and province_col in df_old.columns and province_col in df_new.columns:
                # Chuyển đổi ngày để so sánh
                df_old[date_col + '_parsed'] = pd.to_datetime(
                    df_old[date_col], format='%d/%m/%Y', errors='coerce'
                )
                df_new[date_col + '_parsed'] = pd.to_datetime(
                    df_new[date_col], format='%d/%m/%Y', errors='coerce'
                )
                
                # Tạo key để xác định duplicate: Ngay7 + CTKD7
                df_old['_merge_key'] = df_old[date_col + '_parsed'].astype(str) + '_' + df_old[province_col].astype(str)
                df_new['_merge_key'] = df_new[date_col + '_parsed'].astype(str) + '_' + df_new[province_col].astype(str)
                
                # Lấy các key đã có trong file cũ
                existing_keys = set(df_old['_merge_key'].values)
                new_keys = set(df_new['_merge_key'].values)
                
                # Xác định dữ liệu mới (chưa có trong file cũ)
                df_new_only = df_new[~df_new['_merge_key'].isin(existing_keys)].copy()
                
                # Xác định dữ liệu cần cập nhật (có trong cả 2 file)
                keys_to_update = new_keys & existing_keys
                duplicates_removed = len(keys_to_update)
                
                # Xử lý duplicate: thay thế dòng cũ bằng dòng mới tại đúng vị trí
                if duplicates_removed > 0:
                    # Lấy dữ liệu mới cần cập nhật
                    df_new_update = df_new[df_new['_merge_key'].isin(keys_to_update)].copy()
                    
                    # Tạo mapping từ key đến dữ liệu mới
                    new_data_dict = {}
                    for _, row in df_new_update.iterrows():
                        key = row['_merge_key']
                        new_data_dict[key] = row
                    
                    # Thay thế dòng cũ bằng dòng mới tại đúng vị trí
                    for idx in df_old.index:
                        key = df_old.loc[idx, '_merge_key']
                        if key in new_data_dict:
                            # Thay thế dòng cũ bằng dòng mới, giữ nguyên index gốc
                            new_row = new_data_dict[key].copy()
                            new_row['_original_index'] = df_old.loc[idx, '_original_index']
                            df_old.loc[idx] = new_row
                    
                    # Xóa các dòng đã được cập nhật khỏi df_new_update để tránh trùng
                    df_new_update = pd.DataFrame()  # Đã xử lý xong
                
                # Xóa cột tạm từ df_old
                df_old = df_old.drop(columns=['_merge_key', date_col + '_parsed'], errors='ignore')
                
                # Thêm dữ liệu mới vào cuối, với index lớn hơn để giữ thứ tự
                if len(df_new_only) > 0:
                    df_new_only = df_new_only.drop(columns=['_merge_key', date_col + '_parsed'], errors='ignore')
                    # Thêm index lớn để đảm bảo dữ liệu mới ở cuối
                    max_old_index = df_old['_original_index'].max() if len(df_old) > 0 else -1
                    df_new_only['_original_index'] = range(max_old_index + 1, max_old_index + 1 + len(df_new_only))
                    
                    # Merge: file cũ (đã cập nhật duplicate) + dữ liệu mới
                    df_merged = pd.concat([df_old, df_new_only], ignore_index=True)
                else:
                    df_merged = df_old.copy()
                
                # Sắp xếp lại theo index gốc để giữ thứ tự ban đầu
                df_merged = df_merged.sort_values('_original_index', na_position='last')
                df_merged = df_merged.drop(columns=['_original_index'], errors='ignore')
                
            else:
                # Nếu không có cột ngày/tỉnh, merge đơn giản và loại bỏ duplicate
                df_merged = pd.concat([df_old.drop(columns=['_original_index'], errors='ignore'), df_new], ignore_index=True)
                before_dedup = len(df_merged)
                df_merged = df_merged.drop_duplicates(keep='last')
                duplicates_removed = before_dedup - len(df_merged)
        
        # Reset lại số thứ tự (STT) nếu có - ĐẾM LIÊN TỤC TỪ 1
        # Tìm cột STT (có thể là "STT", "stt", "Số thứ tự", "textbox164", hoặc các biến thể)
        stt_cols = [c for c in df_merged.columns if any(keyword in str(c).upper() 
                   for keyword in ['STT', 'SỐ THỨ TỰ', 'TEXTBOX164', 'TEXTBOX', 'NO', 'NUMBER', 'INDEX'])]
        
        if stt_cols:
            stt_col = stt_cols[0]  # Lấy cột đầu tiên tìm thấy
            
            # QUAN TRỌNG: Reset index của DataFrame trước khi gán STT
            # Đảm bảo index liên tục từ 0 đến len-1
            df_merged = df_merged.reset_index(drop=True)
            
            # Reset lại STT cho toàn bộ file đã merge, đếm liên tục từ 1
            # Sử dụng iloc để đảm bảo gán đúng cho tất cả các dòng
            try:
                # Cách 1: Gán trực tiếp bằng list
                df_merged[stt_col] = list(range(1, len(df_merged) + 1))
            except:
                try:
                    # Cách 2: Gán bằng Series với index đúng
                    df_merged[stt_col] = pd.Series(range(1, len(df_merged) + 1), index=df_merged.index)
                except:
                    # Cách 3: Gán từng dòng một (chậm nhưng chắc chắn)
                    for i in range(len(df_merged)):
                        df_merged.iloc[i, df_merged.columns.get_loc(stt_col)] = i + 1
        
        # Lưu file đã merge
        df_merged.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        # Thống kê
        stats = {
            'old_rows': len(df_old) if not df_old.empty else 0,
            'new_rows': len(df_new),
            'merged_rows': len(df_merged),
            'duplicates_removed': duplicates_removed,
            'added_rows': len(df_merged) - (len(df_old) if not df_old.empty else 0)
        }
        
        # Thống kê ngày
        if 'Ngay7' in df_merged.columns:
            df_merged['Ngay7_parsed'] = pd.to_datetime(
                df_merged['Ngay7'], format='%d/%m/%Y', errors='coerce'
            )
            stats['min_date'] = df_merged['Ngay7_parsed'].min()
            stats['max_date'] = df_merged['Ngay7_parsed'].max()
            df_merged = df_merged.drop(columns=['Ngay7_parsed'], errors='ignore')
        
        return stats
        
    except Exception as e:
        raise Exception(f"Lỗi khi merge dữ liệu: {str(e)}")

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

# Kiểm tra xem đã xử lý file này chưa (tránh vòng lặp vô hạn)
if 'last_processed_file' not in st.session_state:
    st.session_state.last_processed_file = None
if 'last_processed_size' not in st.session_state:
    st.session_state.last_processed_size = 0

if uploaded_file is not None:
    # Kiểm tra xem file này đã được xử lý chưa
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.last_processed_file == file_id:
        # File đã được xử lý, chỉ cần set file_path để tiếp tục
        file_path = '1.Ngày.csv'
    else:
        # Lưu file upload vào thư mục hiện tại
        file_path = '1.Ngày.csv'
        is_append_mode = "Append" in upload_mode
        
        if is_append_mode:
            # CHẾ ĐỘ APPEND: Gộp dữ liệu mới vào file cũ
            if os.path.exists(file_path):
                # Lưu file mới tạm thời
                temp_new_file = 'temp_new_data.csv'
                with open(temp_new_file, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                try:
                    # Merge dữ liệu
                    stats = merge_data_files(file_path, temp_new_file, file_path)
                    
                    # Đánh dấu đã xử lý file này
                    st.session_state.last_processed_file = file_id
                    
                    # Clear cache để load dữ liệu mới
                    load_data.clear()
                    
                    # Hiển thị thông tin merge
                    st.sidebar.success("✅ Đã gộp dữ liệu mới thành công!")
                    st.sidebar.info(f"📊 **Thống kê:**")
                    st.sidebar.info(f"  • Dòng cũ: {stats['old_rows']:,}")
                    st.sidebar.info(f"  • Dòng mới (upload): {stats['new_rows']:,}")
                    st.sidebar.info(f"  • Dòng sau merge: {stats['merged_rows']:,}")
                    st.sidebar.info(f"  • Dòng đã thêm: {stats['added_rows']:,}")
                    
                    if stats['duplicates_removed'] > 0:
                        st.sidebar.warning(f"⚠️ Đã loại bỏ {stats['duplicates_removed']:,} dòng trùng lặp (thay bằng dữ liệu mới)")
                    
                    if 'min_date' in stats and 'max_date' in stats:
                        min_date = stats['min_date']
                        max_date = stats['max_date']
                        if pd.notna(min_date) and pd.notna(max_date):
                            st.sidebar.info(f"📅 Khoảng ngày: {min_date.strftime('%d/%m/%Y')} - {max_date.strftime('%d/%m/%Y')}")
                    
                    file_changed = True
                    
                except Exception as e:
                    st.sidebar.error(f"❌ Lỗi khi gộp dữ liệu: {str(e)}")
                    st.exception(e)
                    st.stop()
                finally:
                    # Xóa file tạm
                    if os.path.exists(temp_new_file):
                        try:
                            os.remove(temp_new_file)
                        except:
                            pass
            else:
                # Chưa có file cũ, chỉ cần lưu file mới
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                st.session_state.last_processed_file = file_id
                load_data.clear()
                st.sidebar.success(f"✅ Đã tạo file mới! ({uploaded_file.size:,} bytes)")
                file_changed = True
        
        if not is_append_mode:
            # CHẾ ĐỘ REPLACE: Thay thế toàn bộ file cũ (GIỮ NGUYÊN CHỨC NĂNG CŨ)
            # Kiểm tra xem file có thay đổi không (dựa vào timestamp hoặc size)
            file_changed = True
            if os.path.exists(file_path):
                old_size = os.path.getsize(file_path)
                new_size = uploaded_file.size
                if old_size != new_size:
                    file_changed = True
                else:
                    # Kiểm tra nội dung (so sánh hash)
                    uploaded_file.seek(0)
                    new_content = uploaded_file.read()
                    uploaded_file.seek(0)
                    
                    with open(file_path, 'rb') as f:
                        old_content = f.read()
                    
                    if new_content != old_content:
                        file_changed = True
            
            # Lưu file mới
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            # Đánh dấu đã xử lý file này
            st.session_state.last_processed_file = file_id
            load_data.clear()
            
            st.sidebar.success(f"✅ Đã thay thế file thành công! ({uploaded_file.size:,} bytes)")
            
            # Hiển thị thông tin file
            st.sidebar.info(f"📄 Tên file: {uploaded_file.name}")
            file_changed = True

# Xác định file_path nếu chưa có
if file_path is None:
    if os.path.exists('1.Ngày.csv'):
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
        
        # Điều hướng trang
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
        
        # Hiển thị dữ liệu theo trang
        start_idx = (st.session_state.current_page - 1) * rows_per_page
        end_idx = start_idx + rows_per_page
        page_data = df.iloc[start_idx:end_idx]
        
        st.dataframe(page_data, use_container_width=True, height=400)
    else:
        # Hiển thị toàn bộ dữ liệu
        st.dataframe(df, use_container_width=True, height=600)

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
                    
                    st.dataframe(alerts_df, use_container_width=True)
                    
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
                st.dataframe(alerts_df, use_container_width=True)
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

