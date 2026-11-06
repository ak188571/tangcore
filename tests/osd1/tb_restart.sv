`timescale 1ns/1ps
module tb_restart;
    localparam FREQ=32000000;
    reg clk=0,hclk=0,resetn=0,uart_rx=1;
    always #5 clk=~clk;
    always #2 hclk=~hclk;
    wire uart_tx,game_reset,unsupported_reset;
    wire [7:0] rom_loading,rom_do;
    wire rom_do_valid;
    wire [31:0] core_config,osd_window;
    wire osd_input_block;
    reg [11:0] joy1=0,joy2=0;
    iosys_bl616 #(.FREQ(FREQ),.SUPPORT_RESTART(1)
`ifdef HAS_SNES_CRT
        ,.SUPPORT_CRT(1)
`endif
    ) dut(
        .clk(clk),.hclk(hclk),.resetn(resetn),.uart_rx(uart_rx),.uart_tx(uart_tx),
        .game_reset(game_reset),.overlay_x(8'b0),.overlay_y(8'b0),
        .joy1(joy1),.joy2(joy2),.osd_visible(1'b0),.osd_input_block(osd_input_block),
        .rom_loading(rom_loading),.rom_do(rom_do),.rom_do_valid(rom_do_valid),
        .core_config(core_config),.osd_window(osd_window),
`ifdef HAS_CRT
        .crt_config_applied(32'h001b1234),
`endif
        .mgmt_readdata(16'b0),.fdd_request(2'b0));
    iosys_bl616 #(.FREQ(FREQ)) unsupported(
        .clk(clk),.hclk(hclk),.resetn(resetn),.uart_rx(uart_rx),
        .game_reset(unsupported_reset),.overlay_x(8'b0),.overlay_y(8'b0),
        .joy1(12'b0),.joy2(12'b0),.osd_visible(1'b0),
`ifdef HAS_CRT
        .crt_config_applied(32'b0),
`endif
        .mgmt_readdata(16'b0),.fdd_request(2'b0));
    wire [7:0] received_byte;
    wire received_valid;
    async_receiver #(.ClkFrequency(FREQ),.Baud(2000000)) monitor(
        .clk(clk),.RxD(uart_tx),.RxD_data(received_byte),.RxD_data_ready(received_valid));
    byte unsigned received[$];
    integer reset_ticks=0,reset_starts=0,rom_writes=0;
    reg was_reset=0,check_retained=0;
    always @(posedge clk)begin
        if(received_valid)received.push_back(received_byte);
        if(resetn)begin
            if(unsupported_reset)$fatal(1,"disabled core reset");
            if(game_reset)reset_ticks++;
            if(game_reset&&!was_reset)reset_starts++;
            if(rom_do_valid)rom_writes++;
            if(check_retained&&(rom_loading!=0||rom_do_valid||core_config!=32'h001b1234||osd_window!=32'h02031406))
                $fatal(1,"restart changed loading/data/config/window");
        end
        was_reset<=game_reset;
    end
    task automatic send_byte(input byte unsigned value);
        @(negedge clk);uart_rx=0;repeat(16)@(negedge clk);
        for(integer bitnum=0;bitnum<8;bitnum++)begin uart_rx=value[bitnum];repeat(16)@(negedge clk);end
        uart_rx=1;repeat(32)@(negedge clk);
    endtask
    task automatic header(input byte unsigned len,input byte unsigned cmd);
        send_byte(8'haa);send_byte(0);send_byte(len);send_byte(cmd);
    endtask
    task automatic set_overlay(input byte unsigned value);
        header(2,8'h08);send_byte(value);repeat(100)@(negedge clk);
    endtask
    initial begin
        repeat(10)@(negedge clk);resetn=1;repeat(100)@(negedge clk);
        set_overlay(0);
        if(osd_input_block)$fatal(1,"initial release failed");
        joy2=12'h184;repeat(10)@(negedge clk);
        if(osd_input_block)$fatal(1,"P2 opened OSD");
        joy2=0;joy1=12'h184;repeat(10)@(negedge clk);
        if(!osd_input_block)$fatal(1,"P1 OSD1 chord leaked");
        joy1=12'h004;repeat(10)@(negedge clk);
        if(!osd_input_block)$fatal(1,"partly released chord leaked");
        joy1=0;repeat(10)@(negedge clk);
        if(osd_input_block)$fatal(1,"full release failed");
        joy1=12'h0c4;repeat(10)@(negedge clk);
        if(!osd_input_block)$fatal(1,"ambiguous chord leaked");
        joy1=0;repeat(10)@(negedge clk);set_overlay(1);
        // Capability response passes through the real serial TX and receiver.
        header(1,2);repeat(25000)@(negedge clk);
        begin
            bit found=0;
            for(integer k=6;k<received.size();k++)
                if({received[k-6],received[k-5],received[k-4],received[k-3],received[k-2],received[k-1],received[k]}=="RSTROM1")found=1;
            if(!found)$fatal(1,"restart capability absent");
        end
        // Model an already loaded ROM via the existing serial interface.
        header(2,6);send_byte(1);
        header(5,7);send_byte(8'h4e);send_byte(8'h45);send_byte(8'h53);send_byte(8'h1a);
        header(1,8'h13);repeat(100)@(negedge clk);
        if(game_reset||reset_starts)$fatal(1,"restart accepted during ROM loading");
        header(2,6);send_byte(0);
        header(5,3);send_byte(0);send_byte(8'h1b);send_byte(8'h12);send_byte(8'h34);
        header(5,8'h10);send_byte(2);send_byte(3);send_byte(20);send_byte(6);
        repeat(100)@(negedge clk);
        if(rom_writes!=4)$fatal(1,"test ROM transfer failed");
        check_retained=1;
        // Both short/long malformed commands must be inert.
        header(0,8'h13);header(2,8'h13);send_byte(0);
        repeat(100)@(negedge clk);
        if(reset_starts)$fatal(1,"wrong-length restart accepted");
        set_overlay(0);header(1,8'h13);repeat(100)@(negedge clk);
        if(reset_starts)$fatal(1,"restart accepted without OSD ownership");
        set_overlay(1);header(1,8'h13);repeat(100)@(negedge clk);
        if(!game_reset||!osd_input_block)$fatal(1,"restart did not assert with blocked input");
        // Repeated requests do not prolong an in-progress pulse.
        header(1,8'h13);header(1,8'h13);
        wait(!game_reset);repeat(5)@(negedge clk);
        if(reset_ticks!=FREQ/50||reset_starts!=1||rom_writes!=4)
            $fatal(1,"bad reset duration/repetition/data: ticks=%0d starts=%0d writes=%0d",reset_ticks,reset_starts,rom_writes);
        header(1,8'h13);repeat(100)@(negedge clk);
        if(!game_reset)$fatal(1,"second independent restart failed");
        wait(!game_reset);repeat(5)@(negedge clk);
        if(reset_starts!=2||reset_ticks!=2*(FREQ/50))$fatal(1,"second pulse duration");
        set_overlay(0);repeat(10)@(negedge clk);
        if(osd_input_block)$fatal(1,"input did not resume");
        $display("RESTART PASS: actual UART, capability, two bounded resets, no ROM retransmission, config/window retained, loading/length/ownership/default-off guards");
        $finish;
    end
    initial begin #30000000;$fatal(1,"restart timeout");end
endmodule
