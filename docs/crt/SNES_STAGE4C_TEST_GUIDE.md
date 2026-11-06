# SNES Reset S4c 実機確認

2026年11月6日。Console138K。SNES起動は保存・追従確認の2回。FPGAはS3bを維持し、導入前にSD・全flashを新しく退避する。

## 1回目の起動

日本語一覧・titles.csv順序を確認し、USB P1でスーパーマリオコレクションを起動する。映像・音声・操作を確認し、SELECT＋左でOSD2を開いて全buttonを離す。

一時metadataは日本語・一覧順を保ち、対象SNESの推奨値だけを追加する。既存USERが優先される。

```text
起動時USER    ON / WEAK / STRONG
CSV推奨値     ON / STANDARD / WEAK
SNES defaults ON / STRONG / STANDARD
ROM ID        232bb5b8
```

### OSD2（表示の上から順）

| 順 | 項目 | 確認内容 |
| --- | --- | --- |
| 1 | SNES CRT SETTINGS | 見出しを確認する。 |
| 2 | SAVE | SAVED→ResetでUNSAVED→保存でSAVED。 |
| 3 | INITIAL: USER | 起動時のsourceを維持する。 |
| 4 | CRT ENABLE | 初期ON。Reset preview後もON。 |
| 5 | H BLUR | WEAK→ResetでSTANDARD。 |
| 6 | SCANLINE | STRONG→ResetでWEAK。 |
| 7 | STORE: USER | 起動時のsnapshotを維持する。 |
| 8 | APPLY | 変更・取消し後にFRAME ACK。 |
| 9 | ROM ID: 232bb5b8 | 同じROMであることを確認する。 |
| 10 | SAVE (X/Y: CANCEL) | Reset後に選ぶ。保存後も開いたまま。 |
| 11 | RESET TO RECOMMENDED | CSV推奨値のpreview。SDへは未保存。 |
| 12 | DEFAULTS: OK | 一時fileの読取り成功を確認する。 |
| 13 | POS | 見やすい位置で文字・枠が正常。 |

最初にResetを選び、CSV推奨値とUNSAVEDを確認する。保存せずX/Yを保持して閉じ、全解放後の通常操作と、開き直した時の起動時USER値を確認する。

再びResetし、CSV推奨値を確認して上のSAVE行から保存する。SAVEDで開いたまま、同じReset modeでもう一度SAVEする。最後に設定を変更しX/Yで取り消し、開き直すと保存したCSV推奨値へ戻ることを確認する。INITIAL/STOREは起動時のUSER表示を保つ。

NES回帰は一覧へ戻り、ドクターマリオを1回起動する。OSD2は上から13項目、既存値・preview・FRAME ACK・X/Y取消しを確認する。SAVE/RESETは実行しない。DEFAULTSは一時fileによりOKとなるが、NES推奨値は追加しない。SNESへ戻る必要はない。

## PC照合とmetadata復旧

電源を切りSDだけPCへ移す。全fileを新しく退避し、世代・kind・CRCと他file/属性を照合する。BOOT接続・firmware更新は不要。

```text
.a  generation 3  USER   値27（元の保存値を保持）
.b  generation 4  RESET  値0 （推奨値を固定しない）
```

合格後、titles.csv全byteを復元し、今回作ったdefaultsと一致する一時fileだけを除去する。USER/Reset recordは残す。異常時は観測した退避を保ち、復旧前に照合する。

## 2回目の起動

同じfirmwareの本体へSDを戻し、同じSNESを1回起動する。OSD2は上からSNES CRT SETTINGS、SAVE SAVED、INITIAL DEFAULT、CRT ENABLE OFF、H BLUR OFF、SCANLINE OFF、STORE RESET、APPLY FRAME ACK、ROM ID 232bb5b8を確認する。

最後はSAVE行、RESET TO RECOMMENDED、DEFAULTS MISSING、POSの順に確認する。

設定変更・保存・追加起動は不要。古いCSV数値を固定せず全OFFへ追従したかを報告する。FAILEDや異常時は直前の操作を伝える。物理故障は意図的に起こさない。
