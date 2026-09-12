"""Giao diện tra cứu — vỏ Streamlit mỏng.

Chạy:
    pip install -e '.[ui]'
    streamlit run src/tra_cuu_gtdb/api/app.py

Tệp này CỐ Ý không chứa logic: mọi thứ có thể sai (định dạng tiền, gom kết quả,
xếp mức tin cậy) nằm ở ``trinh_bay.py`` và được kiểm thử ở
``tests/test_trinh_bay.py``. Ở đây chỉ có lệnh vẽ.
"""
from __future__ import annotations

import streamlit as st

from tra_cuu_gtdb.api.trinh_bay import TEN_LOAI, tom_tat
from tra_cuu_gtdb.api.trinh_bay import the_ket_qua as gom_the

VI_DU = [
    "Vượt đèn đỏ xe máy phạt bao nhiêu?",
    "Nồng độ cồn 0,3 mg/l phạt thế nào?",
    "Xe cơ giới là gì?",
    "Lỗi nào bị trừ 10 điểm giấy phép lái xe?",
    "Điều 6 khoản 9 điểm a Nghị định 168/2024/NĐ-CP nói về lỗi gì?",
    "Tôi vừa vượt đèn đỏ vừa không có giấy phép lái xe thì bị phạt bao nhiêu?",
]

MAU_TIN_CAY = {"cao": "🟢", "trung bình": "🟡", "thấp": "🔴"}


@st.cache_resource(show_spinner="Đang nạp cơ sở tri thức…")
def nap_he_thong():
    """Nạp một lần cho cả phiên — dựng chỉ mục TF-IDF mất vài giây."""
    from tra_cuu_gtdb.reasoning.engine import TraCuuPhapLuat

    return TraCuuPhapLuat()


def ve_the(t) -> None:
    nhan = TEN_LOAI.get(t.loai, t.loai)
    if t.bo_sung:
        nhan += " · tri thức bổ sung"
    with st.container(border=True):
        st.markdown(f"**{t.tieu_de}**")
        st.caption(f"{MAU_TIN_CAY.get(t.muc_tin_cay, '')} {nhan}"
                   + (f" · độ tin cậy {t.muc_tin_cay}" if t.diem is not None else ""))
        for d in t.dong:
            st.markdown(f"- {d}")
        if t.can_cu:
            st.caption(f"Căn cứ: {t.can_cu}")


def main() -> None:
    st.set_page_config(page_title="Tra cứu pháp luật giao thông đường bộ",
                       page_icon="⚖️", layout="centered")
    st.title("Tra cứu pháp luật giao thông đường bộ")
    st.caption("CS106 · Đề tài 4 · Nhóm 7 — tri thức từ Luật 36/2024/QH15 và "
               "Nghị định 168/2024/NĐ-CP, bản hợp nhất tới 2026")

    ht = nap_he_thong()

    if "truy_van" not in st.session_state:
        st.session_state.truy_van = VI_DU[0]

    st.markdown("**Câu hỏi ví dụ**")
    cot = st.columns(2)
    for i, vd in enumerate(VI_DU):
        if cot[i % 2].button(vd, key=f"vd_{i}", use_container_width=True):
            st.session_state.truy_van = vd

    truy_van = st.text_input("Câu hỏi", key="truy_van",
                             placeholder="Ví dụ: không đội mũ bảo hiểm phạt bao nhiêu?")
    top_k = st.slider("Số kết quả mỗi loại", 1, 10, 5, key="top_k")

    if not truy_van.strip():
        st.info("Nhập câu hỏi hoặc bấm một ví dụ ở trên.")
        return

    kq = ht.hoi(truy_van, top_k=top_k)
    st.divider()

    if kq["khong_tim_thay"]:
        st.warning(tom_tat(kq))
        return

    st.success(tom_tat(kq))
    for t in gom_the(kq):
        ve_the(t)

    if kq.get("lien_quan"):
        st.markdown("**Kiến thức liên quan**")
        st.markdown("\n".join(
            f"- {g['ten']} ({g['so_quy_dinh']} quy định)" for g in kq["lien_quan"]))

    with st.expander("Chi tiết phân tích truy vấn"):
        st.json({k: v for k, v in kq["phan_tich"].items() if k != "keyphrase"})


if __name__ == "__main__":
    main()
