
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

    // FIFO de 8 palabras de 8 bits
    reg [7:0] mem [0:7];

    // Punteros de escritura y lectura
    reg [2:0] wr_ptr;
    reg [2:0] rd_ptr;

    // Contador de ocupacion
    reg [3:0] used;

    // Registro de salida
    reg [7:0] data_out;
    reg read_valid;

    // Senales internas
    wire [7:0] data_in;
    wire write_en;
    wire read_en;

    wire full;
    wire empty;
    wire [3:0] count;

    wire do_write;
    wire do_read;

    // ENTRADAS
    assign data_in = ui_in[7:0];
    assign write_en = uio_in[0];
    assign read_en  = uio_in[1];

    // ESTADOS DE LA FIFO
    assign count = used;
    assign full  = (used == 4'd8);
    assign empty = (used == 4'd0);

    // CONTROL DE OPERACIONES
    assign do_write = write_en && !full;
    assign do_read  = read_en  && !empty;

    always @(posedge clk) begin

        if (!rst_n) begin

            wr_ptr     <= 3'd0;
            rd_ptr     <= 3'd0;
            used       <= 4'd0;
            data_out   <= 8'd0;
            read_valid <= 1'b0;

        end

        else begin

            read_valid <= do_read;

            // ESCRITURA
            if (do_write) begin
                mem[wr_ptr] <= data_in;
                wr_ptr <= wr_ptr + 3'd1;
            end

            // LECTURA
            if (do_read) begin
                data_out <= mem[rd_ptr];
                rd_ptr <= rd_ptr + 3'd1;
            end

            // CONTADOR DE OCUPACION
            case ({do_write, do_read})

                2'b10:
                    used <= used + 4'd1;

                2'b01:
                    used <= used - 4'd1;

                default:
                    used <= used;

            endcase

        end
    end

    // SALIDA DE DATOS
    assign uo_out = data_out;

    // SALIDAS BIDIRECCIONALES
    assign uio_out[0] = 1'b0;
    assign uio_out[1] = 1'b0;

    assign uio_out[2] = full;
    assign uio_out[3] = empty;
    assign uio_out[4] = read_valid;

    assign uio_out[5] = count[0];
    assign uio_out[6] = count[1];
    assign uio_out[7] = count[2];

    // CONFIGURACION DE PINES
    // 0 = Entrada
    // 1 = Salida
    assign uio_oe = 8'b11111100;

    // Senales no utilizadas
    wire _unused = &{ena, uio_in[7:2],
                     count[3], 1'b0};

endmodule

`default_nettype wire

