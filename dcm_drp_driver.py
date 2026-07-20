#!/usr/bin/env python3

# Coding       : utf-8 
# Project      : MDO_Calc
# Package      : 
# Filename     : dcm_drp_driver.py
# Date         : 2026-07-19  6:43 a.m.
# AUTHOR       : Brad Balla kratos@telelinker.com
# Organization : Telelinker Logic Solutions

# Copyright � 2026 Telelinker Logic Solutions
# All rights reserved. 

# ----------------------------------------------------------------------
# Description

# ----------------------------------------------------------------------
# dcm_drp_driver.py

import json
import cocotb
from cocotb.triggers import RisingEdge, ReadOnly


async def dcm_drp_write(dut, addr: int, data: int):
    """
    Single DCM DRP write transaction.
    Assumes DCM exposes DCLK, DADDR, DI, DEN, DWE, DO, DRDY.
    """
    dut.daddr.value = addr
    dut.di.value    = data
    dut.den.value   = 1
    dut.dwe.value   = 1

    await RisingEdge(dut.dclk)

    dut.den.value   = 0
    dut.dwe.value   = 0

    while True:
        await RisingEdge(dut.dclk)
        if int(dut.drdy.value) == 1:
            break


async def dcm_drp_read(dut, addr: int) -> int:
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


def load_dcm_config(path: str = "dcm_config.json"):
    with open(path, "r") as f:
        return json.load(f)


async def apply_dcm_config(dut, cfg: dict):
    """
    Apply DCM configuration:
      - write DRP registers from JSON
      - optionally toggle DCM reset
      - optionally wait for LOCK
    """
    for addr_str, value in sorted(cfg["drp_registers"].items()):
        addr = int(addr_str, 16)
        await dcm_drp_write(dut, addr, int(value))

    if hasattr(dut, "dcm_rst"):
        dut.dcm_rst.value = 1
        await RisingEdge(dut.dclk)
        dut.dcm_rst.value = 0

    if hasattr(dut, "dcm_locked"):
        for _ in range(2000):
            await RisingEdge(dut.dclk)
            if int(dut.dcm_locked.value) == 1:
                break


@cocotb.test()
async def test_dcm_reconfigure(dut):
    cfg = load_dcm_config("dcm_config.json")

    dut.den.value   = 0
    dut.dwe.value   = 0
    dut.daddr.value = 0
    dut.di.value    = 0

    await apply_dcm_config(dut, cfg)

    if hasattr(dut, "dcm_locked"):
        assert int(dut.dcm_locked.value) == 1, "DCM failed to lock after DRP reconfiguration"