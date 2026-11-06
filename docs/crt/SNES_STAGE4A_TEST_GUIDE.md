# SNES 読取り専用設定 S4a 実機確認

2026年11月6日。Console138K。SNES起動は1回。同じ起動中に確認をまとめる。firmwareと、PCで作った一時的なUSER recordだけを導入する。FPGA image・日本語一覧・titles.csv・NES設定は維持する。

通常起動し、日本語一覧とtitles.csv順序を確認する。USB P1でスーパーマリオコレクションを1回起動し、映像・音声・通常操作を確認する。OSD2はP1のSELECT＋左で開き、全buttonを離す。

期待する初期値は次のとおり。

```text
CRT ENABLE   ON
H BLUR       STANDARD
SCANLINE     WEAK
ROM ID       232bb5b8
```

## OSD2（表示の上から順）

| 順 | 項目 | 確認内容 |
| --- | --- | --- |
| 1 | SNES CRT READ ONLY | 読取り専用段階の見出し。 |
| 2 | SAVE: READ ONLY | 保存成功を表示していないこと。 |
| 3 | INITIAL: USER | PCで用意したrecordを採用。 |
| 4 | CRT ENABLE | 初期ON。OFF/ONの変更で位置が動かない。 |
| 5 | H BLUR | 初期STANDARD。変更のpreviewが動く。 |
| 6 | SCANLINE | 初期WEAK。変更のpreviewが動く。 |
| 7 | STORE: USER | system=2のrecordを正常に読んだ状態。 |
| 8 | APPLY | 変更後、FRAME ACKへ収束。 |
| 9 | ROM ID: 232bb5b8 | PCのraw全file CRC32と一致。 |
| 10 | SAVE: NOT AVAILABLE | 選択できない。 |
| 11 | RESET: NOT AVAILABLE | 選択できない。 |
| 12 | DEFAULTS | fileがない今回の基準ではMISSING。 |
| 13 | POS | 見やすい位置でOSDの文字・枠へ効果がかからない。 |

初期値から変更した状態でX/Yを押して保持し、全解放後に操作へ戻ることを確認する。OSD2を開き直すと全OFFではなくON/STANDARD/WEAKへ戻ることを確認する。ゲームの再起動・一覧復帰・別SNES起動は不要。

共有firmwareを変更したため、SNES確認後はNESのドクターマリオを1回起動して既存値・preview・FRAME ACK・取消しを回帰確認する。SAVE/RESETは実行しない。NESの後にSNESを再起動する必要はない。

実機後にSDをPCへ戻すとき、導入直後の全file・属性との一致を確認する。一時USER recordはPCが作成した試験用で、S4a firmwareは書き込まない。結果を記録するまで手動で編集・削除しない。
