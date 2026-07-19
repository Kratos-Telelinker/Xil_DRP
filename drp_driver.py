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

import json
import cocotb
from cocotb.triggers import RisingEdge, ReadOnly


async def drp_write(dut, addr: int, data: int):
    """
    Single DRP write transaction:
      - present address and data
      - pulse DEN/DWE
      - wait for DRDY
    """
    dut.daddr.value = addr
    dut.di.value    = data
    dut.den.value   = 1
    dut.dwe.value   = 1

    await RisingEdge(dut.dclk)
    dut.den.value   = 0
    dut.dwe.value   = 0

    # wait for DRDY
    while True:
        await RisingEdge(dut.dclk)
        if int(dut.drdy.value) == 1:
            break


async def drp_read(dut, addr: int) -> int:
    """
    Single DRP read transaction:
      - present address
      - pulse DEN
      - wait for DRDY
      - sample DO
    """
    dut.daddr.value = addr
    dut.den.value   = 1
    dut.dwe.value   = 0

    await RisingEdge(dut.dclk)
    dut.den.value   = 0

    while True:
        await RisingEdge(dut.dclk)
        if int(dut.drdy.value) == 1:
            break

    await ReadOnly()
    return int(dut.do.value)


def load_drp_config(path: str = "drp_config.json"):
    """
    Load DRP configuration JSON produced by MDO_calc.py.
    """
    with open(path, "r") as f:
        cfg = json.load(f)
    return cfg


async def apply_drp_config(dut, cfg: dict):
    """
    Apply DRP configuration to MMCM/PLL:
      - write all DRP registers from JSON
      - optionally toggle MMCM reset
      - wait for LOCK
    JSON format (from MDO_calc.py):
      cfg["drp_registers"] = { "0x14": value, "0x15": value, ... }
    """
    # Write DRP registers
    for addr_str, value in cfg["drp_registers"].items():
        addr = int(addr_str, 16)
        await drp_write(dut, addr, int(value))

    # Optional: reset MMCM/PLL if your DUT exposes a reset
    if hasattr(dut, "mmcm_rst"):
        dut.mmcm_rst.value = 1
        await RisingEdge(dut.dclk)
        dut.mmcm_rst.value = 0

    # Optional: wait for LOCK if your DUT exposes a lock signal
    if hasattr(dut, "mmcm_locked"):
        # wait up to some cycles for lock
        for _ in range(1000):
            await RisingEdge(dut.dclk)
            if int(dut.mmcm_locked.value) == 1:
                break


@cocotb.test()
async def test_drp_reconfigure(dut):
    """
    Example cocotb test:
      - load drp_config.json
      - apply DRP configuration
      - (optionally) check output clock behavior
    """
    cfg = load_drp_config("drp_config.json")

    # Initialize DRP interface to known state
    dut.den.value   = 0
    dut.dwe.value   = 0
    dut.daddr.value = 0
    dut.di.value    = 0

    # Apply configuration
    await apply_drp_config(dut, cfg)

    # At this point MMCM/PLL should be reconfigured.
    # You can add checks on mmcm_locked, output clock frequency, etc.