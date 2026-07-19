# freq_meter.py

import cocotb
from cocotb.triggers import RisingEdge, Timer


async def measure_frequency(dut, sig, ref_clk, window_cycles: int, time_unit="ns"):
    """
    Measure frequency of 'sig' using 'ref_clk' as time base.
    Counts rising edges of sig over 'window_cycles' of ref_clk.
    Returns frequency in MHz.
    """
    # Wait for a clean start
    for _ in range(10):
        await RisingEdge(ref_clk)

    edge_count = 0
    start_time = dut._log.sim_time

    for _ in range(window_cycles):
        await RisingEdge(ref_clk)
        if sig.value:
            # detect rising edge of sig
            # simple: check previous value via a small delay
            pass

    # Better: sample sig directly on its own edges
    edge_count = 0
    start_time = dut._log.sim_time

    for _ in range(window_cycles):
        await RisingEdge(sig)
        edge_count += 1

    end_time = dut._log.sim_time
    sim_time_ns = (end_time - start_time)  # cocotb uses sim time units; assume ns

    period_ns = sim_time_ns / edge_count if edge_count > 0 else 0.0
    freq_mhz = 1000.0 / period_ns if period_ns > 0 else 0.0
    return freq_mhz


@cocotb.test()
async def test_mmcm_output_freq(dut):
    """
    Example: verify clk_out0 frequency after DRP reconfig.
    """
    from drp_driver import load_drp_config, apply_drp_config

    cfg = load_drp_config("drp_config.json")

    # Apply DRP configuration
    await apply_drp_config(dut, cfg)

    # Measure frequency of clk_out0 using dclk as reference
    freq_mhz = await measure_frequency(dut, dut.clk_out0, dut.dclk, window_cycles=1000)
    dut._log.info(f"Measured clk_out0 frequency: {freq_mhz:.3f} MHz")