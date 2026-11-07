# OSD2 起動時情報の追加実機確認

SNESはUSB P1、スーパーマリオコレクションを各段階1回、合計3回起動する。
各段階で日本語一覧・titles.csv順序と映像・音声・通常操作を確認する。
SELECT＋左でOSD2を開き全buttonを離す。STARTは単独で押し、切替後に全buttonを離す。
各回の操作依頼は以下の表示順で行う。

## 通常表示

1. CRT X/Y:BACK：従来の小型枠。
2. CRT：1・2回目はON、3回目はOFF。
3. BLUR：1回目STD、2回目WEAK、3回目OFF。
4. SCAN：1回目WEAK、2回目STRONG、3回目OFF。
5. SAVE：1回目SAVE OK、2・3回目SAVE。ここでは実行しない。
6. RESET：表示だけ確認し実行しない。
7. POS：選んだ位置が正常。
8. START:INFO：STARTで補助表示を開く。

## 補助表示（通常5項目の下）

1. SAVE：1回目SAVED、2・3回目RECOMMENDED。
2. LOADED FROM：1回目SYSTEM、2回目GLOBAL、3回目BUILT-IN。
3. SAVE READ：1回目RECOVERED、2回目BAD SAVE、3回目NEW SCHEMA。
4. APPLY：FRAME ACKへ収束。
5. ROM ID：232bb5b8。
6. DEFAULTS：1・2回目OK、3回目BAD FILE。
7. RESET = RECOMMENDED：説明を確認。
8. POS：位置を維持。
9. START:HIDE：収納して小型枠へ戻れる。

1・2回目はSAVE/RESETせず、CRT変更previewとFRAME ACK、X/Y取消し、開き直した初期値の復元を同じ起動中に確認する。
3回目はCRTをONへ変え、SAVEを1回だけ実行する。SAVE FAILED、補助SAVE: FAILED、LOADED FROM: BUILT-IN、SAVE READ: NEW SCHEMAが維持されることを確認する。
その後X/Yで取り消し、開き直して全OFFとSAVE表示の復元を確認する。RESETの保存や再試行は不要。

各回後は電源を切りmicroSDだけPCへ移す。新しい全file退避と一時fileの完全一致を確認してから次段階へ進む。
3回目後は元のa7 Reset・b6 USERを全byteと属性で復旧し、一時defaultsを除去する。追加のSNES起動は不要。

## 復旧後のNES回帰

ドクターマリオを1回だけ起動し、日本語一覧・順序・映像・音声・通常操作を確認する。
通常①見出し②CRT③BLUR④SCAN⑤SAVE⑥RESET⑦POS⑧START:INFOの順に確認。
補助①SAVE状態②LOADED FROM③SAVE READ④APPLY⑤ROM ID⑥DEFAULTS⑦RESETの説明⑧POS⑨START:HIDEの順に確認。
既存値・preview・FRAME ACK・START保持中の追加入力遮断・小型枠への復帰・X/Y取消しを確認する。
NESのSAVE/RESETは実行しない。最後に電源を切りSDをPCへ移し、元の全65file・属性不変を読取り照合する。
