# Console138K UART8受信・SDRAM格納の並行化

2026年11月8日（日本時間）。共通tagは `uart8-overlap-hw-20261108`、3 repositoryの統合先は `tangcore-integrated`。
通常版firmwareと対応SNES coreで、2 MiB・4 MiBの起動・下段表示・OSD1からの一覧復帰を利用者が確認した。

## 対応するsourceと通常版

| repository | commit |
| --- | --- |
| firmware-bl616 | `6744940d6a1a84f677c9bd4e73696788bf3fb1de` |
| snestang | `d4d46357a226ce77b08b78cf4be938fc6111bb80` |

親repositoryのgitlinkは上記commitを指す。
通常版の配布は[verified-normal-pair.zip](../../verification/uart8-overlap-20261108/verified-normal-pair.zip)、
計測用は[verified-trace-pair.zip](../../verification/uart8-overlap-20261108/verified-trace-pair.zip)。
各ZIPのrelease-manifest.jsonにsource commit、SHA256SUMSに収録ファイルの照合値がある。

| 対象 | byte数 | SHA-256 |
| --- | ---: | --- |
| 通常版firmware | 238,896 | `d183f55bfa2fd91215f70f0a6c499140d504e19f10159f5a4fd9e594d8f89e60` |
| 計測版firmware | 241,744 | `d901978c4437c9e55b9ca2b45860a64fe43cda8b68a4e7a5ce2312f81f167e2e` |
| SNES core | 4,733,130 | `e2dc7702b9f5bfc9c9401cd36c2dd4b3935d1e21499a3f51806f2b978ef37f7b` |

## 実装

- UARTの設定は8 Mbit/s・8N1のまま。最大2件のDATAを先行し、前のDATAのSDRAM格納と次のUART受信を重ねる。
- 共通C++ Sessionが送信credit、CRC、session、連番、ACK・再送を管理し、UART adapterはDMA・物理送信・応答byte・速度切替を扱う。SPIにも共用できる構造を維持した。
- FPGAは4096 byteの受信FIFOと1024 byte×3 bankを使用する。直近2件のcommit済みpayloadを保持し、完全一致の再送だけをACKする。
- ACKは格納完了後、ENDは実際のSDRAMを全ROM分読み戻して照合後に返す。異常時はゲームのresetを保持する。
- 2件目のACKだけでは先頭の送信creditを解放しない。各DATAは最大4回。破損で後続がorderになった場合は先行replyを回収してから古い順に再送する。
- Window=2を確認して有効化する。旧coreの明示的なformat応答では8 Mbit/sの1件転送へ戻り、無応答は失敗とする。
- 最下段のPreparing SNES core → ROM transfer 0～100%（5%刻み）→ Verifying ROMを維持する。

詳細仕様はfirmware-bl616とsnestangの `docs/rom/ROMXFR1.md` に記載する。SPIの物理信号は未実装。

## 実機測定

| 区間 | マリオコレクション（2 MiB） | ドンキーコング（4 MiB） |
| --- | ---: | ---: |
| 旧8 Mbit/sのROM転送 | 3.988683秒 | 7.953412秒 |
| 並行化後のROM転送 | 3.237535秒 | 6.467952秒 |
| 転送時間の短縮率 | 18.83% | 18.68% |
| 再送（旧→新） | 0→0回 | 0→0回 |
| END照合・ACK待ち（新） | 0.487760秒 | 0.975412秒 |
| firmware処理全体（旧→新） | 11.004571→10.141644秒 | 16.235597→14.631731秒 |
| 確定→タイトル（新・手動） | 14.05秒 | 26.50秒 |

ROM転送はRomBegin→RomQueued（全DATA ACK完了）、ENDは別区間。2本ともwindow=2、CRCは元ROMからの独立計算と旧記録に一致した。
firmware全体はAccepted→Finishedで、タイトル表示とは境界が異なる。全体の短縮にはcore書換え時間の約0.11～0.12秒短縮も含む。
各条件・各タイトル1回。過去の最終通常版と今回の通常版ではタイトル到達を再計時しておらず、手動値の厳密な同一条件の短縮率は算出しない。

## 通常版の適用と確認

計測版から通常版（TC_LAUNCH_TRACE=OFF）へ切り替え、BOOT再接続後に全flashを独立して読み戻した。
firmwareとの一致に加え、boot領域と0x80000以降が保存前の内容と一致した。
全flashのSHA-256は `02e00d00914db31ce68ed63d5f2caf6d5c4f45c7f3f1e81fdb2c3bd68814c77f`。
coreは変更せず、PC側の監査でmicroSDの83 user filesの内容・属性・更新日時が一致した。保存はuser file単位で、sector imageではない。

通常版の利用者確認は「2本とも起動・下段表示・一覧復帰が正常でした」。対象は上記2本、各1回。
現在の実機は通常版を保持している。

## PC検証とtiming

共通C++と実際の受信RTL・SNES sinkで2／4 MiB、CRC破損、ACK消失・破損、直近2件の再送、異なるpayload、奇数byte分割、SDRAM停止・読み戻し破損、FIFO超過を確認した。
UARTの2→8→2 Mbit/s、連続8N1、bit周期±2%、watchdog、旧coreとの互換、実DMA adapter、UI・OSD・入力・CRT回帰試験が通過した。
UART固有制御を外した共通C++／RTLも試験した。公開コードは試験・build・実機適用した作業ソースと改行形式を除いて一致する。

Gowin 1.9.12.03で `gw_sh build_console138k_usb.tcl console138k ds2` を実行した。
適用制約下のsetup／hold違反0／0件、Fmaxは80 MHz系80.173 MHz、96 MHz系96.372 MHz。既存PLL警告を保持した。
追加controller、長時間連続動作、電源異常、物理SPIは未検証。

実機確認・測定・配布物の照合値は[verification/uart8-overlap-20261108](../../verification/uart8-overlap-20261108/)を参照する。
旧tagとその配布物は前段の直列転送版の記録として保持する。
