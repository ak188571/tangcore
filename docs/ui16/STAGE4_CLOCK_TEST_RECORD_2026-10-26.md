# TangCore UI16：PLL警告の切分けと実機試験

日付：2026年10月26日。作業元は第3段階 version 2 の実機検証済み版。`sources/` と第3段階の作業コピーは変更していない。microSD上の動作版monitor（SHA-256 `FDFE22E845E80900F38BFD559E44E821579E964B626BEDC30FB60BCFED49FFF3`）を `reference/working-monitor.bin` に保存した。

## 背景

動作版のGowin EDA buildには `PA1019` が2件あり、PLL27のVCOは1350 MHz、PLL74のVCOは1485 MHzで、工具が示す650～1300 MHzの範囲を超える。出力は27 MHz、74.25 MHz、371.25 MHz。`PR1014` は基板で固定された `sys_clk` のV22端子を経由するclock配線について残る。動作版のtimingはsetup/hold違反0、50 MHz系Fmax 78.329 MHz。

Gowinの[Arora V Clock User Guide](https://www.gowinsemi.com/upload/database_doc/2465/document_ja/65c1e6a70eb0d.pdf)に従い、MDIVと出力0のODIVの1/8単位の小数分周を候補にした。`check_pll.py` はVerilog、IPC、MODの分周値と計算上のVCO・出力周波数の一致を検査する。

## 個別候補とbuild

| 候補 | PLL27 VCO | PLL74 VCO | 実機 | PA1019 | setup/hold違反 |
|---|---:|---:|---|---:|---:|
| 動作版 | 1350 MHz | 1485 MHz | 第3段階で正常 | 2 | 0/0 |
| `monitor`：PLL27整数分周 | 675 MHz | 1485 MHz | 映像信号なし | 1 | 0/0 |
| `monitor-pll27-frac`：PLL27小数分周 | 1012.5 MHz | 1485 MHz | 映像・日本語menu・上下操作は正常 | 1 | 0/0 |
| `monitor-pll74-only`：PLL74小数分周 | 1350 MHz | 1113.75 MHz | 未実施 | 1 | 0/0 |
| `monitor-combined-frac`：両PLL小数分周 | 1012.5 MHz | 1113.75 MHz | 映像・日本語menu・上下操作は正常 | 0 | 0/0 |

PLL27整数分周候補は `IDIV=2, MDIV=27, ODIV0=25`。Gowin buildは通ったが、実機で映像信号が出なかった。直ちに動作版を復元し、microSDの全60 fileのSHA-256一致を確認した。利用者は映像・menuの復旧を確認した。

PLL27小数分周候補は `IDIV=1, MDIV=20.25, ODIV0=37.5` とし、VCO1012.5 MHz、出力27 MHz。microSDへ導入後に読戻しSHA-256 `B8956419784DB3AD365E741F7FA48FFC1BFBBDC3856B17833073FA51BFA81D60` を確認した。利用者は映像、日本語表示、上下操作が正常と報告した。

PLL74小数分周候補は `IDIV=1, MDIV=41.25, ODIV0=15, ODIV1=3` とし、VCO1113.75 MHz、出力74.25/371.25 MHz。両PLL変更版はGowin buildでPA1019が0件になり、setup/hold違反0、50 MHz系Fmax 78.329 MHz。binary SHA-256は `E01027299E356C353E7C30827FDBCD852C0BB41AB0D71EBC765CAB1F82833121`。microSDへ導入し、読戻しSHA-256が一致した。利用者は映像、日本語表示、上下操作が正常と報告した。

## font欠落時の実機試験

両PLL変更版で、元のfontを同じmicroSD内の別名に退避し、4語の試験用folderを導入した。退避fileのSHA-256は元の `font16.ui16` と一致。利用者は「新天地」「薔薇」「麒麟」「鬱」が□に置き換わり、上下操作、folderからの復帰、画面表示は正常と確認した。fontを元の場所へ復元し、試験用folderを撤去した。microSDの全60 fileについて、monitor以外は第3段階の最終記録とSHA-256が一致し、monitorは両PLL変更版のSHA-256と一致した。復元後の通常menuでも日本語表示と上下操作が正常だった。復元記録は `font-fault-restore.json`。

## 安全措置と既知の警告

- 各候補は独立したmonitorコピーでbuildし、変更したsourceは対応するPLLの `.v`、`.ipc`、`.mod` に限定した。
- microSDの識別は `TANGCONSOLE` / FAT32、導入前後にmonitorとfontのSHA-256を照合した。元の全60 fileの照合記録は `pll27-restore.json` などに保存した。
- 両PLL変更版の実機で映像・日本語menu・上下操作・folder出入り・NES/SNES起動と操作・OSD復帰・S1のLED全点灯が正常。
- 第3段階で通過したBL616 host回帰15件、Verilator RTL試験7件、BL616送信byte列とRTL受信器の境界試験のsourceは変えていない。今回の変更対象はPLL設定file6件だけである。
- 既存の `PR1014` は残る。基板配線を変更せず、timing結果を確認する。

## 参照した公式資料

- [Gowin Arora V Clock User Guide](https://www.gowinsemi.com/upload/database_doc/2465/document_ja/65c1e6a70eb0d.pdf)
- [Gowin Software User Messages Reference](https://cdn.gowinsemi.com.cn/SUG937E.pdf)
