# SNES 明示SAVE S4b 実機確認

2026年11月6日。Console138K。保存と電源再投入後の復元のため、SNES起動は2回にまとめる。FPGA imageはS3bのまま。CSV/defaults・NES設定は変更しない。

## 1回目の起動

通常起動し、日本語一覧・titles.csv順序を確認して、USB P1でスーパーマリオコレクションを1回起動する。映像・音声・操作を確認し、P1のSELECT＋左でOSD2を開いて全buttonを離す。

初期値はS4aのPC recordから読み込む。初期SAVE状態のSAVEDは、既存USER recordを採用した意味で、S4bで新しく書き込んだ証拠ではない。

```text
CRT ENABLE   ON
H BLUR       STANDARD
SCANLINE     WEAK
ROM ID       232bb5b8
```

### OSD2（表示の上から順）

| 順 | 項目 | 確認内容 |
| --- | --- | --- |
| 1 | SNES CRT SAVE - S4B | 見出しを確認する。 |
| 2 | SAVE | 初期SAVED。変更後UNSAVED、明示SAVE後SAVEDへ変わる。 |
| 3 | INITIAL: USER | 起動時のsourceを維持する。 |
| 4 | CRT ENABLE | 初期ON。今回の保存値でもONを使う。 |
| 5 | H BLUR | 初期STANDARD。1回目SAVEはSTRONG、次のSAVEはWEAK。 |
| 6 | SCANLINE | 初期WEAK。1回目SAVEはSTANDARD、次のSAVEはSTRONG。 |
| 7 | STORE: USER | 起動時の情報を維持する。 |
| 8 | APPLY | 各変更後FRAME ACKへ収束する。 |
| 9 | ROM ID: 232bb5b8 | 同じROMのkeyであること。 |
| 10 | SAVE (X/Y: CANCEL) | 下の保存値を順にSAVEする。各回SAVEDのまま開いていること。同値の再SAVEは再書込みしない。 |
| 11 | RESET: NOT AVAILABLE | 選択できない。 |
| 12 | DEFAULTS: MISSING | 表示を確認する。 |
| 13 | POS | 見やすい位置で文字・枠に効果がかからない。 |

SAVEする値の順序：

```text
1. ON / STRONG / STANDARD
2. ON / WEAK / STRONG
3. 同じ値でもう一度SAVE
```

最後の保存後に値を変えてUNSAVEDにし、X/Yを保持して閉じる。全解放後に操作へ戻り、OSD2を開き直すとON/WEAK/STRONGへ戻ることを確認する。OSD1のRestart Gameや追加のSNES起動は不要。

共有firmwareのNES回帰を案内されたら、Return to Game Listからドクターマリオを1回起動する。NESではSAVE/RESETを実行しない。その後SNESへは戻らず、電源を切ってSDをPCへ移し、両slotと他file不変の読取り確認を受ける。

## PC照合後の2回目の起動

同じS4b firmwareのままSDを戻して通常起動する。スーパーマリオコレクションを1回起動し、OSD2を表示順に確認する。INITIALはUSER、CRT ENABLEはON、H BLURはWEAK、SCANLINEはSTRONG、STOREはUSER、APPLYはFRAME ACK、ROM IDは232bb5b8。SAVE/RESETは実行しない。全強度の試験や別SNES起動は不要。

期待する両slotは次のとおり。これはPC側で確認する。

```text
.a  generation 3  USER  ON/WEAK/STRONG
.b  generation 2  USER  ON/STRONG/STANDARD
```

SAVEがFAILEDになった場合は、表示と直前の操作を伝える。今回の実機手順では故障を意図的に起こさない。SD故障時のguardは電源再投入までSD I/Oを止め、失敗書込みの実体はPCで読んで判断する。
