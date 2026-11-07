# 小型OSD2 実機確認

2026年11月7日。Console138K。共有firmwareだけを更新する。OSD1/OSD2は全機種で英語表示を維持する。SD全体・全flashを新しく退避し、確認済みS4cへ戻せる状態で導入する。

## SNESは1回の起動にまとめる

日本語一覧・titles.csv順序を確認し、USB P1でスーパーマリオコレクションを1回起動する。映像・音声・通常操作を確認し、SELECT＋左でOSD2を開いて全buttonを離す。初期値はS4cの保存済みReset modeで全OFF。

```text
SAVE OK / SAVE * / SAVE FAILED
START:INFO <-> START:HIDE
STD = STANDARD
```

### 通常表示（上から順）

| 順 | 項目 | 確認内容 |
| --- | --- | --- |
| 1 | CRT X/Y:BACK | 枠が小さく、ゲームを見やすい。 |
| 2 | CRT | 初期OFF。ON/OFFのpreview。 |
| 3 | BLUR | OFF/WEAK/STD/STRONG。STDは従来のSTANDARD。 |
| 4 | SCAN | 同じ4段階。 |
| 5 | SAVE | 初期OK、変更後は*。変更した値は保存しない。 |
| 6 | RESET | 推奨値のpreviewへ戻る。OSDを閉じない。 |
| 7 | POS | C/TL/TR/BL/BRの5位置。文字・枠が欠けない。 |
| 8 | START:INFO | START単独で補助表示を開く。保持中に開閉を繰り返さない。 |

CRT ON・BLUR STD・SCAN WEAKなどへ変更し、SAVE *を確認する。SAVEを実行せず、同じ項目を選んだままSTARTで補助表示を開く。

### 補助表示（通常5項目の下から順）

| 順 | 項目 | 確認内容 |
| --- | --- | --- |
| 1 | SAVE状態 | UNSAVEDなど現在の状態。 |
| 2 | INITIAL | 起動時DEFAULT。 |
| 3 | STORE | 起動時RESET。 |
| 4 | APPLY | 変更後FRAME ACKへ収束する。 |
| 5 | ROM ID | 232bb5b8。 |
| 6 | DEFAULTS | MISSING。 |
| 7 | RESET = RECOMMENDED | 短縮名の意味を示す。 |
| 8 | POS | 選んだ位置を維持する。 |
| 9 | START:HIDE | STARTで収納し、枠も元の小ささへ戻る。 |

開閉で選択項目・値・位置が動かず、OSDが一度消えないことを確認する。背景の映像・音声は続く。X/Yを保持して閉じ、全解放後の通常操作と、開き直した時の小型表示・全OFFへの取消しを確認する。

次に値を変更してからRESETを選び、全OFFへ戻ることを確認する。最後のSAVEは全OFF・SAVE OKで未変更の状態だけで実行し、OKのまま開いていることを確認する。実recordへの再書込みがないことは後でSDを照合する。

## NES回帰と最終SD照合

OSD1のReturn to Game Listで日本語一覧へ戻り、ドクターマリオを1回起動する。通常表示は上から見出し、CRT、BLUR、SCAN、SAVE、RESET、POS、STARTの順に確認する。既存値・preview・STARTの補助表示/収納・FRAME ACK・X/Y取消しを確認する。NESのSAVE/RESETは実行しない。

その後SNESへ戻る必要はない。電源を切り、SDだけPCへ移して全65file・属性と既存recordの不変を読取り確認する。BOOT操作やfirmware再書込みは不要。今回の確認では新しいUSER値の保存・metadata追加・物理故障の注入を行わない。
