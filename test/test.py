
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def test_fifo_8x8(dut):

    dut._log.info("INICIANDO PRUEBA FIFO 8x8")

    # CONFIGURACION INICIAL
    dut.ena.value = 1
    dut.clk.value = 0
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    # RELOJ DE 50 MHz (PERIODO 20 ns)
    async def ciclo(dato=0, escribir=0, leer=0):

        dut.clk.value = 0
        dut.ui_in.value = dato

        # uio_in[0] = WRITE
        # uio_in[1] = READ
        dut.uio_in.value = escribir | (leer << 1)

        await Timer(10, unit="ns")

        dut.clk.value = 1
        await Timer(10, unit="ns")

    # VERIFICACION DEL ESTADO
    def verificar(cantidad, valido, dato):

        salida = int(dut.uo_out.value)
        uio = int(dut.uio_out.value)

        full = (uio >> 2) & 1
        empty = (uio >> 3) & 1
        read_valid = (uio >> 4) & 1

        # Tres bits visibles del contador
        used = (uio >> 5) & 0x07

        assert used == (cantidad & 0x07), (
            f"USED incorrecto: {used}"
        )

        assert full == int(cantidad == 8), (
            f"FULL incorrecto: {full}"
        )

        assert empty == int(cantidad == 0), (
            f"EMPTY incorrecto: {empty}"
        )

        assert read_valid == valido, (
            f"READ_VALID incorrecto: {read_valid}"
        )

        assert salida == dato, (
            f"Dato esperado {dato}, recibido {salida}"
        )

    # PRUEBA 1: RESET
    await ciclo()
    verificar(0, 0, 0)

    assert int(dut.uio_oe.value) == 0xFC

    dut.rst_n.value = 1
    dut._log.info("RESET CORRECTO")

    # PRUEBA 2: ESCRIBIR 8 PALABRAS
    datos = [25, 100, 200, 255, 30, 110, 120, 230]

    for cantidad, dato in enumerate(datos, 1):

        await ciclo(dato=dato, escribir=1)
        verificar(cantidad, 0, 0)

        dut._log.info(
            f"ESCRITURA {cantidad}: {dato}"
        )

    # PRUEBA 3: FIFO LLENA
    verificar(8, 0, 0)

    await ciclo(dato=50, escribir=1)

    # La escritura extra debe ser rechazada
    verificar(8, 0, 0)

    dut._log.info("FIFO LLENA CORRECTAMENTE")

    # PRUEBA 4: LEER LAS 8 PALABRAS
    for indice, esperado in enumerate(datos):

        await ciclo(leer=1)

        cantidad = 7 - indice

        verificar(
            cantidad,
            1,
            esperado
        )

        dut._log.info(
            f"LECTURA {indice + 1}: {esperado}"
        )

    # PRUEBA 5: LECTURA EN VACIO
    await ciclo(leer=1)

    # Se conserva el ultimo dato leido
    verificar(0, 0, datos[-1])

    dut._log.info("FIFO VACIA CORRECTAMENTE")

    # PRUEBA 6: REINICIO FINAL
    dut.rst_n.value = 0

    await ciclo()
    verificar(0, 0, 0)

    dut._log.info("RESET FINAL CORRECTO")

    dut._log.info(
        "TODAS LAS PRUEBAS FIFO 8x8 PASARON"
    )
