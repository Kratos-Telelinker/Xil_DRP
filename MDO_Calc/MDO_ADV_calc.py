#!/usr/bin/env python3

# Coding       : utf-8 
# Project      : MDO_Calc
# Package      : 
# Filename     : MDO_ADV_calc.py
# Date         : 2026-07-19  6:43 a.m.
# AUTHOR       : krato bdballa@telelinker.com
# Organization : Telelinker Logic Solutions

# Copyright � 2024 Telelinker Logic Solutions
# All rights reserved. 

# ----------------------------------------------------------------------
# Description
"""
MDO_calc.py — Multi-family MMCM/PLL calculator + DRP encoder + JSON export
Supports:
  MMCM: spartan7, artix7, kintex7, virtex7, ultrascale, ultrascale_plus
  PLL : pll7, pll_ultrascale, pll_ultrascale_plus
"""
# ----------------------------------------------------------------------
from dataclasses import dataclass
from typing import Optional, Tuple
import sys
import json

# ============================================================
# FAMILY LIMIT TABLES
# ============================================================

FAMILY_TABLE = {
    # MMCM families
    "spartan7": {
        "TYPE": "MMCM",
        "FVCO_MIN": 600.0, "FVCO_MAX": 1200.0,
        "FPFD_MIN": 10.0,  "FPFD_MAX": 450.0,
        "M_MIN": 2.0, "M_MAX": 64.0,
        "D_MIN": 1.0, "D_MAX": 106.0,
        "O_MIN": 1.0, "O_MAX": 128.0,
        "FRAC": False,
    },
    "artix7": {
        "TYPE": "MMCM",
        "FVCO_MIN": 600.0, "FVCO_MAX": 1200.0,
        "FPFD_MIN": 10.0,  "FPFD_MAX": 450.0,
        "M_MIN": 2.0, "M_MAX": 64.0,
        "D_MIN": 1.0, "D_MAX": 106.0,
        "O_MIN": 1.0, "O_MAX": 128.0,
        "FRAC": False,
    },
    "kintex7": {
        "TYPE": "MMCM",
        "FVCO_MIN": 600.0, "FVCO_MAX": 1440.0,
        "FPFD_MIN": 10.0,  "FPFD_MAX": 450.0,
        "M_MIN": 2.0, "M_MAX": 64.0,
        "D_MIN": 1.0, "D_MAX": 106.0,
        "O_MIN": 1.0, "O_MAX": 128.0,
        "FRAC": False,
    },
    "virtex7": {
        "TYPE": "MMCM",
        "FVCO_MIN": 600.0, "FVCO_MAX": 1600.0,
        "FPFD_MIN": 10.0,  "FPFD_MAX": 450.0,
        "M_MIN": 2.0, "M_MAX": 64.0,
        "D_MIN": 1.0, "D_MAX": 106.0,
        "O_MIN": 1.0, "O_MAX": 128.0,
        "FRAC": False,
    },
    "ultrascale": {
        "TYPE": "MMCM",
        "FVCO_MIN": 800.0, "FVCO_MAX": 1600.0,
        "FPFD_MIN": 10.0,  "FPFD_MAX": 500.0,
        "M_MIN": 4.0, "M_MAX": 128.0,
        "D_MIN": 1.0, "D_MAX": 106.0,
        "O_MIN": 1.0, "O_MAX": 128.0,
        "FRAC": True,
    },
    "ultrascale_plus": {
        "TYPE": "MMCM",
        "FVCO_MIN": 800.0, "FVCO_MAX": 1800.0,
        "FPFD_MIN": 10.0,  "FPFD_MAX": 500.0,
        "M_MIN": 4.0, "M_MAX": 128.0,
        "D_MIN": 1.0, "D_MAX": 128.0,
        "O_MIN": 1.0, "O_MAX": 128.0,
        "FRAC": True,
    },

    # PLL families (7-series, UltraScale, UltraScale+)
    "pll7": {
        "TYPE": "PLL",
        "FVCO_MIN": 400.0, "FVCO_MAX": 1080.0,
        "FPFD_MIN": 10.0,  "FPFD_MAX": 450.0,
        "M_MIN": 2.0, "M_MAX": 64.0,
        "D_MIN": 1.0, "D_MAX": 52.0,
        "O_MIN": 1.0, "O_MAX": 128.0,
        "FRAC": False,
    },
    "pll_ultrascale": {
        "TYPE": "PLL",
        "FVCO_MIN": 800.0, "FVCO_MAX": 1600.0,
        "FPFD_MIN": 10.0,  "FPFD_MAX": 500.0,
        "M_MIN": 4.0, "M_MAX": 128.0,
        "D_MIN": 1.0, "D_MAX": 128.0,
        "O_MIN": 1.0, "O_MAX": 128.0,
        "FRAC": False,
    },
    "pll_ultrascale_plus": {
        "TYPE": "PLL",
        "FVCO_MIN": 800.0, "FVCO_MAX": 1800.0,
        "FPFD_MIN": 10.0,  "FPFD_MAX": 500.0,
        "M_MIN": 4.0, "M_MAX": 128.0,
        "D_MIN": 1.0, "D_MAX": 128.0,
        "O_MIN": 1.0, "O_MAX": 128.0,
        "FRAC": False,
    },
}

FRAC_DEN = 8  # simple 1/8 fractional step for UltraScale MMCM families

# ============================================================
# DATA CLASS
# ============================================================

@dataclass
class MmcmSolution:
    fin_mhz: float
    fout_mhz: float
    m_int: int
    m_frac: int
    d: int
    o_int: int
    o_frac: int
    fvco_mhz: float
    fpfd_mhz: float
    error_ppm: float

    divclk_high: int
    divclk_low: int
    clkfbout_high: int
    clkfbout_low: int
    clkout_high: int
    clkout_low: int

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def _split_even_odd_divide(n: int) -> Tuple[int, int]:
    """Return (high, low) counts for a given integer divide, 50% duty."""
    if n <= 1:
        return 1, 1
    if n % 2 == 0:
        return n // 2, n // 2
    else:
        return (n + 1) // 2, (n - 1) // 2


def select_family(name: str):
    name = name.lower()
    if name not in FAMILY_TABLE:
        print(f"\nERROR: Unknown family '{name}'")
        print("Valid families:")
        for f in FAMILY_TABLE.keys():
            print("  -", f)
        sys.exit(1)
    return FAMILY_TABLE[name]

# ============================================================
# DRP ENCODING (7-series style for timing + frac fields)
# ============================================================

def encode_clk_timing_reg1(high: int, low: int) -> int:
    """
    Encode HighTime/LowTime into _1 register:
    [11]    HighTime[8]
    [10:6]  HighTime[7:3]
    [5]     LowTime[8]
    [4:0]   LowTime[7:3]
    """
    high &= 0x1FF
    low  &= 0x1FF
    reg = 0
    reg |= ((high >> 8) & 0x1) << 11
    reg |= ((high >> 3) & 0x1F) << 6
    reg |= ((low  >> 8) & 0x1) << 5
    reg |= ((low  >> 3) & 0x1F) << 0
    return reg


def encode_clk_ctrl_reg2(edge: int, nocount: int,
                         frac_num: int = 0,
                         frac_rem: int = 0) -> int:
    """
    Encode EDGE/NOCOUNT + fractional fields:
    [13]    EDGE
    [12]    NOCOUNT
    [11:6]  FRAC numerator
    [5:0]   FRAC remainder
    """
    reg = 0
    reg |= (edge & 0x1) << 13
    reg |= (nocount & 0x1) << 12
    reg |= (frac_num & 0x3F) << 6
    reg |= (frac_rem & 0x3F) << 0
    return reg


def encode_divclk_regs(sol: MmcmSolution) -> Tuple[int, int]:
    reg1 = encode_clk_timing_reg1(sol.divclk_high, sol.divclk_low)
    reg2 = encode_clk_ctrl_reg2(edge=0, nocount=0, frac_num=0, frac_rem=0)
    return reg1, reg2


def encode_clkfbout_regs(sol: MmcmSolution, family: dict) -> Tuple[int, int]:
    reg1 = encode_clk_timing_reg1(sol.clkfbout_high, sol.clkfbout_low)
    if family["FRAC"] and family["TYPE"] == "MMCM":
        frac_num = sol.m_frac
        frac_rem = 0
    else:
        frac_num = 0
        frac_rem = 0
    reg2 = encode_clk_ctrl_reg2(edge=0, nocount=0, frac_num=frac_num, frac_rem=frac_rem)
    return reg1, reg2


def encode_clkout0_regs(sol: MmcmSolution, family: dict) -> Tuple[int, int]:
    reg1 = encode_clk_timing_reg1(sol.clkout_high, sol.clkout_low)
    if family["FRAC"] and family["TYPE"] == "MMCM":
        frac_num = sol.o_frac
        frac_rem = 0
    else:
        frac_num = 0
        frac_rem = 0
    reg2 = encode_clk_ctrl_reg2(edge=0, nocount=0, frac_num=frac_num, frac_rem=frac_rem)
    return reg1, reg2


def encode_pll_regs(sol: MmcmSolution) -> dict:
    """
    PLL DRP registers: same timing structure, no fractional fields.
    """
    divclk_1 = encode_clk_timing_reg1(sol.divclk_high, sol.divclk_low)
    divclk_2 = encode_clk_ctrl_reg2(0, 0)

    clkfbout_1 = encode_clk_timing_reg1(sol.clkfbout_high, sol.clkfbout_low)
    clkfbout_2 = encode_clk_ctrl_reg2(0, 0)

    clkout0_1 = encode_clk_timing_reg1(sol.clkout_high, sol.clkout_low)
    clkout0_2 = encode_clk_ctrl_reg2(0, 0)

    return {
        "0x14": divclk_1,
        "0x15": clkfbout_1,
        "0x16": clkfbout_2,
        "0x01": clkout0_1,
        "0x02": clkout0_2,
    }

# ============================================================
# CORE SOLVER (MMCM + PLL, fractional for UltraScale MMCM)
# ============================================================

def find_mmcm_solution(fin_mhz: float,
                       fout_mhz: float,
                       family: dict,
                       max_error_ppm: float = 50_000.0
                       ) -> Optional[MmcmSolution]:

    FVCO_MIN = family["FVCO_MIN"]
    FVCO_MAX = family["FVCO_MAX"]
    FPFD_MIN = family["FPFD_MIN"]
    FPFD_MAX = family["FPFD_MAX"]
    M_MIN = int(family["M_MIN"])
    M_MAX = int(family["M_MAX"])
    D_MIN = int(family["D_MIN"])
    D_MAX = int(family["D_MAX"])
    O_MIN = int(family["O_MIN"])
    O_MAX = int(family["O_MAX"])
    use_frac = family["FRAC"] and (family["TYPE"] == "MMCM")

    best: Optional[MmcmSolution] = None

    for d in range(D_MIN, D_MAX + 1):
        fpfd = fin_mhz / d
        if fpfd < FPFD_MIN or fpfd > FPFD_MAX:
            continue

        for m_int in range(M_MIN, M_MAX + 1):
            m_frac_range = range(0, FRAC_DEN) if use_frac else range(1)
            for m_frac in m_frac_range:
                m_eff = m_int + m_frac / FRAC_DEN
                fvco = fpfd * m_eff
                if fvco < FVCO_MIN or fvco > FVCO_MAX:
                    continue

                for o_int in range(O_MIN, O_MAX + 1):
                    o_frac_range = range(0, FRAC_DEN) if use_frac else range(1)
                    for o_frac in o_frac_range:
                        o_eff = o_int + o_frac / FRAC_DEN
                        fout_actual = fvco / o_eff
                        error_ppm = abs(fout_actual - fout_mhz) / fout_mhz * 1e6
                        if error_ppm > max_error_ppm:
                            continue

                        divclk_high, divclk_low = _split_even_odd_divide(d)
                        clkfbout_high, clkfbout_low = _split_even_odd_divide(m_int)
                        clkout_high, clkout_low = _split_even_odd_divide(o_int)

                        sol = MmcmSolution(
                            fin_mhz=fin_mhz,
                            fout_mhz=fout_mhz,
                            m_int=m_int,
                            m_frac=m_frac,
                            d=d,
                            o_int=o_int,
                            o_frac=o_frac,
                            fvco_mhz=fvco,
                            fpfd_mhz=fpfd,
                            error_ppm=error_ppm,
                            divclk_high=divclk_high,
                            divclk_low=divclk_low,
                            clkfbout_high=clkfbout_high,
                            clkfbout_low=clkfbout_low,
                            clkout_high=clkout_high,
                            clkout_low=clkout_low,
                        )

                        if best is None or sol.error_ppm < best.error_ppm:
                            best = sol

    return best

def main():
    # MDO_ADV_calc.py Code starts here Indented 1 level
    print('MDO_ADV_calc.py  created: 2026-07-19  6:43 a.m.')
# ============================================================
# MAIN
# ============================================================


    if len(sys.argv) < 2:
        print("Usage: python MDO_calc.py <family>")
        print("Families:")
        for f in FAMILY_TABLE.keys():
            print("  -", f)
        sys.exit(1)

    family_name = sys.argv[1]
    family = select_family(family_name)

    print(f"\nSelected family: {family_name} (TYPE={family['TYPE']})\n")

    fin = float(input("Enter input frequency (MHz): "))
    fout = float(input("Enter desired output frequency (MHz): "))

    sol = find_mmcm_solution(fin, fout, family)

    if sol is None:
        print("\nNo legal MMCM/PLL solution found.\n")
        return

    use_frac = family["FRAC"] and (family["TYPE"] == "MMCM")
    m_eff = sol.m_int + (sol.m_frac / FRAC_DEN if use_frac else 0.0)
    o_eff = sol.o_int + (sol.o_frac / FRAC_DEN if use_frac else 0.0)
    fout_actual = sol.fvco_mhz / o_eff

    print("\n=== Clocking Solution ===")
    print(f"Type     : {family['TYPE']}")
    print(f"FIN      : {sol.fin_mhz:.3f} MHz")
    print(f"FOUT req : {sol.fout_mhz:.3f} MHz")
    print(f"FOUT act : {fout_actual:.6f} MHz")
    print(f"M        : {m_eff:.6f} (int={sol.m_int}, frac={sol.m_frac}/{FRAC_DEN if use_frac else 1})")
    print(f"D        : {sol.d}")
    print(f"O        : {o_eff:.6f} (int={sol.o_int}, frac={sol.o_frac}/{FRAC_DEN if use_frac else 1})")
    print(f"FVCO     : {sol.fvco_mhz:.3f} MHz")
    print(f"FPFD     : {sol.fpfd_mhz:.3f} MHz")
    print(f"Error    : {sol.error_ppm:.1f} ppm\n")

    print("DIVCLK   : high =", sol.divclk_high, "low =", sol.divclk_low)
    print("CLKFBOUT : high =", sol.clkfbout_high, "low =", sol.clkfbout_low)
    print("CLKOUT0  : high =", sol.clkout_high, "low =", sol.clkout_low)
    print()

    # DRP register generation
    divclk_1, divclk_2 = encode_divclk_regs(sol)
    clkfbout_1, clkfbout_2 = encode_clkfbout_regs(sol, family)
    clkout0_1, clkout0_2 = encode_clkout0_regs(sol, family)

    if family["TYPE"] == "PLL":
        drp_regs = encode_pll_regs(sol)
    else:
        drp_regs = {
            "0x14": divclk_1,
            "0x15": clkfbout_1,
            "0x16": clkfbout_2,
            "0x01": clkout0_1,
            "0x02": clkout0_2,
        }

    print("DRP registers (hex):")
    for addr, val in drp_regs.items():
        print(f"  {addr} : 0x{val:04X}")
    print()

    json_obj = {
        "family": family_name,
        "type": family["TYPE"],
        "fin_mhz": sol.fin_mhz,
        "fout_mhz": sol.fout_mhz,
        "m_int": sol.m_int,
        "m_frac": sol.m_frac,
        "d": sol.d,
        "o_int": sol.o_int,
        "o_frac": sol.o_frac,
        "fvco_mhz": sol.fvco_mhz,
        "fpfd_mhz": sol.fpfd_mhz,
        "error_ppm": sol.error_ppm,
        "divclk_high": sol.divclk_high,
        "divclk_low": sol.divclk_low,
        "clkfbout_high": sol.clkfbout_high,
        "clkfbout_low": sol.clkfbout_low,
        "clkout0_high": sol.clkout_high,
        "clkout0_low": sol.clkout_low,
        "drp_registers": drp_regs,
    }

    with open("drp_config.json", "w") as f:
        json.dump(json_obj, f, indent=2)

    print("DRP configuration written to drp_config.json\n")

# ============================================================

if __name__ == '__main__':
    print()
    print("*" * 50)
    print("MDO_ADV_calc.py : Running Python {0}.{1}.{2}"
          .format(int(sys.version_info[0]),
                  int(sys.version_info[1]),
                  int(sys.version_info[2])))
    print("Copyright � 2026 Telelinker Logic Solutions")
    print("All rights reserved")
    print("*" * 50 + "\n")
    if int(sys.version_info[0]) < 3 or (int(sys.version_info[0]) == 3
                                        and int(sys.version_info[1]) < 12):
        raise Exception("Must be running Python 3.12 or newer.")
    main()
