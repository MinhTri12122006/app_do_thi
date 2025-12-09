import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import io
import pandas as pd

# màu sắc trong đồ thị 
MAU_SAC = {
    "mac_dinh": "#97C2FC",
    "duong_di": "#FF6961",      
    "duyet": "#77DD77",         
    "hai_phia_A": "#ADD8E6",   
    "hai_phia_B": "#FFD700"    
} 

# chuyển đổi dử liệu 
def tao_do_thi_tu_du_lieu(du_lieu_text, co_huong):
    if co_huong:
        G = nx.DiGraph()
    else:
        G = nx.Graph()

    kq = io.StringIO(du_lieu_text)
    for dong in kq.readlines():
        dong = dong.strip()
        if not dong or dong.startswith('#'): continue
        parts = dong.split(',')
        try:
            u, v = parts[0].strip(), parts[1].strip()
            w = 1.0
            if len(parts) > 2:
                w = float(parts[2].strip())
            G.add_edge(u, v, weight=w, label=str(w))
        except: continue
    return G

def dat_lai_mau_mac_dinh(G):
    for n in G.nodes():
        G.nodes[n]['color'] = MAU_SAC["mac_dinh"]
        G.nodes[n]['size'] = 15
    for u, v in G.edges():
        G.edges[u, v]['color'] = "#C0C0C0"
        G.edges[u, v]['width'] = 2

# TÌM ĐƯỜNG ĐI NGẮN NHẤT
def chuc_nang_tim_duong_di(G, bat_dau, ket_thuc):
    try:
        path = nx.shortest_path(G, bat_dau, ket_thuc, weight='weight')
        w = nx.shortest_path_length(G, bat_dau, ket_thuc, weight='weight')
        
        st.success(f"Đường đi ngắn nhất: {' → '.join(path)}")
        st.info(f"Tổng trọng số: {w}")
        
        for n in path: 
            G.nodes[n]['color'] = MAU_SAC["duong_di"]
            G.nodes[n]['size'] = 25
        for i in range(len(path)-1):
            u, v = path[i], path[i+1]
            G.edges[u, v]['color'] = MAU_SAC["duong_di"]
            G.edges[u, v]['width'] = 5
    except:
        st.error("Không có đường đi.")

# DUYỆT ĐỒ THỊ (BFS & DFS)
def chuc_nang_duyet_do_thi(G, bat_dau, kieu_duyet):
    try:
        if kieu_duyet == "BFS":
            edges = list(nx.bfs_edges(G, bat_dau))
            nodes = list(nx.bfs_tree(G, bat_dau)) 
        else:
            # DFS
            edges = list(nx.dfs_edges(G, bat_dau))
            nodes = list(nx.dfs_tree(G, bat_dau))
            
        st.success(f"Thứ tự duyệt {kieu_duyet}: {' → '.join(nodes)}")
        
        for n in nodes: G.nodes[n]['color'] = MAU_SAC["duyet"]
        for u, v in edges:
            if G.has_edge(u, v):
                G.edges[u, v]['color'] = MAU_SAC["duyet"]
                G.edges[u, v]['width'] = 4
    except Exception as e:
        st.error(f"Lỗi: {e}")

# KIỂM TRA 2 PHÍA
def chuc_nang_kiem_tra_2_phia(G):
    try:
        sets = nx.bipartite.sets(G)
        st.success("Đồ thị là đồ thị 2 phía!")
        
        tap_A = list(sets[0])
        tap_B = list(sets[1])
        st.json({"Tập A": tap_A, "Tập B": tap_B})
        
        for n in tap_A: G.nodes[n]['color'] = MAU_SAC["hai_phia_A"]
        for n in tap_B: G.nodes[n]['color'] = MAU_SAC["hai_phia_B"]
    except:
        st.error("Không phải đồ thị 2 phía.")

# VẼ ĐỒ THỊ TRỰC QUAN 
def ve_do_thi_truc_quan(G, co_huong):
    net = Network(height="450px", width="100%", notebook=True, directed=co_huong, cdn_resources='in_line')
    net.from_nx(G)
    net.show_buttons(filter_=['physics'])
    return net.generate_html()

# Chuyển đổi đồ thị sang ma trận , danh sách kề , cạnh 
def hien_thi_chuyen_doi_bieu_dien(G):
    st.header("6. Chuyển đổi biểu diễn đồ thị")
    ma_tran_ke, danh_sach_ke, danh_sach_canh = st.tabs(["Ma trận kề", "Danh sách kề", "Danh sách cạnh"])
    
    nodes = sorted(list(G.nodes()))
    
    with ma_tran_ke: 
        st.write("Ma trận trọng số :")
        mat = nx.to_numpy_array(G, nodelist=nodes, weight='weight')
        df = pd.DataFrame(mat, index=nodes, columns=nodes)
        st.dataframe(df.style.format("{:.0f}"))
        
    with danh_sach_ke:
        st.write("Danh sách kề :")
        st.json(nx.to_dict_of_lists(G))
        
    with danh_sach_canh: 
        st.write("Danh sách cạnh :")
        txt_canh = ""
        for u, v, d in G.edges(data=True):
            txt_canh += f"{u}, {v}, {d.get('weight', 1)}\n"
        st.text_area("", value=txt_canh, height=150, disabled=True)
    
    return txt_canh

# LƯU ĐỒ THỊ 
def hien_thi_nut_luu(html_graph, txt_canh):
    st.sidebar.markdown("---")
    st.sidebar.header("2. Lưu Trữ")
    
    st.sidebar.download_button("Tải Đồ Thị (HTML)", html_graph, "do_thi.html", "text/html")
    st.sidebar.download_button("Tải Dữ Liệu (TXT)", txt_canh, "danh_sach_canh.txt", "text/plain")

# CÂY KHUNG NHỎ NHẤT (MST) prim và Kruskal
def chuc_nang_mst(G, thuat_toan):
    if G.is_directed():
        st.error("Lỗi: Thuật toán MST chỉ áp dụng cho đồ thị VÔ HƯỚNG.")
        return

    try:
        T = nx.minimum_spanning_tree(G, weight='weight', algorithm=thuat_toan)
        
        mst_edges = list(T.edges(data=True))
        tong_trong_so = T.size(weight='weight')
        
        st.success(f"Kết quả thuật toán {thuat_toan.capitalize()}:")
        st.info(f"Tổng trọng số cây khung: {tong_trong_so}")

        mau_mst = "#FFA500"
    
        dat_lai_mau_mac_dinh(G)
        
        for u, v, data in mst_edges:

            if G.has_edge(u, v):
                G.edges[u, v]['color'] = mau_mst
                G.edges[u, v]['width'] = 6
            

            G.nodes[u]['color'] = mau_mst
            G.nodes[v]['color'] = mau_mst
        st.write("Các cạnh trong cây khung:")
        st.json([(u, v, d['weight']) for u, v, d in mst_edges])
            
    except Exception as e:
        st.error(f"Lỗi khi chạy thuật toán: {e}")
        st.warning("Lưu ý: Đồ thị phải liên thông mới tìm được cây khung.")

# Fleury
def chuc_nang_euler(G, thuat_toan):
    try:
        path = []
        is_circuit = False
        # Hierholzer (Tìm Chu Trình)
        if thuat_toan == "Hierholzer":
            if not nx.is_eulerian(G):
                st.error("Lỗi: Đồ thị không có Chu Trình Euler (các đỉnh phải có bậc chẵn hoặc cân bằng vào/ra).")
                st.warning("Gợi ý: Thử dùng Fleury để tìm đường đi.")
                return
            path = list(nx.eulerian_circuit(G))
            is_circuit = True
            st.success("Tìm thấy Chu Trình Euler (Hierholzer)!")

        # Fleury (Tìm Đường Đi)
        elif thuat_toan == "Fleury":
            if not nx.has_eulerian_path(G):
                st.error("Lỗi: Đồ thị không có Đường Đi Euler (quá nhiều đỉnh bậc lẻ).")
                return
            path = list(nx.eulerian_path(G))
            st.success("Tìm thấy Đường Đi Euler (Fleury)!")

        # Hiển thị kết quả
        txt_path = " -> ".join([f"({u},{v})" for u, v in path])
        st.info(f"Lộ trình: {txt_path}")
        
        # Tô màu đường đi
        mau_euler = "#FF00FF" 
        dat_lai_mau_mac_dinh(G)
        
        for i, (u, v) in enumerate(path):
            if G.has_edge(u, v): 
                G.edges[u, v]['color'] = mau_euler
                G.edges[u, v]['width'] = 6
                G.edges[u, v]['label'] = str(i + 1) 
            
            G.nodes[u]['color'] = mau_euler
            G.nodes[v]['color'] = mau_euler

    except Exception as e:
        st.error(f"Không thể thực hiện thuật toán: {e}")




def main():
    st.set_page_config(page_title="Đồ Thị 6 Chức Năng")
    st.title("Chương trình Xử lý Đồ thị (6 Chức năng)")

    st.sidebar.header("Nhập dữ liệu")
    co_huong = st.sidebar.checkbox("Đồ thị có hướng ")
    mac_dinh = """A, B, 5
                    B, C, 5
                    C, A, 5
                    C, D, 7
                    D, E, 7
                    E, C, 7 """
    data_input = st.sidebar.text_area("Danh sách cạnh (u, v, w):", value=mac_dinh, height=150)
    # Tạo đồ thị
    G = tao_do_thi_tu_du_lieu(data_input, co_huong)
    if G.number_of_nodes() == 0:
        st.warning("Vui lòng nhập dữ liệu cạnh.")
        return

    dat_lai_mau_mac_dinh(G)
    nodes = sorted(list(G.nodes()))

# ĐIỀU KHIỂN CHỨC NĂNG (Sidebar)
    st.sidebar.markdown("---")
    st.sidebar.header("Bảng Điều Khiển")
    
    # Tìm đường đi
    with st.sidebar.expander("3. Tìm đường đi ngắn nhất"):
        s = st.selectbox("Từ:", nodes, key='s')
        e = st.selectbox("Đến:", nodes, index=len(nodes)-1, key='e')
        if st.button("Tìm đường đi"):
            chuc_nang_tim_duong_di(G, s, e)

    # Duyệt
    with st.sidebar.expander("4. Duyệt BFS & DFS"):
        root = st.selectbox("Gốc:", nodes, key='root')
        c1, c2 = st.columns(2)
        if c1.button("BFS"): chuc_nang_duyet_do_thi(G, root, "BFS")
        if c2.button("DFS"): chuc_nang_duyet_do_thi(G, root, "DFS")

    # Kiểm tra 2 phía
    with st.sidebar.expander("5. Kiểm tra 2 phía"):
        if st.button("Kiểm tra ngay"):
            chuc_nang_kiem_tra_2_phia(G)
    
    # Prim & Kruskal
    with st.sidebar.expander("7. Cây khung nhỏ nhất (MST)"):
        st.write("Chọn thuật toán:")
        c1, c2 = st.columns(2)
        if c1.button("Prim"): 
            chuc_nang_mst(G, "prim")
        if c2.button("Kruskal"): 
            chuc_nang_mst(G, "kruskal")
    
    # MST 
    with st.sidebar.expander("8. Euler (Fleury & Hierholzer)"):
        st.write("Chọn thuật toán:")
        c1, c2 = st.columns(2)
        
        # Fleury 
        if c1.button("Fleury"): 
            chuc_nang_euler(G, "Fleury")
            
        # Hierholzer 
        if c2.button("Hierholzer"): 
            chuc_nang_euler(G, "Hierholzer")

    st.header("1. Đồ thị Trực quan")
    html_graph = ve_do_thi_truc_quan(G, co_huong)
    components.html(html_graph, height=460)
# chuyển đổi 
    txt_canh = hien_thi_chuyen_doi_bieu_dien(G)
# lưu 
    hien_thi_nut_luu(html_graph, txt_canh)

if __name__ == "__main__":
    main()