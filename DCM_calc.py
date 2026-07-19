#!/usr/bin/env python3

# Coding       : utf-8 
# Project      : MDO_Calc
# Package      : 
# Filename     : MDO_ADV_calc.py
# Date         : 2026-07-19  6:43 a.m.
# AUTHOR       : kratos@telelinker.com
# Organization : Telelinker Logic Solutions

# Copyright � 2026 Telelinker Logic Solutions
# All rights reserved.
# ----------------------------------------------------------------------
# Description
"""
DCM_calc.py — DCM_CLKGEN-style frequency calculator + DRP encoder + JSON export
Separate from MMCM/PLL math.
"""
# ----------------------------------------------------------------------
from dataclasses import dataclass
from typing import Optional
import sys
import json

# Approximate limits (check UG for exact values)
FCLKIN_MIN = 1.0    # MHz
FCLKIN_MAX = 210.0  # MHz
FOUT_MIN   = 1.0    # MHz
FOUT_MAX   = 210.0  # MHz

@dataclass
class DcmSolution:
    fin_mhz: float
    fout_mhz: float
    mult: int
    div: int
    fout_actual_mhz: float
    error_ppm: float

def find_dcm_solution(fin_mhz: float,
                      fout_mhz: float,
                      max_error_ppm: float = 50_000.0
                      ) -> Optional[DcmSolution]:
    if fin_mhz < FCLKIN_MIN or fin_mhz > FCLKIN_MAX:
        return None

    best: Optional[DcmSolution] = None

    # brute-force mult/div
    for mult in range(1, 64):
        for div in range(1, 64):
            fout_actual = fin_mhz * mult / div
            if fout_actual < FOUT_MIN or fout_actual > FOUT_MAX:
                continue
            error_ppm = abs(fout_actual - fout_mhz) / fout_mhz * 1e6
            if error_ppm > max_error_ppm:
                continue

            sol = DcmSolution(
                fin_mhz=fin_mhz,
                fout_mhz=fout_mhz,
                mult=mult,
                div=div,
                fout_actual_mhz=fout_actual,
                error_ppm=error_ppm,
            )
            if best is None or sol.error_ppm < best.error_ppm:
                best = sol

    return best

# --- DRP encoding (simplified DCM_CLKGEN-style) ---

def encode_dcm_drp(sol: DcmSolution) -> dict:
    """
    Return a DRP register map for DCM_CLKGEN-like block.
    This is schematic: you’ll align exact addresses/fields to UG.
    """
    # Example encoding:
    # - MULT register at 0x00
    # - DIV  register at 0x01
    # - CTRL register at 0x02 (enable, restart, etc.)
    mult_reg = sol.mult & 0xFF
    div_reg  = sol.div & 0xFF
    ctrl_reg = 0x0001  # enable bit

    return {
        "0x00": mult_reg,
        "0x01": div_reg,
        "0x02": ctrl_reg,
    }

def main():
    # DCM_calc.py Code starts here Indented 1 level
    print('DCM_calc.py  created: 2026-07-19  7:40 a.m.\n\n')

    if len(sys.argv) < 1:
        print("Usage: python DCM_calc.py")
        sys.exit(1)

    fin = float(input("Enter DCM input frequency (MHz): "))
    fout = float(input("Enter desired DCM output frequency (MHz): "))

    sol = find_dcm_solution(fin, fout)

    if sol is None:
        print("\nNo legal DCM solution found.\n")
        return

    print("\n=== DCM Solution ===")
    print(f"FIN       : {sol.fin_mhz:.3f} MHz")
    print(f"FOUT req  : {sol.fout_mhz:.3f} MHz")
    print(f"FOUT act  : {sol.fout_actual_mhz:.6f} MHz")
    print(f"MULT      : {sol.mult}")
    print(f"DIV       : {sol.div}")
    print(f"Error     : {sol.error_ppm:.1f} ppm\n")

    drp_regs = encode_dcm_drp(sol)

    print("DCM DRP registers (hex):")
    for addr, val in drp_regs.items():
        print(f"  {addr} : 0x{val:04X}")
    print()

    json_obj = {
        "type": "DCM",
        "fin_mhz": sol.fin_mhz,
        "fout_mhz": sol.fout_mhz,
        "mult": sol.mult,
        "div": sol.div,
        "fout_actual_mhz": sol.fout_actual_mhz,
        "error_ppm": sol.error_ppm,
        "drp_registers": drp_regs,
    }

    with open("dcm_config.json", "w") as f:
        json.dump(json_obj, f, indent=2)

    print("DCM configuration written to dcm_config.json\n")

if __name__ == '__main__':
    print()
    print("*" * 50)
    print("DCM_calc.py : Running Python {0}.{1}.{2}"
          .format(int(sys.version_info[0]),
                  int(sys.version_info[1]),
                  int(sys.version_info[2])))
    print("Copyright � 2026 Telelinker Logic Solutions")
    print("All rights reserved")
    print("*" * 50 + "\n\n")
    if int(sys.version_info[0]) < 3 or (int(sys.version_info[0]) == 3
                                        and int(sys.version_info[1]) < 12):
        raise Exception("Must be running Python 3.12 or newer.")
    main()
