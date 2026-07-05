from __future__ import annotations

"""
Feature parser.

Converts a CICFlowMeter flow data dict (from Flow.get_data()) into
the exact 82-column numeric feature vector expected by the KServe model.
"""

from decimal import Decimal
import math


MODEL_FEATURES: tuple[tuple[str, str | None], ...] = (
    ("Src Port", "src_port"),
    ("Dst Port", "dst_port"),
    ("Protocol", "protocol"),
    ("Flow Duration", "flow_duration"),
    ("Total Fwd Packet", "tot_fwd_pkts"),
    ("Total Bwd packets", "tot_bwd_pkts"),
    ("Total Length of Fwd Packet", "totlen_fwd_pkts"),
    ("Total Length of Bwd Packet", "totlen_bwd_pkts"),
    ("Fwd Packet Length Max", "fwd_pkt_len_max"),
    ("Fwd Packet Length Min", "fwd_pkt_len_min"),
    ("Fwd Packet Length Mean", "fwd_pkt_len_mean"),
    ("Fwd Packet Length Std", "fwd_pkt_len_std"),
    ("Bwd Packet Length Max", "bwd_pkt_len_max"),
    ("Bwd Packet Length Min", "bwd_pkt_len_min"),
    ("Bwd Packet Length Mean", "bwd_pkt_len_mean"),
    ("Bwd Packet Length Std", "bwd_pkt_len_std"),
    ("Flow Bytes/s", "flow_byts_s"),
    ("Flow Packets/s", "flow_pkts_s"),
    ("Flow IAT Mean", "flow_iat_mean"),
    ("Flow IAT Std", "flow_iat_std"),
    ("Flow IAT Max", "flow_iat_max"),
    ("Flow IAT Min", "flow_iat_min"),
    ("Fwd IAT Total", "fwd_iat_tot"),
    ("Fwd IAT Mean", "fwd_iat_mean"),
    ("Fwd IAT Std", "fwd_iat_std"),
    ("Fwd IAT Max", "fwd_iat_max"),
    ("Fwd IAT Min", "fwd_iat_min"),
    ("Bwd IAT Total", "bwd_iat_tot"),
    ("Bwd IAT Mean", "bwd_iat_mean"),
    ("Bwd IAT Std", "bwd_iat_std"),
    ("Bwd IAT Max", "bwd_iat_max"),
    ("Bwd IAT Min", "bwd_iat_min"),
    ("Fwd PSH Flags", "fwd_psh_flags"),
    ("Bwd PSH Flags", "bwd_psh_flags"),
    ("Fwd URG Flags", "fwd_urg_flags"),
    ("Bwd URG Flags", "bwd_urg_flags"),
    ("Fwd RST Flags", None),
    ("Bwd RST Flags", None),
    ("Fwd Header Length", "fwd_header_len"),
    ("Bwd Header Length", "bwd_header_len"),
    ("Fwd Packets/s", "fwd_pkts_s"),
    ("Bwd Packets/s", "bwd_pkts_s"),
    ("Packet Length Min", "pkt_len_min"),
    ("Packet Length Max", "pkt_len_max"),
    ("Packet Length Mean", "pkt_len_mean"),
    ("Packet Length Std", "pkt_len_std"),
    ("Packet Length Variance", "pkt_len_var"),
    ("FIN Flag Count", "fin_flag_cnt"),
    ("SYN Flag Count", "syn_flag_cnt"),
    ("RST Flag Count", "rst_flag_cnt"),
    ("PSH Flag Count", "psh_flag_cnt"),
    ("ACK Flag Count", "ack_flag_cnt"),
    ("URG Flag Count", "urg_flag_cnt"),
    ("CWR Flag Count", "cwe_flag_count"),
    ("ECE Flag Count", "ece_flag_cnt"),
    ("Down/Up Ratio", "down_up_ratio"),
    ("Average Packet Size", "pkt_size_avg"),
    ("Fwd Segment Size Avg", "fwd_seg_size_avg"),
    ("Bwd Segment Size Avg", "bwd_seg_size_avg"),
    ("Fwd Bytes/Bulk Avg", "fwd_byts_b_avg"),
    ("Fwd Packet/Bulk Avg", "fwd_pkts_b_avg"),
    ("Fwd Bulk Rate Avg", "fwd_blk_rate_avg"),
    ("Bwd Bytes/Bulk Avg", "bwd_byts_b_avg"),
    ("Bwd Packet/Bulk Avg", "bwd_pkts_b_avg"),
    ("Bwd Bulk Rate Avg", "bwd_blk_rate_avg"),
    ("Subflow Fwd Packets", "subflow_fwd_pkts"),
    ("Subflow Fwd Bytes", "subflow_fwd_byts"),
    ("Subflow Bwd Packets", "subflow_bwd_pkts"),
    ("Subflow Bwd Bytes", "subflow_bwd_byts"),
    ("FWD Init Win Bytes", "init_fwd_win_byts"),
    ("Bwd Init Win Bytes", "init_bwd_win_byts"),
    ("Fwd Act Data Pkts", "fwd_act_data_pkts"),
    ("Fwd Seg Size Min", "fwd_seg_size_min"),
    ("Active Mean", "active_mean"),
    ("Active Std", "active_std"),
    ("Active Max", "active_max"),
    ("Active Min", "active_min"),
    ("Idle Mean", "idle_mean"),
    ("Idle Std", "idle_std"),
    ("Idle Max", "idle_max"),
    ("Idle Min", "idle_min"),
    ("Total TCP Flow Time", "total_tcp_flow_time"),
)


def _to_float(value) -> float:
    try:
        if isinstance(value, Decimal):
            result = float(value)
        else:
            result = float(value)
    except (ValueError, TypeError):
        return 0.0

    if math.isinf(result) or math.isnan(result):
        return 0.0
    return result


def parse_features(row: dict) -> list[float] | None:
    """
    Convert a CICFlowMeter flow data dict into a feature vector.

    Uses the same column order as /app/feature_columns.json in the
    ai-threat-detector predictor image.

    Parameters
    ----------
    row : dict
        Column-name -> value mapping from Flow.get_data().
        Values may be int, float, Decimal, or str.

    Returns
    -------
    list[float] | None
        The numeric feature vector (82 elements).
    """
    if not row:
        print("[WARN] Empty flow row received", flush=True)
        return None

    enriched_row = dict(row)
    if _to_float(enriched_row.get("protocol")) == 6.0:
        enriched_row["total_tcp_flow_time"] = enriched_row.get("flow_duration", 0.0)
    else:
        enriched_row["total_tcp_flow_time"] = 0.0

    return [
        0.0 if source_key is None else _to_float(enriched_row.get(source_key))
        for _, source_key in MODEL_FEATURES
    ]
