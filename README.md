# MDO_ADV_calc — Multi-family MMCM/PLL Clock Calculator + DRP Encoder

`MDO_ADV_calc.py` is a command-line tool that computes legal clocking configurations
for Xilinx MMCM and PLL primitives across multiple FPGA families, and emits
DRP register values plus a JSON configuration file suitable for cocotb-based
dynamic reconfiguration.

## Supported structures

- MMCM:
  - `spartan7`
  - `artix7`
  - `kintex7`
  - `virtex7`
  - `ultrascale`
  - `ultrascale_plus` (fractional M/O supported)
- PLL:
  - `pll7` (PLLE2_ADV / PLLE2_BASE)
  - `pll_ultrascale`
  - `pll_ultrascale_plus`
  - 
## DCM vs MMCM/PLL — Separate Flows
This repository intentionally separates **DCM** logic from **MMCM/PLL** logic.

### MMCM/PLL (MDO_ADV_calc.py)
- Uses `M`, `D`, `O` structure:
  - `FVCO = FIN / D * M`
  - `FOUT = FVCO / O`
- Supports:
  - 7‑Series MMCM
  - UltraScale / UltraScale+ MMCM (fractional M/O)
  - 7‑Series PLL
  - UltraScale / UltraScale+ PLL (integer only)
- Emits:
  - `drp_config.json`
  - DRP registers for MMCM/PLL
- Driven by:
  - `drp_driver.py`
  - `mmcm_drp_wrapper.sv`

### DCM (DCM_calc.py)

- Uses simple multiply/divide:
  - `FOUT = FIN * MULT / DIV`
- No fractional support.
- Different legal frequency ranges and behavior than MMCM/PLL.
- Emits:
  - `dcm_config.json`
  - DRP registers for DCM (e.g., MULT, DIV, CTRL)


### Why separate?

- DCMs are **not** MMCMs or PLLs:
  - Different internal architecture
  - Different DRP maps
  - Different jitter and phase‑shift behavior
  - Mixing DCM math with MMCM/PLL math leads to invalid configurations.

### DCM_calc.py Constraints
  1. Input clock constraints (FCLKIN)
    Typical legal range:
    1 MHz ≤ FCLKIN ≤ 210 MHz
    Below ~1 MHz the DLL cannot lock
    Above ~200 MHz the internal delay line cannot track

  2. Output clock constraints (FOUT)
    1 MHz ≤ FOUT ≤ 210 MHz
    DCM_CLKGEN uses a digital accumulator + phase interpolator
    calculator enforces:
      FOUT_MIN = 1.0
      FOUT_MAX = 210.0
  
  3. Multiply/Divide constraints (M, D)
      DCM_CLKGEN uses:
      1 ≤ M ≤ 63
      1 ≤ D ≤ 63
      M and D are 6‑bit integer registers
      No fractional support
      No extended ranges like MMCM/PLL
  
  4. Restart requirement
     DCM_CLKGEN requires:
     DCM_RESET or DCM_RESTART after DRP writes

MMCM/PLL:
## Usage
python MDO_ADV_calc.py <family>
Examples:
python MDO_ADV_calc.py artix7
python MDO_ADV_calc.py ultrascale
python MDO_ADV_calc.py pll7
The script will prompt:
Enter input frequency (MHz):
Enter desired output frequency (MHz):

It then:
Searches for legal M, D, O satisfying:
𝐹VCO = 𝐹IN/(𝐷 ⋅ 𝑀)
𝐹OUT = 𝐹VCO/𝑂
within the device’s VCO and PFD limits.

For UltraScale MMCM families, it also considers fractional M and O
with a denominator of 8.

Computes DRP-friendly timing splits (HighTime/LowTime) for:
      DIVCLK, CLKFBOUT & CLKOUT0

Encodes DRP registers for:
      MMCM: 0x14, 0x15, 0x16, 0x01, 0x02

PLL:  same addresses, integer-only fields
Writes drp_config.json containing:
  family and type (MMCM or PLL)
  frequencies and error
  M, D, O (integer + fractional parts)
  DRP register map

Integration with cocotb
      Use the companion drp_driver.py or dcm_drp_driver.py to:
            Load drp_config.json 
            Apply DRP writes to target the MMCM/PLL or DCM 
            Optionally toggle reset and wait for LOCKED

    Example:
      python 
        from drp_driver import load_drp_config, apply_drp_config
        cfg = load_drp_config("drp_config.json")
        await apply_drp_config(dut, cfg)

    Always cross-check VCO/PFD ranges against the official device datasheet
    (UG472, UG572, DS181, DS189, etc.) for production designs.

# Unified MMCM/PLL DRP Reconfiguration Flow

This project provides:
- A multi-family MMCM/PLL clock calculator (`MDO_ADV_calc.py`)
- Automatic DRP register generation
- JSON export for simulation
- A cocotb DRP driver files which are currently under development 
  which are designed for cocotb co-simulation (`drp_driver.py`)
- A SystemVerilog MMCM/PLL wrapper (`mmcm_drp_wrapper.sv`)
- A Makefile and invoke tasks for one-command execution

Example Run
PS C:\test_MDO> python MDO_ADV_calc.py

**************************************************
MDO_ADV_calc.py : Running Python 3.12.0
Copyright � 2026 Telelinker Logic Solutions
All rights reserved
**************************************************

****MDO_ADV_calc.py  created: 2026-07-19  6:43 a.m.
Usage: python MDO_calc.py <family>
Families:
  - spartan7
  - artix7
  - kintex7
  - virtex7
  - ultrascale
  - ultrascale_plus
  - pll7
  - pll_ultrascale
  - pll_ultrascale_plus****


** Command must be entered with command line parameter <family> as shown below, if not supported family list will be displayed **


**PS C:\test_MDO> python MDO_ADV_calc.py pll_ultrascale_plus**

**************************************************
MDO_ADV_calc.py : Running Python 3.12.0
Copyright � 2026 Telelinker Logic Solutions
All rights reserved
**************************************************

MDO_ADV_calc.py  created: 2026-07-19  6:43 a.m.


Selected family: pll_ultrascale_plus (TYPE=PLL)

Enter input frequency (MHz): 115

Enter desired output frequency (MHz): 275.55


=== Clocking Solution ===

Type     : PLL

FIN      : 115.000 MHz

FOUT req : 275.550 MHz

FOUT act : 275.520833 MHz

M        : 115.000000 (int=115, frac=0/1)

D        : 8

O        : 6.000000 (int=6, frac=0/1)

FVCO     : 1653.125 MHz

FPFD     : 14.375 MHz

Error    : 105.8 ppm

DIVCLK   : high = 4 low = 4

CLKFBOUT : high = 58 low = 57

CLKOUT0  : high = 3 low = 3

DRP registers (hex):

  0x14 : 0x0000
  
  0x15 : 0x01C7
  
  0x16 : 0x0000
  
  0x01 : 0x0000
  
  0x02 : 0x0000




DRP configuration written to drp_config.json

{

  "family": "pll_ultrascale_plus",

  "type": "PLL",
  
  "fin_mhz": 115.0,
  
  "fout_mhz": 275.55,
  
  "m_int": 115,
  
  "m_frac": 0,
  
  "d": 8,
  
  "o_int": 6,
  
  "o_frac": 0,
  
  "fvco_mhz": 1653.125,
  
  "fpfd_mhz": 14.375,
  
  "error_ppm": 105.84890824422784,
  
  "divclk_high": 4,
  
  "divclk_low": 4,
  
  "clkfbout_high": 58,
  
  "clkfbout_low": 57,
  
  "clkout0_high": 3,
  
  "clkout0_low": 3,
  
  "drp_registers": {
  
    "0x14": 0,
    
    "0x15": 455,
    
    "0x16": 0,
    
    "0x01": 0,
    
    "0x02": 0
  
  }
  
