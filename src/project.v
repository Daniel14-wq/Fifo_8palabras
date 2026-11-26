`default_nettype none

module tt_um_Fifo (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    // FIFO de 4 posiciones de 8 bits.
    reg [7:0] mem [0:7];

    // Punteros y contador.
    reg [1:0] wr_ptr;
    reg [1:0] rd_ptr;
    reg [7:0] used;

    // Registro de salida.
    reg [7:0] data_out;
    reg       read_valid;

    // Señales internas.
    wire [7:0] data_in;
    wire write_en;
    wire read_en;

    wire full;
    wire empty;
    wire do_write;
    wire do_read;

    // BLOQUE 1. ENTRADAS
    assign data_in  = ui_in[7:0];

    // Controles desde pines bidireccionales.
    assign write_en = uio_in[0];
    assign read_en  = uio_in[1];

    // BLOQUE 2. ESTADOS DE LA FIFO
    assign full  = (used == 3'd8);
    assign empty = (used == 3'd0);

    // BLOQUE 3. CONTROL DE OPERACIONES
    assign do_write = write_en && !full;
    assign do_read  = read_en  && !empty;

    // BLOQUE 4. MEMORIA Y PUNTEROS
    always @(posedge clk) begin

        if (!rst_n) begin
            wr_ptr     <= 2'd0;
            rd_ptr     <= 2'd0;
            used       <= 7'd0;
            data_out   <= 8'd0;
            read_valid <= 1'b0;
        end

        else begin

            read_valid <= do_read;

            // ESCRITURA
            if (do_write) begin
                mem[wr_ptr] <= data_in;
                wr_ptr <= wr_ptr + 2'd1;
            end

            // LECTURA
            if (do_read) begin
                data_out <= mem[rd_ptr];
                rd_ptr <= rd_ptr + 2'd1;
            end

            // CONTADOR DE OCUPACION
            case ({do_write, do_read})

                2'b10:
                    used <= used + 7'd1;

                2'b01:
                    used <= used - 7'd1;

                default:
                    used <= used;

            endcase

        end
    end

    // BLOQUE 5. SALIDA DE DATOS
    assign uo_out = data_out;

    // BLOQUE 6. SALIDAS BIDIRECCIONALES
    assign uio_out[0] = 1'b0;
    assign uio_out[1] = 1'b0;

    assign uio_out[2] = full;
    assign uio_out[3] = empty;
    assign uio_out[4] = read_valid;

    assign uio_out[5] = used[0];
    assign uio_out[6] = used[1];
    assign uio_out[7] = used[2];

    // 0 = Entrada
    // 1 = Salida
    assign uio_oe = 8'b11111100;

    // Puerto no utilizado funcionalmente.
    wire _unused = &{ena, uio_in[7:2], 1'b0};

endmodule

`default_nettype wire
