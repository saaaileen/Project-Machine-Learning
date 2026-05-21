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
        "median":   float(np.median(a)),
        "mode":     float(pd.Series(a).mode()[0]) if len(a) > 0 else 0.0,
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
        for p_out, arr in [
            ("fwd_packets_delta_len",  fwd),
            ("bwd_packets_delta_len",  bwd),
            ("packets_delta_len",      both),
        ]:
            s = _stats(arr)
            for k, v in s.items():
                if k in ["min", "max", "mean", "std", "variance", "skewness", "kurtosis", "median", "mode"]:
                    setattr(flow.udps, f"{k}_{p_out}", v)
                elif k == "cv":
                    setattr(flow.udps, f"cov_{p_out}", v)
                else:
                    setattr(flow.udps, f"{p_out}_{k}", v)

        # 10 stats × 2 payload directions = 20 more cols
        for prefix, arr in [
            ("fwd_payload_bytes", flow.udps._fwd_payload_lens),
            ("bwd_payload_bytes", flow.udps._bwd_payload_lens),
            ("payload_bytes", flow.udps._fwd_payload_lens + flow.udps._bwd_payload_lens),
        ]:
            s = _stats(arr)
            for k, v in s.items():
                if k == "cv":
                    setattr(flow.udps, f"{prefix}_cov", v)
                else:
                    setattr(flow.udps, f"{prefix}_{k}", v)

        # payload ratio (how much of each packet is actual data)
        total_bytes   = sum(both) or 1
        payload_bytes = sum(flow.udps._fwd_payload_lens + flow.udps._bwd_payload_lens)
        flow.udps.total_payload_bytes = float(payload_bytes)
        flow.udps.fwd_total_payload_bytes = float(sum(flow.udps._fwd_payload_lens))
        flow.udps.bwd_total_payload_bytes = float(sum(flow.udps._bwd_payload_lens))
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
        for prefix, prefix_delta, arr in [
            ("packets_IAT", "packets_delta_time", flow_iats),
            ("fwd_packets_IAT", "fwd_packets_delta_time", fwd_iats),
            ("bwd_packets_IAT", "bwd_packets_delta_time", bwd_iats),
        ]:
            s = _stats(arr)
            for k, v in s.items():
                if k == "cv":
                    k = "cov"
                if prefix == "packets_IAT" and k == "std":
                    setattr(flow.udps, f"packet_IAT_std", v)
                else:
                    setattr(flow.udps, f"{prefix}_{k}", v)
                    
                if k in ["min", "max", "mean", "std", "variance", "skewness", "kurtosis", "median", "mode"]:
                    setattr(flow.udps, f"{k}_{prefix_delta}", v)
                elif k == "cov":
                    setattr(flow.udps, f"cov_{prefix_delta}", v)

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
            
            setattr(flow.udps, f"{f}_flag_counts", fwd_cnt + bwd_cnt)
            setattr(flow.udps, f"fwd_{f}_flag_counts", fwd_cnt)
            setattr(flow.udps, f"bwd_{f}_flag_counts", bwd_cnt)
            
            setattr(flow.udps, f"{f}_flag_percentage_in_total", (fwd_cnt + bwd_cnt) / total_pkts)
            setattr(flow.udps, f"fwd_{f}_flag_percentage_in_total", fwd_cnt / total_pkts)
            setattr(flow.udps, f"bwd_{f}_flag_percentage_in_total", bwd_cnt / total_pkts)
            
            setattr(flow.udps, f"fwd_{f}_flag_percentage_in_fwd_packets", fwd_cnt / max(flow.udps._fwd_flag_pkts, 1))
            setattr(flow.udps, f"bwd_{f}_flag_percentage_in_bwd_packets", bwd_cnt / max(flow.udps._bwd_flag_pkts, 1))


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
            setattr(flow.udps, f"{d}_bulk_state_count", cnt)
            setattr(flow.udps, f"{d}_bulk_total_size", byts)
            setattr(flow.udps, f"avg_{d}_bytes_per_bulk", byts / max(cnt, 1))
            setattr(flow.udps, f"avg_{d}_bulk_rate", byts / max(dur / 1000, 1))


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
            setattr(flow.udps, f"subflow_{d}_packets", float(p.sum()))
            setattr(flow.udps, f"subflow_{d}_bytes", float(b.sum()))


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
            if k == "cv":
                setattr(flow.udps, f"active_cov", v)
            else:
                setattr(flow.udps, f"active_{k}", v)

        # 10 stats for idle times
        for k, v in _stats(flow.udps._idle_list).items():
            if k == "cv":
                setattr(flow.udps, f"idle_cov", v)
            else:
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
            ("fwd", flow.udps._fwd_hdr_lens),
            ("bwd", flow.udps._bwd_hdr_lens),
        ]:
            s = _stats(arr)
            for k, v in s.items():
                if k in ["min", "max", "mean", "std", "variance", "skewness", "kurtosis", "median", "mode"]:
                    setattr(flow.udps, f"{prefix}_{k}_header_bytes", v)
                    setattr(flow.udps, f"{k}_{prefix}_header_bytes_delta_len", v)
                elif k == "cv":
                    setattr(flow.udps, f"{prefix}_cov_header_bytes", v)
                    setattr(flow.udps, f"cov_{prefix}_header_bytes_delta_len", v)

        # overall stats
        s_all = _stats(flow.udps._fwd_hdr_lens + flow.udps._bwd_hdr_lens)
        for k, v in s_all.items():
            if k in ["min", "max", "mean", "std", "variance", "skewness", "kurtosis", "median", "mode"]:
                setattr(flow.udps, f"{k}_header_bytes", v)
                setattr(flow.udps, f"{k}_header_bytes_delta_len", v)
            elif k == "cv":
                setattr(flow.udps, f"cov_header_bytes", v)
                setattr(flow.udps, f"cov_header_bytes_delta_len", v)


# ─────────────────────────────────────────────────────────────────────────────
# PLUGIN 8 — Window Size + Initial Window  (~14 cols)
# TCP window size statistics per direction
# ─────────────────────────────────────────────────────────────────────────────
class WindowPlugin(NFPlugin):
    def on_init(self, packet, flow):
        flow.udps._fwd_wins  = []
        flow.udps._bwd_wins  = []
        flow.udps.fwd_init_win_bytes = -1
        flow.udps.bwd_init_win_bytes = -1

    def on_update(self, packet, flow):
        win = getattr(packet, "tcp_window", None)
        if win is None:
            return
        if packet.direction == 0:
            flow.udps._fwd_wins.append(win)
            if flow.udps.fwd_init_win_bytes == -1:
                flow.udps.fwd_init_win_bytes = win
        else:
            flow.udps._bwd_wins.append(win)
            if flow.udps.bwd_init_win_bytes == -1:
                flow.udps.bwd_init_win_bytes = win

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

        flow.udps.bytes_rate     = (fb + bb) / dur_s
        flow.udps.packets_rate      = (fp + bp) / dur_s
        flow.udps.fwd_packets_rate       = fp / dur_s
        flow.udps.bwd_packets_rate       = bp / dur_s
        flow.udps.bwd_bytes_rate      = bb / dur_s
        flow.udps.down_up_rate        = bb / max(fb, 1)
        
        # Additional exact feature name aliases
        flow.udps.bwd_avg_segment_size = bb / max(bp, 1)
        flow.udps.handshake_state = 0.0 # Placeholder
        flow.udps.delta_start = 0.0     # Placeholder
        
        # Payload bytes delta len aliases (duplicate names in dataset)
        flow.udps.mode_payload_bytes_delta_len = getattr(flow.udps, "payload_bytes_mode", 0.0)
        flow.udps.skewness_payload_bytes_delta_len = getattr(flow.udps, "payload_bytes_skewness", 0.0)
        flow.udps.skewness_fwd_payload_bytes_delta_len = getattr(flow.udps, "fwd_payload_bytes_skewness", 0.0)
        flow.udps.skewness_bwd_payload_bytes_delta_len = getattr(flow.udps, "bwd_payload_bytes_skewness", 0.0)

        # Also map some final basic features
        flow.udps.duration = dur_ms
        flow.udps.packets_count = fp + bp


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
    
    # ── Final Naming Alignment ──
    # NFStream automatically prepends 'udps.' to all our plugin features.
    # We must strip this prefix so the column names perfectly match the model's expected features.
    df.columns = [c.replace("udps.", "") for c in df.columns]

    print(f"\n[+] Flows captured : {len(df)}")
    print(f"[+] Total columns  : {len(df.columns)}")

    # Print column count breakdown
    categories = {
        "NFStream base":       [c for c in df.columns if c in ["id", "src_ip", "src_port", "dst_ip", "dst_port", "protocol"]],
        "Pkt length (plugin)": [c for c in df.columns if "delta_len" in c or "payload_bytes" in c],
        "IAT (plugin)":        [c for c in df.columns if "IAT" in c or "delta_time" in c],
        "TCP flags (plugin)":  [c for c in df.columns if "flag" in c],
        "Bulk (plugin)":       [c for c in df.columns if "bulk" in c],
        "Subflow (plugin)":    [c for c in df.columns if "subflow" in c],
        "Active/Idle (plugin)":[c for c in df.columns if "active_" in c or "idle_" in c],
        "Header (plugin)":     [c for c in df.columns if "header_bytes" in c],
        "Window (plugin)":     [c for c in df.columns if "win" in c],
        "Rate (plugin)":       [c for c in df.columns if "rate" in c],
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