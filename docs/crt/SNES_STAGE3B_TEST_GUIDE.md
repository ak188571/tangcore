# SNES 走査線 S3b 実機確認

2026年11月6日。Console138K。共有firmwareはS3a版を維持し、SDのSNES imageだけを更新する。SNES起動は1回で済ませ、同じゲームを起動したまま全項目を確認する。

通常起動し、日本語一覧・titles.csv順序を確認して、USB P1でスーパーマリオコレクションを1回起動する。映像・音声・通常操作を確認する。文字・縦線や広い明るい面が見える場面でP1のSELECT＋左を押し、OSD2を開いて全buttonを離す。

初期値とX/Yによる取消し後の値は次のとおり。

```text
CRT ENABLE   OFF
H BLUR       OFF
SCANLINE     OFF
```

## OSD2（表示の上から順）

| 順 | 項目 | 確認内容 |
| --- | --- | --- |
| 1 | SNES CRT PREVIEW | 見出しを確認する。 |
| 2 | SAVE: UNAVAILABLE | 保存未対応を維持する。 |
| 3 | INITIAL: DEFAULT | 全OFF開始を確認する。 |
| 4 | CRT ENABLE | ONにする。後の効果比較中にOFFへ戻しても、横位置・サイズが動かず元の映像へ戻ることを確認する。 |
| 5 | H BLUR | 最初はOFF。その後STRONGにし、走査線との併用で左右端に別行の色・余分な帯・位置ずれが出ないことを確認する。 |
| 6 | SCANLINE | OFF→WEAK→STANDARD→STRONGで明暗が強まること、横の走査線が上下に流れたり部分的に崩れたりしないことを確認する。STRONGでも黒が浮かず、明るい面を比較できることを確認する。ぼかし併用後に両方OFFへ戻す。 |
| 7 | STORE: UNAVAILABLE | 表示を確認する。 |
| 8 | APPLY | 各変更・連続変更・A/B保持後にFRAME ACKへ収束する。 |
| 9 | ROM ID: UNAVAILABLE | 表示を確認する。 |
| 10 | SAVE: NOT AVAILABLE | 選択できない。 |
| 11 | RESET: NOT AVAILABLE | 選択できない。 |
| 12 | DEFAULTS: UNAVAILABLE | 表示を確認する。 |
| 13 | POS | 見やすい位置で、ぼかし・走査線の併用中もOSDの文字と枠へ効果がかからないことを確認する。 |

X/Yを保持して閉じ、全解放後に操作が戻ることを確認する。再びOSD2を開き全OFFへ戻っていることを確認する。ゲームの再起動・一覧復帰・別ゲーム起動は不要。そのまま待機してよい。

正常な項目番号と、異常があれば強度・直前の操作を伝える。結果はこのゲーム・接続先の範囲に限定する。239行・high-resolution・interlaceの完全対応を検証する試験ではない。
