# SNES 水平ぼかし S3a 実機確認

2026年11月6日。Console138K。言語設定 ja-JP。S1で確認したスーパーマリオコレクション・USB P1を基準に、追加した水平ぼかしだけを切り分ける。走査線・保存・推奨値適用はまだ有効にしていない。

## 導入と通常起動

FPGA build/timingとPC試験に合格した版を使う。導入時はSDの全file内容・属性と全flashを新しく退避し、共有firmwareとSNES imageだけを更新する。今回の直前のS1版へ復旧できる状態を保つ。実機操作は担当者の案内に従う。

通常起動後、日本語一覧・titles.csv順序、SNESの映像・音声・通常操作を確認する。文字・縦線・明暗境界が見える場面でP1のSELECT＋左を押し、OSD2を開いて全buttonを離す。

## OSD2（表示の上から順）

| 順 | 表示・項目 | 確認すること |
| --- | --- | --- |
| 1 | SNES CRT PREVIEW | SNESのpreview段階であることを確認する。 |
| 2 | SAVE: UNAVAILABLE | 保存未対応の表示を維持する。 |
| 3 | INITIAL: DEFAULT | 起動時は全OFF。保存値やCSVはまだ採用しない。 |
| 4 | CRT ENABLE | OFF/ONを切り替える。横位置・画面サイズが動かないことを確認する。 |
| 5 | H BLUR | CRT ENABLEをONにし、OFF→WEAK→STANDARD→STRONGの順で比較する。水平のぼかし量が変わり、左右端に別行の色や余分な帯が入らないことを確認する。最後にOFFへ戻し、元の映像へ戻ることを確認する。 |
| 6 | SCANLINE: NOT YET | 選択できず、走査線効果も出ない。 |
| 7 | STORE: UNAVAILABLE | 保存recordはまだ読んでいない。 |
| 8 | APPLY | 各強度・ON/OFFの変更後、FRAME ACKへ収束する。連続変更後やA/B保持中にも確認する。 |
| 9 | ROM ID: UNAVAILABLE | ROM IDはまだ取得していない。 |
| 10 | SAVE: NOT AVAILABLE | 選択できない。 |
| 11 | RESET: NOT AVAILABLE | 選択できない。 |
| 12 | DEFAULTS: UNAVAILABLE | defaults.tsvはまだ読んでいない。 |
| 13 | POS | STRONGでもOSDの文字とpanel枠がぼけないことを確認する。位置変更の5か所自体はS1で確認済みなので、今回は見やすい位置で画質を比べればよい。 |

起動時とX/Yで破棄した後は、次の状態になる。

```text
CRT ENABLE   OFF
H BLUR       OFF
SCANLINE     NOT YET
```

保存機能が未対応なので、X/Yで閉じると全OFFへ戻る。OSDを閉じたまま調整値を保持する段階ではない。X/Y保持中に終了buttonがゲームへ漏れず、全解放後に通常操作へ戻ることと、再度開くと全OFFになることを確認する。

## OSD1とNES回帰

OSD1では表示順にRestart Game、Return to Game Listを確認する。再起動後もOSD2の水平ぼかしとFRAME ACKが使えること、日本語一覧へ戻れることを確認する。

共有firmwareの表示制御も変更したため、NESのドクターマリオを起動し、既存設定値・CRT preview・X/Y取消しとOSD1復帰が維持されることを確認する。SAVE/Resetは実行しない。最後にSNESへ戻り、SNESの初期表示へ戻ることを確認する。

## 結果の伝え方

OSD2の正常だった項目番号と、ぼかし各強度・左右端・位置不変・OSDの鮮明性を教える。異常があれば直前の操作を添える。今回の結果は確認したゲームとUSB P1の範囲へ限定し、全映像modeや他controller経路へ広げない。実機合格前に走査線の次段階へ進めない。
