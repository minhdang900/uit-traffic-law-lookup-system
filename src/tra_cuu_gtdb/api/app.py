"""Giao diện tra cứu — vỏ Streamlit.

Chạy:
    pip install -e '.[ui]'
    streamlit run src/tra_cuu_gtdb/api/app.py

Tệp này CỐ Ý mỏng: mọi thứ có thể sai (định dạng tiền, gom kết quả, xếp mức
tin cậy) nằm ở ``trinh_bay.py`` và được kiểm thử ở ``tests/test_trinh_bay.py``.
Ở đây chỉ có lệnh vẽ. ``tests/test_giao_dien.py`` canh cho ranh giới đó không
rữa, và canh cho mọi câu hỏi ví dụ đều thật sự trả lời được.
"""
from __future__ import annotations

import streamlit as st

from tra_cuu_gtdb.api.trinh_bay import TEN_LOAI, The, the_ket_qua, tom_tat

#: Chọn sao cho phủ nhiều lớp bài toán khác nhau — bấm nút mà cả sáu ra cùng
#: một kiểu trả lời thì không cho thấy hệ thống làm được gì.
VI_DU = [
    "Vượt đèn đỏ xe máy phạt bao nhiêu?",
    "Xe cơ giới là gì?",
    "Nồng độ cồn 0,3 mg/l phạt thế nào?",
    "Lỗi nào bị trừ 10 điểm giấy phép lái xe?",
    "Điều 6 khoản 9 điểm a Nghị định 168/2024/NĐ-CP nói về lỗi gì?",
    "Tôi vừa vượt đèn đỏ vừa không có giấy phép lái xe thì bị phạt bao nhiêu?",
]

HUY_HIEU = {"cao": "🟢", "trung bình": "🟡", "thấp": "🔴"}


@st.cache_resource(show_spinner="Đang nạp cơ sở tri thức…")
def nap_he_thong():
    """Nạp một lần cho cả phiên — dựng chỉ mục TF-IDF mất vài giây."""
    from tra_cuu_gtdb.reasoning.engine import TraCuuPhapLuat

    return TraCuuPhapLuat()


def ve_the(t: The) -> None:
    nhan = TEN_LOAI.get(t.loai, t.loai)
    if t.bo_sung:
        nhan += " · tri thức bổ sung"
    with st.container(border=True):
        st.markdown(f"**{t.tieu_de}**")
        st.caption(f"{HUY_HIEU.get(t.muc_tin_cay, '')} {nhan}"
                   + (f" · độ tin cậy {t.muc_tin_cay}" if t.diem is not None else ""))
        for d in t.dong:
            st.markdown(f"- {d}")
        if t.can_cu:
            st.caption(f"Căn cứ: {t.can_cu}")


def ve_vi_du() -> None:
    st.markdown("**Câu hỏi ví dụ**")
    cot = st.columns(2)
    for i, vd in enumerate(VI_DU):
        if cot[i % 2].button(vd, key=f"vd_{i}", use_container_width=True):
            st.session_state.truy_van = vd


def ve_ket_qua(kq: dict) -> None:
    if kq["khong_tim_thay"]:
        st.warning(tom_tat(kq))
        return
    st.success(tom_tat(kq))
    for t in the_ket_qua(kq):
        ve_the(t)
    if kq.get("lien_quan"):
        st.markdown("**Kiến thức liên quan**")
        st.markdown("\n".join(
            f"- {g['ten']} ({g['so_quy_dinh']} quy định)" for g in kq["lien_quan"]))
    with st.expander("Chi tiết phân tích truy vấn"):
        st.json({k: v for k, v in kq["phan_tich"].items() if k != "keyphrase"})


def main() -> None:
    st.set_page_config(page_title="Tra cứu pháp luật giao thông đường bộ",
                       page_icon="⚖️", layout="centered")
    st.title("Tra cứu pháp luật giao thông đường bộ")
    st.caption("CS106 · Đề tài 4 · Nhóm 7 — tri thức từ Luật 36/2024/QH15 và "
               "Nghị định 168/2024/NĐ-CP, bản hợp nhất tới 2026")

    ht = nap_he_thong()
    st.session_state.setdefault("truy_van", VI_DU[0])
    ve_vi_du()

    truy_van = st.text_input("Câu hỏi", key="truy_van",
                             placeholder="Ví dụ: không đội mũ bảo hiểm phạt bao nhiêu?")
    top_k = st.slider("Số kết quả mỗi loại", 1, 10, 5, key="top_k")

    st.divider()
    if truy_van.strip():
        ve_ket_qua(ht.hoi(truy_van, top_k=top_k))
    else:
        st.info("Nhập câu hỏi hoặc bấm một ví dụ ở trên.")


if __name__ == "__main__":
    main()
