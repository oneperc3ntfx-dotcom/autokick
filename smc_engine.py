#!/usr/bin/env python3
"""
SMC (Smart Money Concept) Engine
=================================
Mendeteksi struktur market berbasis candle OHLC:
- Swing High / Swing Low
- BOS (Break of Structure) & CHoCH (Change of Character)
- Order Block (OB) terakhir yang valid & belum dimitigasi
- Fair Value Gap (FVG)
- Liquidity Sweep (wick menembus swing lalu reverse)

Catatan penting:
SMC pada dasarnya diskresioner. Modul ini adalah APROKSIMASI rule-based
dari konsep SMC, bukan pengganti analisa manusia. Selalu backtest dulu
sebelum dipakai dengan uang sungguhan.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("XAU-BOT.smc")


# ================= DATA STRUCTURES =================

@dataclass
class Candle:
    time: str
    open: float
    high: float
    low: float
    close: float

    @property
    def bullish(self):
        return self.close > self.open

    @property
    def bearish(self):
        return self.close < self.open


@dataclass
class SwingPoint:
    index: int
    price: float
    kind: str  # "high" or "low"


@dataclass
class OrderBlock:
    index: int
    kind: str  # "bullish" or "bearish"
    top: float
    bottom: float
    mitigated: bool = False


@dataclass
class FVG:
    index: int
    kind: str  # "bullish" or "bearish"
    top: float
    bottom: float
    filled: bool = False


@dataclass
class SMCResult:
    bias: Optional[str] = None          # "BUY" / "SELL" / None
    structure: str = "UNDEFINED"        # "BOS_UP" / "BOS_DOWN" / "CHOCH_UP" / "CHOCH_DOWN" / "RANGE"
    reasons: list = field(default_factory=list)
    active_ob: Optional[OrderBlock] = None
    active_fvg: Optional[FVG] = None
    liquidity_sweep: Optional[str] = None  # "buy_side" / "sell_side" / None
    last_close: Optional[float] = None


# ================= SWING DETECTION =================

def find_swings(candles: list[Candle], left: int = 2, right: int = 2) -> list[SwingPoint]:
    """
    Deteksi swing high/low sederhana: titik dianggap swing high jika
    high-nya lebih tinggi dari `left` candle sebelum dan `right` candle
    sesudahnya (begitu juga sebaliknya untuk swing low).
    """
    swings = []
    n = len(candles)

    for i in range(left, n - right):
        window_high = [candles[j].high for j in range(i - left, i + right + 1)]
        window_low = [candles[j].low for j in range(i - left, i + right + 1)]

        if candles[i].high == max(window_high) and window_high.count(candles[i].high) == 1:
            swings.append(SwingPoint(index=i, price=candles[i].high, kind="high"))

        if candles[i].low == min(window_low) and window_low.count(candles[i].low) == 1:
            swings.append(SwingPoint(index=i, price=candles[i].low, kind="low"))

    swings.sort(key=lambda s: s.index)
    return swings


# ================= STRUCTURE (BOS / CHoCH) =================

def detect_structure(candles: list[Candle], swings: list[SwingPoint]) -> tuple[str, list[str]]:
    """
    Bandingkan swing high/low terbaru untuk menentukan:
    - BOS_UP   : higher high terbentuk searah trend naik (continuation)
    - BOS_DOWN : lower low terbentuk searah trend turun (continuation)
    - CHOCH_UP : trend turun lalu tiba-tiba break swing high terakhir (reversal naik)
    - CHOCH_DOWN: trend naik lalu tiba-tiba break swing low terakhir (reversal turun)
    """
    reasons = []

    highs = [s for s in swings if s.kind == "high"]
    lows = [s for s in swings if s.kind == "low"]

    if len(highs) < 2 or len(lows) < 2:
        return "UNDEFINED", ["Data swing belum cukup untuk menentukan struktur"]

    last_close = candles[-1].close

    last_high = highs[-1]
    prev_high = highs[-2]
    last_low = lows[-1]
    prev_low = lows[-2]

    higher_high = last_high.price > prev_high.price
    higher_low = last_low.price > prev_low.price
    lower_low = last_low.price < prev_low.price
    lower_high = last_high.price < prev_high.price

    was_downtrend = lower_low and lower_high
    was_uptrend = higher_high and higher_low

    # PENTING: cek breakout (harga sekarang vs swing) LEBIH DULU sebelum
    # menyimpulkan trend "masih intact". Kalau urutannya dibalik, candle
    # impulsif yang sudah menembus jauh di atas/bawah swing tapi belum
    # membentuk swing baru (karena butuh `right` candle konfirmasi) akan
    # salah dibaca sebagai trend lama yang masih berjalan.

    # Breakout ke atas swing high terakhir
    if last_close > last_high.price:
        if was_downtrend:
            reasons.append(
                f"CHoCH UP: trend turun berubah, close {last_close:.2f} break swing high {last_high.price:.2f}"
            )
            return "CHOCH_UP", reasons
        reasons.append(f"BOS UP: close {last_close:.2f} menembus swing high {last_high.price:.2f}")
        return "BOS_UP", reasons

    # Breakout ke bawah swing low terakhir
    if last_close < last_low.price:
        if was_uptrend:
            reasons.append(
                f"CHoCH DOWN: trend naik berubah, close {last_close:.2f} break swing low {last_low.price:.2f}"
            )
            return "CHOCH_DOWN", reasons
        reasons.append(f"BOS DOWN: close {last_close:.2f} menembus swing low {last_low.price:.2f}")
        return "BOS_DOWN", reasons

    # Belum ada breakout -> trend lama (kalau ada) masih dianggap intact
    if was_uptrend:
        reasons.append("Struktur uptrend (higher high & higher low) masih intact, belum ada BOS baru")
        return "RANGE", reasons

    if was_downtrend:
        reasons.append("Struktur downtrend (lower low & lower high) masih intact, belum ada BOS baru")
        return "RANGE", reasons

    reasons.append("Struktur belum jelas / sideways")
    return "RANGE", reasons


# ================= ORDER BLOCK =================

def find_order_blocks(candles: list[Candle], structure: str) -> Optional[OrderBlock]:
    """
    Order block sederhana: candle terakhir berlawanan arah (down candle untuk
    bullish OB, up candle untuk bearish OB) sebelum pergerakan impulsif yang
    menghasilkan BOS/CHoCH. Kita ambil dari ~15 candle terakhir, candle paling
    baru yang relevan dan belum dimitigasi (harga belum kembali menembus penuh).
    """
    if structure in ("BOS_UP", "CHOCH_UP"):
        # cari candle bearish terakhir sebelum leg naik
        for i in range(len(candles) - 2, max(len(candles) - 20, 0), -1):
            c = candles[i]
            if c.bearish:
                ob = OrderBlock(index=i, kind="bullish", top=c.high, bottom=c.low)
                # cek mitigasi: apakah candle setelahnya sudah menutup di bawah bottom OB
                for later in candles[i + 1:]:
                    if later.close < ob.bottom:
                        ob.mitigated = True
                        break
                return ob

    if structure in ("BOS_DOWN", "CHOCH_DOWN"):
        # cari candle bullish terakhir sebelum leg turun
        for i in range(len(candles) - 2, max(len(candles) - 20, 0), -1):
            c = candles[i]
            if c.bullish:
                ob = OrderBlock(index=i, kind="bearish", top=c.high, bottom=c.low)
                for later in candles[i + 1:]:
                    if later.close > ob.top:
                        ob.mitigated = True
                        break
                return ob

    return None


# ================= FAIR VALUE GAP =================

def find_fair_value_gaps(candles: list[Candle], lookback: int = 15) -> Optional[FVG]:
    """
    FVG 3-candle: gap antara high candle[i-1] dan low candle[i+1] (bullish FVG),
    atau antara low candle[i-1] dan high candle[i+1] (bearish FVG).
    Mengembalikan FVG terakhir yang belum terisi penuh.
    """
    start = max(1, len(candles) - lookback)
    last_fvg = None

    for i in range(start, len(candles) - 1):
        c0, c2 = candles[i - 1], candles[i + 1]

        # Bullish FVG: low candle setelahnya > high candle sebelumnya
        if c2.low > c0.high:
            fvg = FVG(index=i, kind="bullish", top=c2.low, bottom=c0.high)
            filled = any(c.low <= fvg.bottom for c in candles[i + 2:])
            fvg.filled = filled
            if not filled:
                last_fvg = fvg

        # Bearish FVG: high candle setelahnya < low candle sebelumnya
        if c2.high < c0.low:
            fvg = FVG(index=i, kind="bearish", top=c0.low, bottom=c2.high)
            filled = any(c.high >= fvg.top for c in candles[i + 2:])
            fvg.filled = filled
            if not filled:
                last_fvg = fvg

    return last_fvg


# ================= LIQUIDITY SWEEP =================

def detect_liquidity_sweep(candles: list[Candle], swings: list[SwingPoint]) -> Optional[str]:
    """
    Liquidity sweep: candle terbaru membuat wick yang menembus swing high/low
    sebelumnya, tapi closing kembali di dalam range (rejection) -> indikasi
    stop hunt / liquidity grab sebelum reversal.
    """
    if not swings or len(candles) < 3:
        return None

    last = candles[-1]
    recent_highs = [s for s in swings if s.kind == "high" and s.index < len(candles) - 1]
    recent_lows = [s for s in swings if s.kind == "low" and s.index < len(candles) - 1]

    if recent_highs:
        ref_high = recent_highs[-1].price
        if last.high > ref_high and last.close < ref_high:
            return "sell_side"  # sweep liquidity di atas, lalu reject turun

    if recent_lows:
        ref_low = recent_lows[-1].price
        if last.low < ref_low and last.close > ref_low:
            return "buy_side"  # sweep liquidity di bawah, lalu reject naik

    return None


# ================= MAIN ENTRY POINT =================

def analyze(candles: list[Candle]) -> SMCResult:
    """
    Jalankan seluruh pipeline SMC dan hasilkan kesimpulan bias + alasan.
    `candles` harus urut dari paling lama -> paling baru.
    """
    result = SMCResult()

    if len(candles) < 10:
        result.reasons.append("Data candle tidak cukup (minimal 10 candle)")
        return result

    result.last_close = candles[-1].close

    swings = find_swings(candles)
    structure, structure_reasons = detect_structure(candles, swings)
    result.structure = structure
    result.reasons.extend(structure_reasons)

    sweep = detect_liquidity_sweep(candles, swings)
    result.liquidity_sweep = sweep
    if sweep == "buy_side":
        result.reasons.append("Liquidity sweep terdeteksi di bawah swing low (potensi reversal naik)")
    elif sweep == "sell_side":
        result.reasons.append("Liquidity sweep terdeteksi di atas swing high (potensi reversal turun)")

    ob = find_order_blocks(candles, structure)
    if ob and not ob.mitigated:
        result.active_ob = ob
        result.reasons.append(
            f"Order block {ob.kind} aktif di area {ob.bottom:.2f} - {ob.top:.2f}"
        )

    fvg = find_fair_value_gaps(candles)
    if fvg:
        result.active_fvg = fvg
        result.reasons.append(
            f"Fair Value Gap {fvg.kind} belum terisi di area {fvg.bottom:.2f} - {fvg.top:.2f}"
        )

    # ================= KEPUTUSAN BIAS =================
    # Bias hanya diberikan jika ada konfirmasi struktur YANG JELAS (BOS/CHoCH)
    # Tidak ada bias dipaksakan saat market RANGE/UNDEFINED -> ini penting,
    # lebih baik tidak ada sinyal daripada sinyal palsu.

    if structure in ("BOS_UP", "CHOCH_UP"):
        result.bias = "BUY"
    elif structure in ("BOS_DOWN", "CHOCH_DOWN"):
        result.bias = "SELL"
    else:
        result.bias = None
        result.reasons.append("Tidak ada bias jelas -> sinyal ditahan (no trade)")

    return result
