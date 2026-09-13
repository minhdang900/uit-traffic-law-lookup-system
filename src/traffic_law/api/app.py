"""Giao diện tra cứu — vỏ Streamlit.

Chạy:
    pip install -e '.[ui]'
    streamlit run src/traffic_law/api/app.py

Tệp này CỐ Ý mỏng: mọi thứ có thể sai (định dạng tiền, gom kết quả, xếp mức
tin cậy) nằm ở ``trinh_bay.py`` và được kiểm thử ở ``tests/test_trinh_bay.py``.
Ở đây chỉ có lệnh vẽ. ``tests/test_giao_dien.py`` canh cho ranh giới đó không
rữa, và canh cho mọi câu hỏi ví dụ đều thật sự trả lời được.
"""
from __future__ import annotations

import streamlit as st

from traffic_law.api.presentation import KIND_NAMES, Card, result_cards, summary_line

#: Chọn sao cho phủ nhiều lớp bài toán khác nhau — bấm nút mà cả sáu ra cùng
#: một kiểu trả lời thì không cho thấy hệ thống làm được gì.
EXAMPLES = [
    "Vượt đèn đỏ xe máy phạt bao nhiêu?",
    "Xe cơ giới là gì?",
    "Nồng độ cồn 0,3 mg/l phạt thế nào?",
    "Lỗi nào bị trừ 10 điểm giấy phép lái xe?",
    "Điều 6 khoản 9 điểm a Nghị định 168/2024/NĐ-CP nói về lỗi gì?",
    "Tôi vừa vượt đèn đỏ vừa không có giấy phép lái xe thì bị phạt bao nhiêu?",
]

BADGES = {"cao": "🟢", "trung bình": "🟡", "thấp": "🔴"}


@st.cache_resource(show_spinner="Đang nạp cơ sở tri thức…")
def load_system():
    """Nạp một lần cho cả phiên — dựng chỉ mục TF-IDF mất vài giây."""
    from traffic_law.reasoning.engine import LawLookup

    return LawLookup()


def draw_card(t: Card) -> None:
    nhan = KIND_NAMES.get(t.kind, t.kind)
    if t.supplementary:
        nhan += " · tri thức bổ sung"
    with st.container(border=True):
        st.markdown(f"**{t.tieu_de}**")
        st.caption(f"{BADGES.get(t.confidence, '')} {nhan}"
                   + (f" · độ tin cậy {t.confidence}" if t.point is not None else ""))
        for d in t.lines:
            st.markdown(f"- {d}")
        if t.citation:
            st.caption(f"Căn cứ: {t.citation}")


def draw_examples() -> None:
    st.markdown("**Câu hỏi ví dụ**")
    cols = st.columns(2)
    for i, vd in enumerate(EXAMPLES):
        if cols[i % 2].button(vd, key=f"vd_{i}", use_container_width=True):
            st.session_state.query = vd


def draw_results(kq: dict) -> None:
    if kq["not_found"]:
        st.warning(summary_line(kq))
        return
    st.success(summary_line(kq))
    for t in result_cards(kq):
        draw_card(t)
    if kq.get("related"):
        st.markdown("**Kiến thức liên quan**")
        st.markdown("\n".join(
            f"- {g['name']} ({g['so_quy_dinh']} quy định)" for g in kq["related"]))
    with st.expander("Chi tiết phân tích truy vấn"):
        st.json({k: v for k, v in kq["analysis"].items() if k != "keyphrase"})


def main() -> None:
    st.set_page_config(page_title="Tra cứu pháp luật giao thông đường bộ",
                       page_icon="⚖️", layout="centered")
    st.title("Tra cứu pháp luật giao thông đường bộ")
    st.caption("CS106 · Đề tài 4 · Nhóm 7 — tri thức từ Luật 36/2024/QH15 và "
               "Nghị định 168/2024/NĐ-CP, bản hợp nhất tới 2026")

    ht = load_system()
    st.session_state.setdefault("query", EXAMPLES[0])
    draw_examples()

    query = st.text_input("Câu hỏi", key="query",
                             placeholder="Ví dụ: không đội mũ bảo hiểm phạt bao nhiêu?")
    top_k = st.slider("Số kết quả mỗi loại", 1, 10, 5, key="top_k")

    st.divider()
    if query.strip():
        draw_results(ht.ask(query, top_k=top_k))
    else:
        st.info("Nhập câu hỏi hoặc bấm một ví dụ ở trên.")


if __name__ == "__main__":
    main()
