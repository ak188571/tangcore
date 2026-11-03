# CRT表示とOSD2の実装 第1段階

基準は `ak188571/tangcore` の `tangcore-integrated`、親commit `a67003941a26ccc856134f0d9142298d94b34483`。
作業用branchは親と変更対象submoduleの `crt-osd2-stage1`。対象はConsole138KのNES。

## 今回の到達点

ゲームのRGB生成とOSD合成の間に、遅延を追加しない `crt_filter` のbypassを挿入した。設定値は既存の `core_config` 経由で受信し、保持したbusとrequest/acknowledgeでpixel clock側へ渡し、frame開始時に一括反映する。受領ではなくframeでの適用後にacknowledgeを返す。転送中の変更は最新値へまとめる。

OSD1はPlayer 1のSELECT＋右で開き、中央固定とした。OSD2はPlayer 1のSELECT＋左で独立して開き、中央と四隅の5位置から選べる。表示中のもう一方の呼出しは無視する。両方の呼出しが同時成立した場合は入力を予約するが画面を開かない。呼出し時に余分なbuttonがあっても予約を維持する。

対応coreは `OSDWIN1;CRTSTG1` を通知する。OSDWIN1だけの旧coreではOSD2を開かず、従来の入力経路を使う。`CRTSTG1` は画質効果の対応を意味せず、bypass段階の接続・設定転送に対応することを意味する。

OSD2には次を表示する。

- `BYPASS ONLY - STAGE 1`
- `SESSION ONLY / NO SAVE`
- `CRT REQUEST`、`H BLUR REQ`、`SCANLINE REQ`
- `APPLY: WAITING` または `APPLY: FRAME ACK`
- `CLOSE` と `POS`

左右で要求値を変更する。A/Bでも値を進められる。X/YまたはCLOSEでゲームへ戻る。画面から戻った後も、既存の全button解放待ちを通る。位置と要求値はセッション内のみ保持し、新しいROMの起動時にCRT要求値を初期化する。

## 意図的に含めていない機能

水平方向のぼかし、走査線の演算、推奨値の解決、Reset to Recommended、設定のファイル保存、controller別profile、hold timeは次段階とする。要求値をONにしても、この版のRGBは変わらない。未実装の保存や推奨値への復帰を、動く項目として表示しない。

OSD1の既存項目は保持した。ROM保持型のRestart Gameは今回追加していない。OSD1の2項目化と再起動方式の実装が完了したことを意味しない。

FPGAからBL616へ通知される直結入力は、既存どおり複数の入力sourceをPlayer単位で合成している。BL616 USBとの跨いだ組合せは避けているが、FPGA内で既に合成されたUSBとDS2等を後から識別する機能は未実装。完全なsource別profileは別の通信拡張が必要となる。

組合せ成立以前に押された単独buttonはゲームへ届き得る。成立後の予約をFPGAで行い、BL616 USBでは判定をゲーム向け送信より前に行う。最初の構成buttonから予約する方式や長押しは今回導入していない。

## 設定interface

UARTの既存command `0x03`、4 byte、big endianで `core_config` を更新する。packetの長さはcommandを含め5 byte。長さが違うpacketで設定を更新しない。

| bit | 用途 |
| --- | --- |
| 16 | CRT有効の要求 |
| 18から17 | 水平blurの要求 0 OFF 1 WEAK 2 STANDARD 3 STRONG |
| 20から19 | scanlineの要求 同上 |
| その他 | 既存値を保持 |

この5 bitは要求値の符号化であり、強度の演算係数は未決定。既存の低位bitは上書きしない。

BL616から `AA 00 01 12` を送ると、FPGAは `AA 00 05 12` にframe適用済み32 bit値を続けて返信する。値は返信開始時に固定する。OSD2は100 ms間隔で確認する。これは最新返信時点のsnapshotであり、任意の過去操作に対応するsequence番号ではない。

## 検証

firmwareの `tools/ui16/test_crt.sh` はhotkey、衝突時の予約、既存bitの保持、OSD排他、OSD1中央固定、session初期化を検証する。既存の `test_osd.sh` と `test_launch.sh` にも新しい経路を接続した。

NESの `tests/crt/test_config.sh` は異なるclockで設定を転送し、frame途中の変化がないこと、連続更新の収束、reset、65,536組のRGBのbypass一致を検証する。

NESの `tests/crt/test_integration.sh` は実際のUART回路でpacketを送り、適用値の返信、長さの検査、能力通知、呼出しの即時遮断を確認する。また、固定基準commitの `nes2hdmi.sv` と変更後のmoduleを同時に動かし、400万画素でRGBとOSD座標が一致することを確認する。HDMI符号化とvendor出力bufferだけを試験用に置き換え、拡大とRGB生成とOSDのコードは実物を使う。

Console138K向けのFPGAは `gw_sh build.tcl console138k`、firmwareは `UI16_SYSTEM_MENU=ON`、`UI16_SD_FONT=ON`、`-Os` の既存構成でbuildする。SDCの追加例外は、保持期間を保証するmailboxのbus受信registerと同期器の第1段に限定する。

初版作成時には実機への書き込み、ROMでの起動確認、HDMI表示機器での確認は未実施だった。2026年11月3日にConsole138K／NESで実機試験を行い、OSDの一瞬の消失を修正した後、依頼した全項目の正常動作が利用者から報告された。対象の版と確認範囲は `HARDWARE_STAGE1_20261103.md` を参照する。生成物は第1段階の検証用であり、画質機能の完成版ではない。初版のbuild結果と試験記録は `verification/crt-stage1/` を参照する。

## 次の段階

作業順序とcommitの区切りは `IMPLEMENTATION_STEPS.md` に従う。本書の第1段階は、その表の1〜3に相当する。

実機で確認済みのこの版を基準に、水平blurを一つ追加し、OFF時の一致と画素の端処理を再検証する。次にscanline、推奨値、ゲーム別保存へ進む。
