"""Billing check: single lookup + bulk cross-check MMS vs 1C."""
import json
import time
import pandas as pd
import streamlit as st

from aqyl_console.core import billing, session

st.set_page_config(page_title="Проверка в Billing", page_icon="🔎", layout="wide")
st.title("🔎 Проверка в Billing (1С)")

session.render_cookie_sidebar()

tab1, tab2 = st.tabs(["Одиночная проверка", "Массовая сверка"])

with tab1:
    st.markdown("Что реально стоит на лицевом счёте в 1С.")
    account = st.text_input("Лицевой счёт (ЛС)")
    nomer = st.text_input("Счётчик (ПУ), опционально, для статуса")
    if st.button("Проверить", type="primary"):
        if account:
            code, body = billing.client_data(account.strip())
            st.write(f"**mmsclientdata** → HTTP {code}")
            try:
                data = json.loads(body)
                if isinstance(data, list) and data:
                    item = data[0]
                    st.json(item)
                    st.info(f"На ЛС стоит: **{item.get('nomerPU','нет')}** "
                            f"({item.get('modelPU','')}, {item.get('proizvoditelPU','')})")
                else:
                    st.warning("На ЛС нет привязанного ПУ в 1С.")
            except Exception:
                st.code(body[:500])
        if nomer:
            code, body = billing.check_meter_status(account.strip(), nomer.strip())
            st.write(f"**mmscheckmeterstatus** → HTTP {code}")
            try:
                st.json(json.loads(body))
            except Exception:
                st.code(body[:500])

with tab2:
    st.markdown("Загрузи файл со столбцами `ЛС` (account) и `ПУ ожидаемый` (device_no). "
                "Сверю с фактическим ПУ в 1С.")
    up = st.file_uploader("Файл сверки", type=["xlsx", "csv"], key="crosscheck")
    if up:
        raw = pd.read_excel(up, dtype=str) if up.name.endswith("xlsx") else pd.read_csv(up, dtype=str)
        raw.columns = [c.strip() for c in raw.columns]
        ls_col = st.selectbox("Столбец ЛС", raw.columns)
        pu_col = st.selectbox("Столбец ожидаемого ПУ", raw.columns)
        delay = st.number_input("Задержка (сек)", 0.1, 2.0, 0.2, 0.1)
        if st.button("Сверить", type="primary"):
            progress = st.progress(0.0)
            out = []
            total = len(raw)
            for i in range(1, total + 1):
                ls = str(raw.iloc[i-1][ls_col]).strip()
                exp = str(raw.iloc[i-1][pu_col]).strip()
                code, body = billing.client_data(ls)
                actual, model, verdict = "", "", "?"
                try:
                    d = json.loads(body)
                    if isinstance(d, list) and d:
                        actual = str(d[0].get("nomerPU", "")).strip()
                        model = d[0].get("modelPU", "")
                        verdict = "СОВПАДАЕТ" if actual == exp else "НЕ СОВПАДАЕТ"
                    else:
                        verdict = "НЕТ ПУ НА ЛС"
                except Exception:
                    verdict = f"ERR {code}"
                out.append({"ЛС": ls, "Ожидали": exp, "Факт в 1С": actual,
                            "Модель": model, "Итог": verdict})
                progress.progress(i / total)
                time.sleep(delay)
            res = pd.DataFrame(out)
            match = (res["Итог"] == "СОВПАДАЕТ").sum()
            st.success(f"Совпало: {match} / {len(res)}")
            st.dataframe(res, use_container_width=True, height=400)
            st.download_button("⬇ Скачать результат", res.to_csv(index=False).encode(),
                               file_name="crosscheck.csv", mime="text/csv")
