#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
core="${1:-}"
case "$core" in
  nes) repo=nestang; extra=(-DHAS_CRT) ;;
  snes) repo=snestang; extra=(-DHAS_CRT -DHAS_SNES_CRT -DHAS_SNES_BLUR) ;;
  *) echo 'Usage: tools/test_osd1_restart.sh nes|snes' >&2; exit 2 ;;
esac
flags=(-CFLAGS '-std=c++17')
suffix=''
if command -v cygpath >/dev/null 2>&1; then
  export PATH=/ucrt64/bin:/usr/bin:$PATH
  export MSYS2_ARG_CONV_EXCL='*'
  flags=(-CFLAGS '-BC:/msys64/ucrt64/bin/ -std=c++17' -LDFLAGS '-BC:/msys64/ucrt64/bin/ -mconsole')
  suffix='.exe'
fi
out="build-osd1-tests/$core"
mkdir -p "$out"
# Replace the upstream empty, string-port assertion guard only for simulation.
sed 's/ASSERTION_ERROR PARAMETER_OUT_OF_RANGE("[^"]*");/initial $fatal(1,"UART parameter range");/' \
 "$repo/src/iosys/uart_fixed.v" > "$out/uart_fixed_test.v"
verilator --binary --timing --assert -Wno-fatal -DSIM --top-module tb_restart \
 --Mdir "$out/sim" -j 4 "${extra[@]}" \
 -I"$repo/src/iosys" tests/osd1/tb_restart.sv \
 "$repo/src/iosys/iosys_bl616.v" "$out/uart_fixed_test.v" \
 "${flags[@]}" > "$out/build.log" 2>&1
"$out/sim/Vtb_restart$suffix" | tee "$out/result.log"
