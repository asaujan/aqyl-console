"""Billing check: single lookup + bulk cross-check MMS vs 1C."""
import json
import time
import pandas as pd
import streamlit as st

from aqyl_console.core import billing
from aqyl_console.core.i18n import t

st.title(f"🔎 {t('page3_title')}")

tab1, tab2 = st.tabs([t("tab_single_check"), t("tab_bulk_check")])

with tab1:
    st.markdown(t("billing_intro"))
    account = st.text_input(t("account_label"))
    nomer = st.text_input(t("nomer_label"))
    if st.button(t("btn_check"), type="primary"):
        if account:
            code, body = billing.client_data(account.strip())
            st.write(f"**mmsclientdata** → HTTP {code}")
            try:
                data = json.loads(body)
                if isinstance(data, list) and data:
                    item = data[0]
                    st.json(item)
                    st.info(t(
                        "on_account_info",
                        pu=item.get("nomerPU", t("no_value")),
                        model=item.get("modelPU", ""),
                        maker=item.get("proizvoditelPU", ""),
                    ))
                else:
                    st.warning(t("no_pu_on_account"))
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
    st.markdown(t("crosscheck_intro"))
    up = st.file_uploader(t("crosscheck_file"), type=["xlsx", "csv"], key="crosscheck")
    if up:
        raw = pd.read_excel(up, dtype=str) if up.name.endswith("xlsx") else pd.read_csv(up, dtype=str)
        raw.columns = [c.strip() for c in raw.columns]
        ls_col = st.selectbox(t("ls_col_label"), raw.columns)
        pu_col = st.selectbox(t("pu_col_label"), raw.columns)
        delay = st.number_input(t("delay_short"), 0.1, 2.0, 0.2, 0.1)
        if st.button(t("btn_crosscheck"), type="primary"):
            col_ls = t("col_ls")
            col_expected = t("col_expected")
            col_actual = t("col_actual_1c")
            col_model = t("col_model")
            col_verdict = t("col_verdict")
            v_match = t("verdict_match")
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
                        verdict = v_match if actual == exp else t("verdict_mismatch")
                    else:
                        verdict = t("verdict_no_pu")
                except Exception:
                    verdict = f"ERR {code}"
                out.append({col_ls: ls, col_expected: exp, col_actual: actual,
                            col_model: model, col_verdict: verdict})
                progress.progress(i / total)
                time.sleep(delay)
            res = pd.DataFrame(out)
            match = (res[col_verdict] == v_match).sum()
            st.success(t("matched_n", m=match, n=len(res)))
            st.dataframe(res, use_container_width=True, height=400)
            st.download_button(t("download_result"), res.to_csv(index=False).encode(),
                               file_name="crosscheck.csv", mime="text/csv")
