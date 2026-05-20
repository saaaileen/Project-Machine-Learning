import sys
print("Script is using:", sys.executable)
"""
flow_extractor.py
=================
Generates 300+ columns per network flow from live traffic or a pcap file.
Matches the feature space of the BCCC-cPacket-Cloud-DDoS-2024 dataset.

HOW IT WORKS — the column explosion explained:
    Each "dimension" (fwd packets, bwd packets, IATs, header lengths, etc.)
    gets the SAME set of statistical functions applied to it:
        min, max, mean, std, variance, skewness, kurtosis, total, count, cv
    
    That alone gives you:
        10 functions × 12+ dimensions = 120+ columns
    
    Then add: flag counts, bulk stats, subflow stats, active/idle times,
    window sizes, rate features, SPLT sequences, ratios, L7 metadata.
    
    Grand total: ~310 columns.

USAGE:
    # Live capture (needs sudo/admin):
    sudo python flow_extractor.py --interface eth0 --duration 120 --output flows.csv

    # From a pcap file:
    python flow_extractor.py --pcap capture.pcap --output flows.csv
"""

import argparse
import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis as sp_kurtosis
from nfstream import NFStreamer, NFPlugin


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: safe statistical functions (handle empty/single-element arrays)
# ─────────────────────────────────────────────────────────────────────────────
def _safe(fn, arr, default=0.0):
    a = np.array(arr, dtype=float)
    if len(a) == 0:
        return default
    try:
        return float(fn(a))
    except Exception:
        return default


def _stats(arr):
    """
    Returns dict of 10 statistical measures for a list of numbers.
    This is the core function applied to EVERY dimension.
    """
    a = np.array(arr, dtype=float) if len(arr) > 0 else np.array([0.0])
    mean = float(a.mean())
    std  = float(a.std())
    return {
        "count":    float(len(arr)),
        "total":    float(a.sum()),
        "max":      float(a.max()),
        "min":      float(a.min()),
        "mean":     mean,
        "std":      std,
        "variance": float(np.var(a)),
        "skewness": float(skew(a)) if len(a) > 2 else 0.0,
        "kurtosis": float(sp_kurtosis(a)) if len(a) > 3 else 0.0,
        "cv":       std / mean if mean != 0 else 0.0,   # coefficient of variation
    }


def _prefixed(prefix, stat_dict):
    """Turns {'mean': 1.2} into {'fwd_pkt_len_mean': 1.2}"""
    return {f"{prefix}_{k}": v for k, v in stat_dict.items()}


# ─────────────────────────────────────────────────────────────────────────────
# PLUGIN 1 — Packet Lengths  (~60 cols)
# Dimensions: fwd, bwd, bidirectional — 10 stats each = 30
# Plus per-direction payload stats     — 10 stats each = 30 more
# ─────────────────────────────────────────────────────────────────────────────
class PacketLengthPlugin(NFPlugin):
    def on_init(self, packet, flow):
        flow.udps._fwd_pkt_lens     = []   # raw packet sizes fwd
        flow.udps._bwd_pkt_lens     = []   # raw packet sizes bwd
        flow.udps._fwd_payload_lens = []   # payload only (no IP/TCP header)
        flow.udps._bwd_payload_lens = []

    def on_update(self, packet, flow):
        size    = packet.raw_size
        payload = getattr(packet, "payload_size", 0) or 0

        if packet.direction == 0:
            flow.udps._fwd_pkt_lens.append(size)
            flow.udps._fwd_payload_lens.append(payload)
        else:
            flow.udps._bwd_pkt_lens.append(size)
            flow.udps._bwd_payload_lens.append(payload)

    def on_expire(self, flow):
        fwd = flow.udps._fwd_pkt_lens
        bwd = flow.udps._bwd_pkt_lens
        both = fwd + bwd

        # 10 stats × 3 directions = 30 cols
        for prefix, arr in [
            ("fwd_pkt_len",  fwd),
            ("bwd_pkt_len",  bwd),
            ("pkt_len",      both),
        ]:
            for k, v in _stats(arr).items():
                setattr(flow.udps, f"{prefix}_{k}", v)

        # 10 stats × 2 payload directions = 20 more cols
        for prefix, arr in [
            ("fwd_payload_len", flow.udps._fwd_payload_lens),
            ("bwd_payload_len", flow.udps._bwd_payload_lens),
        ]:
            for k, v in _stats(arr).items():
                setattr(flow.udps, f"{prefix}_{k}", v)

        # payload ratio (how much of each packet is actual data)
        total_bytes   = sum(both) or 1
        payload_bytes = sum(flow.udps._fwd_payload_lens + flow.udps._bwd_payload_lens)
        flow.udps.payload_bytes_total = float(payload_bytes)
        flow.udps.payload_ratio       = payload_bytes / total_bytes


# ─────────────────────────────────────────────────────────────────────────────
# PLUGIN 2 — Inter-Arrival Times  (~60 cols)
# Dimensions: flow IAT, fwd IAT, bwd IAT — 10 stats each = 30
# Plus: fwd IAT total, bwd IAT total, flow IAT total = 30 more
# ─────────────────────────────────────────────────────────────────────────────
class IATPlugin(NFPlugin):
    def on_init(self, packet, flow):
        flow.udps._all_ts  = [packet.time]
        flow.udps._fwd_ts  = [packet.time] if packet.direction == 0 else []
        flow.udps._bwd_ts  = [packet.time] if packet.direction == 1 else []

    def on_update(self, packet, flow):
        flow.udps._all_ts.append(packet.time)
        if packet.direction == 0:
            flow.udps._fwd_ts.append(packet.time)
        else:
            flow.udps._bwd_ts.append(packet.time)

    def _iats(self, ts_list):
        """Convert timestamps to inter-arrival times in milliseconds."""
        if len(ts_list) < 2:
            return [0.0]
        ts = np.array(ts_list)
        return list(np.diff(ts))   # already in ms from nfstream

    def on_expire(self, flow):
        flow_iats = self._iats(flow.udps._all_ts)
        fwd_iats  = self._iats(flow.udps._fwd_ts)
        bwd_iats  = self._iats(flow.udps._bwd_ts)

        # 10 stats × 3 dimensions = 30 cols
        for prefix, arr in [
            ("flow_iat", flow_iats),
            ("fwd_iat",  fwd_iats),
            ("bwd_iat",  bwd_iats),
        ]:
            for k, v in _stats(arr).items():
                setattr(flow.udps, f"{prefix}_{k}", v)

        # absolute total IAT per direction (used in rate calculations)
        flow.udps.fwd_iat_total = float(sum(fwd_iats))
        flow.udps.bwd_iat_total = float(sum(bwd_iats))
        flow.udps.flow_iat_total = float(sum(flow_iats))

        # store for other plugins
        flow.udps._flow_iats = flow_iats
        flow.udps._fwd_iats  = fwd_iats
        flow.udps._bwd_iats  = bwd_iats


# ─────────────────────────────────────────────────────────────────────────────
# PLUGIN 3 — TCP Flags  (~30 cols)
# Per-direction counts of each flag + ratio columns
# ─────────────────────────────────────────────────────────────────────────────
class TCPFlagsPlugin(NFPlugin):
    FLAGS = ["fin", "syn", "rst", "psh", "ack", "urg", "cwr", "ece"]

    def on_init(self, packet, flow):
        for f in self.FLAGS:
            setattr(flow.udps, f"fwd_{f}_cnt", 0)
            setattr(flow.udps, f"bwd_{f}_cnt", 0)
        flow.udps._fwd_flag_pkts = 0
        flow.udps._bwd_flag_pkts = 0

    def on_update(self, packet, flow):
        if packet.direction == 0:
            flow.udps._fwd_flag_pkts += 1
            for f in self.FLAGS:
                val = getattr(packet, f"{f}_flag", False) or \
                      getattr(packet, f, False) or \
                      getattr(packet, f"tcp_{f}", False)
                if val:
                    setattr(flow.udps, f"fwd_{f}_cnt",
                            getattr(flow.udps, f"fwd_{f}_cnt") + 1)
        else:
            flow.udps._bwd_flag_pkts += 1
            for f in self.FLAGS:
                val = getattr(packet, f"{f}_flag", False) or \
                      getattr(packet, f, False) or \
                      getattr(packet, f"tcp_{f}", False)
                if val:
                    setattr(flow.udps, f"bwd_{f}_cnt",
                            getattr(flow.udps, f"bwd_{f}_cnt") + 1)

    def on_expire(self, flow):
        total_pkts = max(flow.udps._fwd_flag_pkts + flow.udps._bwd_flag_pkts, 1)
        for f in self.FLAGS:
            fwd_cnt = getattr(flow.udps, f"fwd_{f}_cnt")
            bwd_cnt = getattr(flow.udps, f"bwd_{f}_cnt")
            # ratio of packets that had this flag set
            setattr(flow.udps, f"fwd_{f}_ratio", fwd_cnt / max(flow.udps._fwd_flag_pkts, 1))
            setattr(flow.udps, f"bwd_{f}_ratio", bwd_cnt / max(flow.udps._bwd_flag_pkts, 1))
            setattr(flow.udps, f"total_{f}_cnt", fwd_cnt + bwd_cnt)


# ─────────────────────────────────────────────────────────────────────────────
# PLUGIN 4 — Bulk Transfers  (~26 cols)
# A "bulk" = consecutive packets in same direction within 1 second
# Stats: count, total bytes, total pkts, duration, avg bytes, avg pkts,
#        avg dur, bytes/sec — per direction
# ─────────────────────────────────────────────────────────────────────────────
class BulkPlugin(NFPlugin):
    BULK_GAP = 1000  # ms — gap that ends a bulk

    def on_init(self, packet, flow):
        for d in ["fwd", "bwd"]:
            setattr(flow.udps, f"{d}_bulk_count",       0)
            setattr(flow.udps, f"{d}_bulk_total_bytes",  0)
            setattr(flow.udps, f"{d}_bulk_total_pkts",   0)
            setattr(flow.udps, f"{d}_bulk_total_dur_ms", 0.0)
            setattr(flow.udps, f"_{d}_bulk_cur_bytes",   0)
            setattr(flow.udps, f"_{d}_bulk_cur_pkts",    0)
            setattr(flow.udps, f"_{d}_bulk_start",       packet.time)
            setattr(flow.udps, f"_{d}_last_ts",          packet.time)

    def _update(self, packet, flow, d):
        last = getattr(flow.udps, f"_{d}_last_ts")
        gap  = packet.time - last

        if gap > self.BULK_GAP:
            cur_pkts = getattr(flow.udps, f"_{d}_bulk_cur_pkts")
            if cur_pkts > 0:
                # close the current bulk
                setattr(flow.udps, f"{d}_bulk_count",
                        getattr(flow.udps, f"{d}_bulk_count") + 1)
                setattr(flow.udps, f"{d}_bulk_total_bytes",
                        getattr(flow.udps, f"{d}_bulk_total_bytes") +
                        getattr(flow.udps, f"_{d}_bulk_cur_bytes"))
                setattr(flow.udps, f"{d}_bulk_total_pkts",
                        getattr(flow.udps, f"{d}_bulk_total_pkts") + cur_pkts)
                dur = last - getattr(flow.udps, f"_{d}_bulk_start")
                setattr(flow.udps, f"{d}_bulk_total_dur_ms",
                        getattr(flow.udps, f"{d}_bulk_total_dur_ms") + dur)
            # reset
            setattr(flow.udps, f"_{d}_bulk_cur_bytes", 0)
            setattr(flow.udps, f"_{d}_bulk_cur_pkts",  0)
            setattr(flow.udps, f"_{d}_bulk_start",     packet.time)

        setattr(flow.udps, f"_{d}_bulk_cur_bytes",
                getattr(flow.udps, f"_{d}_bulk_cur_bytes") + packet.raw_size)
        setattr(flow.udps, f"_{d}_bulk_cur_pkts",
                getattr(flow.udps, f"_{d}_bulk_cur_pkts") + 1)
        setattr(flow.udps, f"_{d}_last_ts", packet.time)

    def on_update(self, packet, flow):
        d = "fwd" if packet.direction == 0 else "bwd"
        self._update(packet, flow, d)

    def on_expire(self, flow):
        for d in ["fwd", "bwd"]:
            cnt  = getattr(flow.udps, f"{d}_bulk_count")
            byts = getattr(flow.udps, f"{d}_bulk_total_bytes")
            pkts = getattr(flow.udps, f"{d}_bulk_total_pkts")
            dur  = getattr(flow.udps, f"{d}_bulk_total_dur_ms")
            setattr(flow.udps, f"{d}_bulk_avg_bytes",
                    byts / cnt if cnt > 0 else 0.0)
            setattr(flow.udps, f"{d}_bulk_avg_pkts",
                    pkts / cnt if cnt > 0 else 0.0)
            setattr(flow.udps, f"{d}_bulk_avg_dur",
                    dur  / cnt if cnt > 0 else 0.0)
            setattr(flow.udps, f"{d}_bulk_bytes_per_sec",
                    byts / (dur / 1000) if dur > 0 else 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# PLUGIN 5 — Subflows  (~14 cols)
# A "subflow" = group of packets separated by >1s idle gap
# Stats: count, avg pkts, avg bytes, avg duration — per direction
# ─────────────────────────────────────────────────────────────────────────────
class SubflowPlugin(NFPlugin):
    IDLE_GAP = 1000  # ms

    def on_init(self, packet, flow):
        flow.udps.sf_fwd_count = 1
        flow.udps.sf_bwd_count = 0
        flow.udps._sf_last_ts  = packet.time
        # store per-subflow stats to aggregate later
        flow.udps._sf_fwd_pkts  = [0]
        flow.udps._sf_fwd_bytes = [0]
        flow.udps._sf_bwd_pkts  = []
        flow.udps._sf_bwd_bytes = []
        flow.udps._sf_fwd_durs  = []
        flow.udps._sf_bwd_durs  = []
        flow.udps._sf_fwd_start = packet.time
        flow.udps._sf_bwd_start = None

    def on_update(self, packet, flow):
        gap = packet.time - flow.udps._sf_last_ts
        if gap > self.IDLE_GAP:
            # start a new subflow
            if packet.direction == 0:
                flow.udps.sf_fwd_count += 1
                dur = flow.udps._sf_last_ts - (flow.udps._sf_fwd_start or flow.udps._sf_last_ts)
                flow.udps._sf_fwd_durs.append(dur)
                flow.udps._sf_fwd_pkts.append(0)
                flow.udps._sf_fwd_bytes.append(0)
                flow.udps._sf_fwd_start = packet.time
            else:
                flow.udps.sf_bwd_count += 1
                dur = flow.udps._sf_last_ts - (flow.udps._sf_bwd_start or flow.udps._sf_last_ts)
                flow.udps._sf_bwd_durs.append(dur)
                flow.udps._sf_bwd_pkts.append(0)
                flow.udps._sf_bwd_bytes.append(0)
                flow.udps._sf_bwd_start = packet.time

        if packet.direction == 0:
            flow.udps._sf_fwd_pkts[-1]  += 1
            flow.udps._sf_fwd_bytes[-1] += packet.raw_size
        else:
            if not flow.udps._sf_bwd_pkts:
                flow.udps._sf_bwd_pkts.append(0)
                flow.udps._sf_bwd_bytes.append(0)
                flow.udps.sf_bwd_count = 1
                flow.udps._sf_bwd_start = packet.time
            flow.udps._sf_bwd_pkts[-1]  += 1
            flow.udps._sf_bwd_bytes[-1] += packet.raw_size

        flow.udps._sf_last_ts = packet.time

    def on_expire(self, flow):
        for d, plist, blist, dlist in [
            ("fwd", flow.udps._sf_fwd_pkts,
                    flow.udps._sf_fwd_bytes,
                    flow.udps._sf_fwd_durs),
            ("bwd", flow.udps._sf_bwd_pkts,
                    flow.udps._sf_bwd_bytes,
                    flow.udps._sf_bwd_durs),
        ]:
            p = np.array(plist) if plist else np.array([0.0])
            b = np.array(blist) if blist else np.array([0.0])
            dr = np.array(dlist) if dlist else np.array([0.0])
            setattr(flow.udps, f"sf_{d}_avg_pkts",  float(p.mean()))
            setattr(flow.udps, f"sf_{d}_avg_bytes", float(b.mean()))
            setattr(flow.udps, f"sf_{d}_avg_dur",   float(dr.mean()))
            setattr(flow.udps, f"sf_{d}_total_pkts",  float(p.sum()))
            setattr(flow.udps, f"sf_{d}_total_bytes", float(b.sum()))


# ─────────────────────────────────────────────────────────────────────────────
# PLUGIN 6 — Active / Idle Periods  (~20 cols)
# Active = time window with packets; Idle = gap between active windows
# 10 stats each = 20 cols
# ─────────────────────────────────────────────────────────────────────────────
class ActiveIdlePlugin(NFPlugin):
    IDLE_THRESHOLD = 1000  # ms — gap that ends an active period

    def on_init(self, packet, flow):
        flow.udps._act_start  = packet.time
        flow.udps._last_ts    = packet.time
        flow.udps._act_list   = []
        flow.udps._idle_list  = []

    def on_update(self, packet, flow):
        gap = packet.time - flow.udps._last_ts
        if gap > self.IDLE_THRESHOLD:
            act_dur = flow.udps._last_ts - flow.udps._act_start
            if act_dur > 0:
                flow.udps._act_list.append(act_dur)
            flow.udps._idle_list.append(gap)
            flow.udps._act_start = packet.time
        flow.udps._last_ts = packet.time

    def on_expire(self, flow):
        # close final active window
        final = flow.udps._last_ts - flow.udps._act_start
        if final > 0:
            flow.udps._act_list.append(final)

        # 10 stats for active times
        for k, v in _stats(flow.udps._act_list).items():
            setattr(flow.udps, f"active_{k}", v)

        # 10 stats for idle times
        for k, v in _stats(flow.udps._idle_list).items():
            setattr(flow.udps, f"idle_{k}", v)


# ─────────────────────────────────────────────────────────────────────────────
# PLUGIN 7 — Header Lengths  (~20 cols)
# Per-direction stats on IP+TCP header sizes
# ─────────────────────────────────────────────────────────────────────────────
class HeaderLengthPlugin(NFPlugin):
    def on_init(self, packet, flow):
        flow.udps._fwd_hdr_lens = []
        flow.udps._bwd_hdr_lens = []

    def on_update(self, packet, flow):
        raw     = packet.raw_size
        payload = getattr(packet, "payload_size", 0) or 0
        hdr     = max(raw - payload, 0)

        if packet.direction == 0:
            flow.udps._fwd_hdr_lens.append(hdr)
        else:
            flow.udps._bwd_hdr_lens.append(hdr)

    def on_expire(self, flow):
        # 10 stats × 2 directions = 20 cols
        for prefix, arr in [
            ("fwd_header_len", flow.udps._fwd_hdr_lens),
            ("bwd_header_len", flow.udps._bwd_hdr_lens),
        ]:
            for k, v in _stats(arr).items():
                setattr(flow.udps, f"{prefix}_{k}", v)

        # single summary values commonly used as standalone features
        flow.udps.fwd_header_len_total = float(sum(flow.udps._fwd_hdr_lens))
        flow.udps.bwd_header_len_total = float(sum(flow.udps._bwd_hdr_lens))


# ─────────────────────────────────────────────────────────────────────────────
# PLUGIN 8 — Window Size + Initial Window  (~14 cols)
# TCP window size statistics per direction
# ─────────────────────────────────────────────────────────────────────────────
class WindowPlugin(NFPlugin):
    def on_init(self, packet, flow):
        flow.udps._fwd_wins  = []
        flow.udps._bwd_wins  = []
        flow.udps.init_win_fwd = -1
        flow.udps.init_win_bwd = -1

    def on_update(self, packet, flow):
        win = getattr(packet, "tcp_window", None)
        if win is None:
            return
        if packet.direction == 0:
            flow.udps._fwd_wins.append(win)
            if flow.udps.init_win_fwd == -1:
                flow.udps.init_win_fwd = win
        else:
            flow.udps._bwd_wins.append(win)
            if flow.udps.init_win_bwd == -1:
                flow.udps.init_win_bwd = win

    def on_expire(self, flow):
        for prefix, arr in [
            ("fwd_win", flow.udps._fwd_wins),
            ("bwd_win", flow.udps._bwd_wins),
        ]:
            s = _stats(arr)
            # only store mean, std, max, min for window (4 × 2 = 8 cols)
            for k in ["mean", "std", "max", "min"]:
                setattr(flow.udps, f"{prefix}_{k}", s[k])


# ─────────────────────────────────────────────────────────────────────────────
# PLUGIN 9 — Flow Rates  (~16 cols)
# Bytes/sec and packets/sec computed over multiple time windows
# ─────────────────────────────────────────────────────────────────────────────
class FlowRatePlugin(NFPlugin):
    def on_init(self, packet, flow):
        flow.udps._fwd_bytes  = 0
        flow.udps._bwd_bytes  = 0
        flow.udps._fwd_pkts   = 0
        flow.udps._bwd_pkts   = 0
        flow.udps._start_ts   = packet.time

    def on_update(self, packet, flow):
        if packet.direction == 0:
            flow.udps._fwd_bytes += packet.raw_size
            flow.udps._fwd_pkts  += 1
        else:
            flow.udps._bwd_bytes += packet.raw_size
            flow.udps._bwd_pkts  += 1

    def on_expire(self, flow):
        dur_ms = max(flow.bidirectional_duration_ms, 1)
        dur_s  = dur_ms / 1000

        fb = flow.udps._fwd_bytes
        bb = flow.udps._bwd_bytes
        fp = flow.udps._fwd_pkts
        bp = flow.udps._bwd_pkts

        flow.udps.flow_bytes_per_s     = (fb + bb) / dur_s
        flow.udps.flow_pkts_per_s      = (fp + bp) / dur_s
        flow.udps.fwd_bytes_per_s      = fb / dur_s
        flow.udps.bwd_bytes_per_s      = bb / dur_s
        flow.udps.fwd_pkts_per_s       = fp / dur_s
        flow.udps.bwd_pkts_per_s       = bp / dur_s

        flow.udps.down_up_ratio        = bb / max(fb, 1)
        flow.udps.avg_pkt_size         = (fb + bb) / max(fp + bp, 1)
        flow.udps.fwd_avg_pkt_size     = fb / max(fp, 1)
        flow.udps.bwd_avg_pkt_size     = bb / max(bp, 1)
        flow.udps.fwd_bwd_bytes_ratio  = fb / max(fb + bb, 1)
        flow.udps.fwd_bwd_pkts_ratio   = fp / max(fp + bp, 1)

        # bytes per packet (another angle on pkt size)
        flow.udps.fwd_bytes_per_pkt    = fb / max(fp, 1)
        flow.udps.bwd_bytes_per_pkt    = bb / max(bp, 1)

        # act data pkts: fwd pkts with payload > 0
        flow.udps.fwd_act_data_pkts    = float(fp)
        flow.udps.bwd_act_data_pkts    = float(bp)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CAPTURE FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def capture(source: str, duration_seconds: int, output_csv: str):
    print(f"\n[*] Source       : {source}")
    print(f"[*] Duration     : {duration_seconds}s")
    print(f"[*] Output       : {output_csv}")
    print(f"[*] Waiting for traffic...\n")

    streamer = NFStreamer(
        source=source,
        # ── Core NFStream statistical features (~68 cols) ──
        statistical_analysis=True,      # min/mean/max/std of pkt sizes + IATs
        splt_analysis=10,               # first 10 pkt lengths + IATs per direction (~40 cols)
        n_dissections=20,               # L7 app name/category
        # ── Timeouts ──
        idle_timeout=15,
        active_timeout=duration_seconds,
        # ── Our custom plugins (each adds its own columns) ──
        udps=(
            PacketLengthPlugin()    # +62 cols
            ,IATPlugin()           # +33 cols
            ,TCPFlagsPlugin()      # +40 cols
            ,BulkPlugin()          # +26 cols
            ,SubflowPlugin()       # +14 cols
            ,ActiveIdlePlugin()    # +20 cols
            ,HeaderLengthPlugin()  # +22 cols
            ,WindowPlugin()        # +10 cols
            ,FlowRatePlugin()      # +20 cols
        ),
    )

    print("[*] Collecting flows (NFStream aggregates packets into flows internally)...")
    df = streamer.to_pandas()

    if df.empty:
        print("[!] No flows captured. Check interface name + permissions (sudo).")
        return None

    # ── Post-processing: clean up and add final derived columns ──
    df = df.replace([float("inf"), float("-inf")], 0).fillna(0)

    # Drop internal plugin state columns (prefixed with underscore after udps.)
    state_cols = [c for c in df.columns if "._" in c or c.endswith("_ts")]
    df = df.drop(columns=state_cols, errors="ignore")

    print(f"\n[+] Flows captured : {len(df)}")
    print(f"[+] Total columns  : {len(df.columns)}")

    # Print column count breakdown
    categories = {
        "NFStream base":       [c for c in df.columns if not c.startswith("udps.")],
        "Pkt length (plugin)": [c for c in df.columns if "pkt_len" in c],
        "IAT (plugin)":        [c for c in df.columns if "_iat_" in c],
        "TCP flags (plugin)":  [c for c in df.columns if any(f in c for f in ["fin","syn","rst","psh","ack","urg","cwr","ece"])],
        "Bulk (plugin)":       [c for c in df.columns if "bulk" in c],
        "Subflow (plugin)":    [c for c in df.columns if c.startswith("udps.sf_")],
        "Active/Idle (plugin)":[c for c in df.columns if "active_" in c or "idle_" in c],
        "Header (plugin)":     [c for c in df.columns if "header_len" in c],
        "Window (plugin)":     [c for c in df.columns if "win" in c],
        "Rate (plugin)":       [c for c in df.columns if any(x in c for x in ["per_s","ratio","avg_pkt"])],
    }
    print("\n[+] Column breakdown:")
    for cat, cols in categories.items():
        print(f"    {cat:<25} : {len(cols)} cols")

    df.to_csv(output_csv, index=False)
    print(f"\n[+] Saved to: {output_csv}")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# ALIGNMENT HELPER
# Use this AFTER capture to match your model's exact training columns
# ─────────────────────────────────────────────────────────────────────────────
def align_to_model(df: pd.DataFrame, feature_names_path: str) -> pd.DataFrame:
    """
    Aligns the captured DataFrame to the exact columns your model was trained on.
    - Drops columns your model doesn't use
    - Zero-fills any columns that are missing from capture but expected by model

    Usage:
        df_raw    = capture("eth0", 120, "flows.csv")
        df_model  = align_to_model(df_raw, "models/feature_names.json")
        preds     = model.predict(df_model)
    """
    import json
    with open(feature_names_path) as f:
        training_cols = json.load(f)

    missing = set(training_cols) - set(df.columns)
    extra   = set(df.columns) - set(training_cols)

    if missing:
        print(f"[!] {len(missing)} columns missing from capture — zero-filling:")
        for c in sorted(missing):
            print(f"    - {c}")
            df[c] = 0.0

    if extra:
        print(f"[i] {len(extra)} extra columns dropped (not in training set)")

    return df[training_cols]


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Capture network flows and extract 300+ features"
    )
    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument("--interface", "-i", help="Network interface (e.g. eth0)")
    src_group.add_argument("--pcap",      "-p", help="Path to existing .pcap file")
    parser.add_argument("--duration", "-d", type=int, default=120,
                        help="Capture duration in seconds (default: 120)")
    parser.add_argument("--output",   "-o", default="flows.csv",
                        help="Output CSV file path (default: flows.csv)")
    args = parser.parse_args()

    source = args.interface if args.interface else args.pcap
    capture(source, args.duration, args.output)