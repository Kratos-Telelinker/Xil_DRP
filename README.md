# MDO_calc — Multi-family MMCM/PLL Clock Calculator + DRP Encoder

`MDO_calc.py` is a command-line tool that computes legal clocking configurations
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

## Usage

```bash
python MDO_calc.py <family>
Examples:

bash
python MDO_calc.py artix7
python MDO_calc.py ultrascale
python MDO_calc.py pll7
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

DIVCLK

CLKFBOUT

CLKOUT0

Encodes DRP registers for:

MMCM: 0x14, 0x15, 0x16, 0x01, 0x02

PLL:  same addresses, integer-only fields

Writes drp_config.json containing:

family and type (MMCM or PLL)

frequencies and error

M, D, O (integer + fractional parts)

DRP register map

Integration with cocotb
Use the companion drp_driver.py to:

Load drp_config.json

Apply DRP writes to the MMCM/PLL

Optionally toggle reset and wait for LOCKED

Example:

python
from drp_driver import load_drp_config, apply_drp_config

cfg = load_drp_config("drp_config.json")
await apply_drp_config(dut, cfg)
Notes
DCM structures are not supported; they use different math and DRP maps.

PLL fractional divides are not supported by hardware; fractional logic is
only used for UltraScale MMCM families.

Always cross-check VCO/PFD ranges against the official device datasheet
(UG472, UG572, DS181, DS189, etc.) for production designs.

# Unified MMCM/PLL DRP Reconfiguration Flow

This project provides:

- A multi-family MMCM/PLL clock calculator (`MDO_calc.py`)
- Automatic DRP register generation
- JSON export for simulation
- A cocotb DRP driver (`drp_driver.py`)
- A SystemVerilog MMCM/PLL wrapper (`mmcm_drp_wrapper.sv`)
- A Makefile and invoke tasks for one-command execution

## Running the full flow

### Using Makefile

```bash
make FAMILY=ultrascale
This performs:

python3 MDO_calc.py ultrascale  
→ generates drp_config.json

Runs cocotb testbench
→ applies DRP writes
→ verifies MMCM/PLL lock
→ optionally measures output frequency

Using invoke
bash
invoke all --family=pll7
Files
MDO_calc.py  
Multi-family MMCM/PLL calculator + DRP encoder + JSON export

drp_driver.py  
Cocotb driver that loads drp_config.json and performs DRP writes

mmcm_drp_wrapper.sv  
SystemVerilog wrapper exposing DRP ports, reset, and lock

tests/  
Cocotb testbench directory

Supported families
MMCM:

spartan7, artix7, kintex7, virtex7

ultrascale, ultrascale_plus (fractional)

PLL:

pll7 (PLLE2_ADV)

pll_ultrascale (PLLE3)

pll_ultrascale_plus (PLLE4)

Output
drp_config.json contains:

M, D, O (integer + fractional)

FVCO, FPFD, error

DRP register map (0x01–0x16)

Family + type (MMCM or PLL)

This JSON is consumed directly by cocotb.
