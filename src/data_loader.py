import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data
def process_data(file_input):
    df = pd.read_csv(file_input, thousands=",")
    df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]

    def _clean_num(series):
        if series.dtype == object or str(series.dtype).startswith("str"):
            return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False).str.strip(), errors="coerce")
        return pd.to_numeric(series, errors="coerce")

    alias_map = {
        "DateTime": ["DateTime", "Thời gian", "Time", "timestamp", "Date", "Ngày"],
        "Hour": ["Giờ", "Hour", "hour"],
        "Site Name": ["Site Name", "Site", "Tên Site", "eNodeB Name", "eNodeB", "NodeB Name"],
        "Tên đối tượng": ["Tên đối tượng", "Cell Name", "Cell", "Tên Cell", "Object Name", "CellId"],
        "Total Data Traffic Volume (GB)": ["Total Data Traffic Volume (GB)", "Total Data Traffic (GB)", "Data Traffic (GB)", "Total Traffic (GB)", "Traffic (GB)", "Traffic_GB"],
        "Traffic Volumn DL (GB)": ["Traffic Volumn DL (GB)", "Traffic Volume DL (GB)", "DL Traffic (GB)", "Data Traffic DL (GB)", "Traffic DL (GB)"],
        "Traffic Volume UL (GB)": ["Traffic Volume UL (GB)", "Traffic Volumn UL (GB)", "UL Traffic (GB)", "Data Traffic UL (GB)", "Traffic UL (GB)"],
        "Resource Block Untilizing Rate Downlink (%)": [
            "Resource Block Untilizing Rate Downlink (%)", "Resource Block Utilizing Rate Downlink (%)",
            "PRB Utilization DL (%)", "PRB DL Utilization (%)", "Resource Block Utilization Rate Downlink (%)",
            "PRB Utilization Downlink (%)", "DL PRB Utilization (%)", "PRB DL (%)", "DL PRB Utilization Rate (%)"
        ],
        "CQI_4G": ["CQI_4G", "CQI 4G Index (%)", "CQI Index", "CQI >= 7 (%)", "CQI 4G", "CQI"],
        "Call Setup Success Rate": ["Call Setup Success Rate", "CSSR (%)", "Call Setup Success Rate (%)", "CSSR"],
        "Service Drop (all service)": ["Service Drop (all service)", "Service Drop Rate (%)", "Service Drop Rate", "DCR (%)", "Call Drop Rate (%)", "Drop Rate (%)"],
        "Intra-frequency HO (%)": ["Intra-frequency HO (%)", "Intra-freq HO SR (%)", "Intra HO (%)", "Intra-frequency HO Success Rate (%)"],
        "Inter-frequency HO (%)": ["Inter-frequency HO (%)", "Inter-freq HO SR (%)", "Inter HO (%)", "Inter-frequency HO Success Rate (%)"],
        "Inter-RAT HOSR (LTE to WCDMA) (%)": ["Inter-RAT HOSR (LTE to WCDMA) (%)", "Inter-RAT HOSR (%)", "IRAT HO (%)"],
        "SRVCC Success Rate (LTE to WCDMA)": ["SRVCC Success Rate (LTE to WCDMA)", "SRVCC Success Rate (%)", "SRVCC SR (%)"],
        "Call Drop Rate (VoLTE)": ["Call Drop Rate (VoLTE)", "VoLTE Drop Rate (%)", "VoLTE DCR (%)"],
        "VoLTE E-RAB Call Setup Success Rate": ["VoLTE E-RAB Call Setup Success Rate", "VoLTE CSSR (%)", "VoLTE Call Setup Success Rate (%)"],
        "VoLTE Traffic (Erl)": ["VoLTE Traffic (Erl)", "VoLTE Traffic"]
    }

    for std_col, aliases in alias_map.items():
        if std_col not in df.columns:
            for alias in aliases:
                if alias in df.columns:
                    df.rename(columns={alias: std_col}, inplace=True)
                    break

    # Quy đổi Throughput Kbps -> Mbps
    dl_kbps_cols = ["User Downlink Average Throughput (Kbps)", "User Downlink Average Throughput(Kbps)", "User Downlink Throughput (Kbps)", "User DL Throughput (Kbps)", "DL Throughput (Kbps)", "DL_Throughput_Kbps"]
    ul_kbps_cols = ["User Uplink Average Throughput (Kbps)", "User Uplink Average Throughput(Kbps)", "User Uplink Throughput (Kbps)", "User UL Throughput (Kbps)", "UL Throughput (Kbps)", "UL_Throughput_Kbps"]

    found_dl_kbps = next((c for c in dl_kbps_cols if c in df.columns), None)
    if found_dl_kbps:
        df["User Downlink Average Throughput (Kbps)"] = _clean_num(df[found_dl_kbps])
        df["DL_Throughput_Mbps"] = df["User Downlink Average Throughput (Kbps)"] / 1000.0
    else:
        dl_mbps_cols = ["DL_Throughput_Mbps", "User Downlink Average Throughput (Mbps)", "DL Throughput (Mbps)", "User DL Throughput (Mbps)"]
        found_dl_mbps = next((c for c in dl_mbps_cols if c in df.columns), None)
        if found_dl_mbps:
            df["DL_Throughput_Mbps"] = _clean_num(df[found_dl_mbps])
            df["User Downlink Average Throughput (Kbps)"] = df["DL_Throughput_Mbps"] * 1000.0

    found_ul_kbps = next((c for c in ul_kbps_cols if c in df.columns), None)
    if found_ul_kbps:
        df["User Uplink Average Throughput (Kbps)"] = _clean_num(df[found_ul_kbps])
        df["UL_Throughput_Mbps"] = df["User Uplink Average Throughput (Kbps)"] / 1000.0
    else:
        ul_mbps_cols = ["UL_Throughput_Mbps", "User Uplink Average Throughput (Mbps)", "UL Throughput (Mbps)", "User UL Throughput (Mbps)"]
        found_ul_mbps = next((c for c in ul_mbps_cols if c in df.columns), None)
        if found_ul_mbps:
            df["UL_Throughput_Mbps"] = _clean_num(df[found_ul_mbps])
            df["User Uplink Average Throughput (Kbps)"] = df["UL_Throughput_Mbps"] * 1000.0

    # Parse DateTime & Hour
    has_hour_col = "Hour" in df.columns
    has_hour = False

    if "DateTime" in df.columns:
        df["DateTime"] = pd.to_datetime(df["DateTime"], dayfirst=True, errors="coerce").fillna(pd.Timestamp.now())
        dt_has_time = bool(((df["DateTime"].dt.hour != 0) | (df["DateTime"].dt.minute != 0)).any())

        if has_hour_col:
            hr = pd.to_numeric(df["Hour"].astype(str).str.extract(r"(\d{1,2})")[0], errors="coerce")
            if hr.notnull().any():
                df["Hour"] = hr.fillna(0).astype(int)
                if not dt_has_time:
                    df["DateTime"] = df["DateTime"].dt.normalize() + pd.to_timedelta(df["Hour"], unit="h")
                has_hour = True
            else:
                df["Hour"] = df["DateTime"].dt.hour
                has_hour = dt_has_time
        else:
            df["Hour"] = df["DateTime"].dt.hour
            has_hour = dt_has_time

        df["Date"] = df["DateTime"].dt.date
    else:
        df["DateTime"] = pd.Timestamp.now()
        df["Date"] = df["DateTime"].dt.date
        df["Hour"] = 0

    df["_has_hour_col"] = has_hour

    # Freqband & Cell Type
    cell_col_name = "Tên đối tượng" if "Tên đối tượng" in df.columns else ("Cell Name" if "Cell Name" in df.columns else None)
    if cell_col_name and cell_col_name in df.columns:
        cell_s = df[cell_col_name].astype(str).str.strip()
        is_moran = cell_s.str.upper().str.startswith("VNP-")
        core = cell_s.where(~is_moran, cell_s.str[4:])
        df["Freqband"] = ("F" + core.str[10]).fillna("N/A")
        df["Cell Type"] = np.where(is_moran, "MORAN", "VNP")

    num_cols = [
        "User Downlink Average Throughput (Kbps)", "User Uplink Average Throughput (Kbps)",
        "DL_Throughput_Mbps", "UL_Throughput_Mbps", "CQI_4G", "Call Setup Success Rate",
        "Service Drop (all service)", "Resource Block Untilizing Rate Downlink (%)",
        "Total Data Traffic Volume (GB)", "Traffic Volumn DL (GB)", "Traffic Volume UL (GB)",
        "Intra-frequency HO (%)", "Inter-frequency HO (%)", "Inter-RAT HOSR (LTE to WCDMA) (%)",
        "SRVCC Success Rate (LTE to WCDMA)", "Call Drop Rate (VoLTE)",
        "VoLTE E-RAB Call Setup Success Rate", "VoLTE Traffic (Erl)",
    ]

    for col in num_cols:
        if col in df.columns:
            df[col] = _clean_num(df[col])

    return df


def aggregate_kpis(df_in, group_cols):
    """Gom nhóm + trung bình có trọng số theo Traffic (vectorized)."""
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    group_cols = list(group_cols)

    TOT, DLT, ULT, VOL = 'Total Data Traffic Volume (GB)', 'Traffic Volumn DL (GB)', 'Traffic Volume UL (GB)', 'VoLTE Traffic (Erl)'
    cols = df_in.columns

    nan_s = pd.Series(np.nan, index=df_in.index)
    tot = df_in[TOT] if TOT in cols else nan_s
    tmp = {'_tot': tot}
    mean_cols = {}
    spec = {'_tot': 'sum'}

    def add_weighted(key, x, weights):
        for i, w in enumerate(weights):
            valid = x.notna() & w.notna()
            tmp[f'{key}__n{i}'] = (x * w).where(valid)
            tmp[f'{key}__d{i}'] = w.where(valid)
            spec[f'{key}__n{i}'] = 'sum'
            spec[f'{key}__d{i}'] = 'sum'
        mean_cols[f'{key}__m'] = x
        spec[f'{key}__m'] = 'mean'

    if DLT in cols: tmp['_dlt'] = df_in[DLT]; spec['_dlt'] = 'sum'
    if ULT in cols: tmp['_ult'] = df_in[ULT]; spec['_ult'] = 'sum'

    dl_weights = ([df_in[DLT]] if DLT in cols else []) + [tot]
    ul_weights = ([df_in[ULT]] if ULT in cols else []) + [tot]
    if 'DL_Throughput_Mbps' in cols: add_weighted('dl', df_in['DL_Throughput_Mbps'], dl_weights)
    if 'UL_Throughput_Mbps' in cols: add_weighted('ul', df_in['UL_Throughput_Mbps'], ul_weights)

    quality_kpis = [k for k in ['Call Setup Success Rate', 'Service Drop (all service)', 'CQI_4G', 'Resource Block Untilizing Rate Downlink (%)'] if k in cols]
    for k in quality_kpis: add_weighted(f'q::{k}', df_in[k], [tot])

    mean_kpis = [k for k in ['Intra-frequency HO (%)', 'Inter-frequency HO (%)', 'Inter-RAT HOSR (LTE to WCDMA) (%)', 'SRVCC Success Rate (LTE to WCDMA)'] if k in cols]
    for k in mean_kpis: mean_cols[f'm::{k}'] = df_in[k]; spec[f'm::{k}'] = 'mean'

    volte_kpis = [k for k in ['VoLTE E-RAB Call Setup Success Rate', 'Call Drop Rate (VoLTE)'] if k in cols]
    if VOL in cols: tmp['_vol'] = df_in[VOL]; spec['_vol'] = 'sum'
    for k in volte_kpis:
        x = df_in[k]
        if VOL in cols:
            tmp[f'v::{k}__n'] = (x * df_in[VOL]).where(x.notna())
            spec[f'v::{k}__n'] = 'sum'
        mean_cols[f'v::{k}__m'] = x
        spec[f'v::{k}__m'] = 'mean'

    work = pd.concat([df_in[group_cols], pd.DataFrame(tmp), pd.DataFrame(mean_cols)], axis=1)
    agg = work.groupby(group_cols, sort=True).agg(spec)

    def wavg(key, n_weights):
        out = agg[f'{key}__m']
        for i in reversed(range(n_weights)):
            d = agg[f'{key}__d{i}']
            out = pd.Series(np.where(d > 0, agg[f'{key}__n{i}'] / d.where(d > 0), out), index=agg.index)
        return out

    res = pd.DataFrame(index=agg.index)
    res[TOT] = agg['_tot']
    if DLT in cols: res[DLT] = agg['_dlt']
    if ULT in cols: res[ULT] = agg['_ult']
    if 'DL_Throughput_Mbps' in cols: res['DL_Throughput_Mbps'] = wavg('dl', len(dl_weights))
    if 'UL_Throughput_Mbps' in cols: res['UL_Throughput_Mbps'] = wavg('ul', len(ul_weights))
    for k in quality_kpis: res[k] = wavg(f'q::{k}', 1)
    for k in mean_kpis: res[k] = agg[f'm::{k}']
    if VOL in cols: res[VOL] = agg['_vol']
    for k in volte_kpis:
        if VOL in cols:
            vt = agg['_vol']
            res[k] = pd.Series(np.where(vt > 0, agg[f'v::{k}__n'] / vt.where(vt > 0), agg[f'v::{k}__m']), index=agg.index).fillna(0.0)
        else:
            res[k] = agg[f'v::{k}__m'].fillna(0.0)

    return res.reset_index()


def calc_weighted_avg(df_in, kpi_col, weight_col=None):
    if kpi_col not in df_in.columns:
        return 0.0

    if weight_col is None:
        if kpi_col == "DL_Throughput_Mbps":
            weight_col = "Traffic Volumn DL (GB)" if "Traffic Volumn DL (GB)" in df_in.columns else "Total Data Traffic Volume (GB)"
        elif kpi_col == "UL_Throughput_Mbps":
            weight_col = "Traffic Volume UL (GB)" if "Traffic Volume UL (GB)" in df_in.columns else "Total Data Traffic Volume (GB)"
        else:
            weight_col = "Total Data Traffic Volume (GB)"

    if weight_col in df_in.columns:
        valid_mask = df_in[kpi_col].notnull() & df_in[weight_col].notnull() & (df_in[weight_col] > 0)
        df_valid = df_in[valid_mask]
        total_weight = df_valid[weight_col].sum()
        if total_weight > 0:
            return (df_valid[kpi_col] * df_valid[weight_col]).sum() / total_weight

    df_valid = df_in[df_in[kpi_col].notnull()]
    return df_valid[kpi_col].mean() if not df_valid.empty else 0.0
