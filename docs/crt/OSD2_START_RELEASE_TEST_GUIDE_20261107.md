# OSD2 START全解放待ち 修正版確認

2026年11月7日。小型表示・英語表記・保存engineは維持し、START操作後は全buttonが解放されるまで追加入力を遮断する。今回のSD差分は利用者の意図したSAVEと確認済みで、softwareによる意図しない保存とは扱わない。現在の有効な保存値を新しく退避し、firmwareだけを更新する。

```text
FW source: a1b6755
.a RESET generation 7 / .b USER generation 6
START -> all buttons up -> next operation
```

## SNES：1回の起動中に確認

USB P1でスーパーマリオコレクションを1回起動する。日本語一覧・titles.csv順序、映像・音声・通常操作を確認し、SELECT＋左でOSD2を開いて全buttonを離す。

通常表示は上からCRT X/Y:BACK、CRT、BLUR、SCAN、SAVE、RESET、POS、START:INFO。初期は全OFF・SAVE OKである。枠と略記は小型版のまま。今回は変更した値を保存せず、START保持中のSAVE遮断だけを試す。

### A：START保持中に追加したA/Bを遮断

CRTをONにしてSAVE *を確認し、SAVE行へcursorを移す。まだA/Bを押さず、STARTを押して保持する。補助表示が1回だけ開いたら、STARTを保持したままAまたはBを1回押す。保存されず、SAVE *と補助表示のUNSAVEDが保たれることを確認する。

補助表示は通常5項目の下から、SAVE状態、INITIAL、STORE、APPLY、ROM ID、DEFAULTS、RESETの説明、POS、START:HIDEの順。期待する値は次のとおり。

| 順 | 項目 | 期待値 |
| --- | --- | --- |
| 1 | SAVE状態 | UNSAVEDを維持 |
| 2 | INITIAL | DEFAULT |
| 3 | STORE | RESET |
| 4 | APPLY | FRAME ACKへ収束 |
| 5 | ROM ID | 232bb5b8 |
| 6 | DEFAULTS | MISSING |
| 7 | RESETの説明 | RECOMMENDED |
| 8 | POS | 選択した位置 |
| 9 | START:HIDE | 案内表示 |

全buttonを解放してからSTARTで収納し、再び全解放する。小型の枠とSAVE *へ戻ることを確認し、X/Yで閉じる。全解放後に開き直すと全OFF・SAVE OKへ戻ることを確認する。

### B：START保持中の方向を遮断し、解放後は操作できる

CRT行を選び、STARTを押して保持する。補助表示が開いたら、STARTを保持したまま右を1回押す。CRTがOFFから変わらないことを確認する。

全解放後にSTARTで収納し、再び全解放する。その後、右を1回押すとCRTがONへ変わることを確認し、X/Yで取り消す。今回、START解放後のSAVEや新しい値の保存は実行しない。背景の映像・音声、文字と枠、閉じた後の通常操作も確認する。SNESの追加起動は不要。

## NES回帰とSD照合

OSD1から一覧へ戻り、ドクターマリオを1回起動する。既存値、小型表示、STARTの保持・収納・縮小復帰、保持中の追加方向入力の遮断、全解放後の通常操作、preview・X/Y取消しを確認する。NESのSAVE/RESETは実行しない。

その後電源を切り、SDだけPCへ移す。新しい導入直前退避との全65file・属性・実recordの不変を読取り照合する。SDやfirmwareの追加書込みは行わない。観測した利用者の保存値を古いgenerationへ戻す操作もしない。
