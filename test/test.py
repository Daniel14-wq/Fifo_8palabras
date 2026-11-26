
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.triggers import Timer


@cocotb.test()
async def test_fifo_8(dut):

    dut._log.info("INICIANDO PRUEBAS FIFO 8x8")

    # CONFIGURACION INICIAL
    dut.ena.value = 1
    dut.clk.value = 0
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    tests = 0

    # RELOJ DE 10 MHz
    # Periodo = 100 ns
    async def ciclo(dato=0, escribir=0, leer=0):

        dut.clk.value = 0
        dut.ui_in.value = dato

        # uio_in[0] = WRITE
        # uio_in[1] = READ
        dut.uio_in.value = escribir | (leer << 1)

        await Timer(50, unit="ns")

        dut.clk.value = 1

        await Timer(50, unit="ns")

    # OBTENER ESTADOS DE LA FIFO
    def obtener_estado():

        salida = int(dut.uo_out.value)
        uio = int(dut.uio_out.value)

        full = (uio >> 2) & 1
        empty = (uio >> 3) & 1
        read_valid = (uio >> 4) & 1

        count = (uio >> 5) & 0x07

        # Recuperar el valor de 8 palabras
        # mediante la bandera FULL
        if full:
            count = 8

        return salida, full, empty, count, read_valid

    # VERIFICAR ESTADOS
    def verificar(cantidad, valido, dato):

        salida, full, empty, count, read_valid = (
            obtener_estado()
        )

        assert count == cantidad, (
            f"ERROR COUNT: esperado={cantidad}, "
            f"recibido={count}"
        )

        assert full == int(cantidad == 8), (
            "ERROR FULL"
        )

        assert empty == int(cantidad == 0), (
            "ERROR EMPTY"
        )

        assert read_valid == valido, (
            "ERROR READ_VALID"
        )

        assert salida == dato, (
            f"ERROR DATA_OUT: esperado={dato}, "
            f"recibido={salida}"
        )

        # Verificar los tres bits fisicos de COUNT
        uio = int(dut.uio_out.value)
        count_bits = (uio >> 5) & 0x07

        assert count_bits == (cantidad & 0x07), (
            "ERROR BITS DE COUNT"
        )

    # FUNCION DE ESCRITURA
    async def write_data(valor):

        await ciclo(dato=valor, escribir=1)

        salida, full, empty, count, valido = (
            obtener_estado()
        )

        dut._log.info(
            f"WRITE {valor} | "
            f"ocupacion={count} | full={full}"
        )

    # FUNCION DE LECTURA
    async def read_data(esperado):

        await ciclo(leer=1)

        salida, full, empty, count, valido = (
            obtener_estado()
        )

        assert salida == esperado, (
            f"ERROR: esperado={esperado}, "
            f"recibido={salida}"
        )

        assert valido == 1, (
            "ERROR READ_VALID"
        )

        dut._log.info(
            f"READ OK: {salida} | "
            f"ocupacion={count}"
        )

    # ====================================
    # PRUEBA 1: FIFO VACIA
    # ====================================

    dut._log.info(
        "===== PRUEBA 1: FIFO VACIA ====="
    )

    await ciclo()
    await ciclo()

    verificar(0, 0, 0)

    assert int(dut.uio_oe.value) == 0xFC

    dut.rst_n.value = 1

    tests += 1

    dut._log.info("PRUEBA 1 APROBADA")

    # ====================================
    # PRUEBA 2: ESCRITURA
    # ====================================

    dut._log.info(
        "===== PRUEBA 2: ESCRITURA ====="
    )

    datos = [3, 7, 12, 5, 56, 233, 100, 170]

    for cantidad, dato in enumerate(datos, 1):

        await write_data(dato)

        verificar(cantidad, 0, 0)

    verificar(8, 0, 0)

    tests += 1

    dut._log.info("PRUEBA 2 APROBADA")

    # ====================================
    # PRUEBA 3: FIFO LLENA
    # ====================================

    dut._log.info(
        "===== PRUEBA 3: FIFO LLENA ====="
    )

    # Intentar escribir una novena palabra
    await write_data(9)

    # La palabra debe ser rechazada
    verificar(8, 0, 0)

    tests += 1

    dut._log.info("PRUEBA 3 APROBADA")

    # ====================================
    # PRUEBA 4: LECTURA FIFO
    # ====================================

    dut._log.info(
        "===== PRUEBA 4: LECTURA FIFO ====="
    )

    for indice, esperado in enumerate(datos):

        await read_data(esperado)

        verificar(
            7 - indice,
            1,
            esperado
        )

    verificar(0, 1, 170)

    tests += 1

    dut._log.info("PRUEBA 4 APROBADA")

    # ====================================
    # PRUEBA 5: LECTURA VACIA
    # ====================================

    dut._log.info(
        "===== PRUEBA 5: LECTURA VACIA ====="
    )

    await ciclo(leer=1)

    # No se permite la lectura
    # Se conserva el ultimo dato
    verificar(0, 0, 170)

    tests += 1

    dut._log.info("PRUEBA 5 APROBADA")

    # ====================================
    # PRUEBA 6: OPERACION SIMULTANEA
    # ====================================

    dut._log.info(
        "===== PRUEBA 6: SIMULTANEA ====="
    )

    await write_data(6)
    verificar(1, 0, 170)

    await write_data(8)
    verificar(2, 0, 170)

    # Escribir 10 y leer 6 simultaneamente
    await ciclo(
        dato=10,
        escribir=1,
        leer=1
    )

    verificar(2, 1, 6)

    # Leer los datos restantes
    await read_data(8)
    verificar(1, 1, 8)

    await read_data(10)
    verificar(0, 1, 10)

    tests += 1

    dut._log.info("PRUEBA 6 APROBADA")

    # ====================================
    # PRUEBA 7: RESET
    # ====================================

    dut._log.info(
        "===== PRUEBA 7: RESET ====="
    )

    await write_data(11)

    verificar(1, 0, 10)

    # RESET ACTIVO EN BAJO
    dut.rst_n.value = 0

    await ciclo()

    verificar(0, 0, 0)

    dut.rst_n.value = 1

    tests += 1

    dut._log.info("PRUEBA 7 APROBADA")

    # ====================================
    # RESULTADOS FINALES
    # ====================================

    dut._log.info("==============================")

    dut._log.info(
        f"PRUEBAS EJECUTADAS: {tests}"
    )

    dut._log.info("ERRORES: 0")

    dut._log.info(
        "RESULTADO: TODAS LAS PRUEBAS APROBADAS"
    )

    dut._log.info("==============================")

