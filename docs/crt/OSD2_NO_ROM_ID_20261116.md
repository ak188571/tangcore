# SNES OSD2の `SAVE READ: NO ROM ID` 確認

2026年11月16日（日本時間）。通常版firmware `95871ef8e9ef547767b145cee4e85577e8bb4972` の起動処理と、実機に一時導入した診断版をPCで確認した。通常版のFlashをBOOT接続で2回読み取って退避し、診断版をアプリ領域へ一時適用した。全Flashの読戻しで診断版と変更範囲外を確認した。実機確認と通常版への復元を完了した。

| PCの条件 | 結果 |
| --- | --- |
| 通常のSD読込み | ROM ID取得とROM loadが成功 |
| ID取得時の終了結果だけ `FR_INT_ERR`、ROM loadは正常 | ROM loadが成功し、`SAVE READ: NO ROM ID` と `ROM ID: UNAVAILABLE` を表示 |
| ID取得中にSD controllerのタイムアウトを検知 | SD保護が動作し、起動処理を中止。ROMの再openやゲーム内OSD2には進まない |
| ID取得の失敗に続き、ROM loadのopenも失敗 | 起動を中止し、OSD2には進まない |
| 一時診断版 | 最初のSD上のSNES ROMで、実際の `f_close` 成功後にID用の戻り値だけを `FR_INT_ERR` に変更。ROM loadが成功し、同じOSD2表示を確認。2回目のID取得には影響しない |

PC試験は製品の起動処理、SNES ROM loader、SD保護処理、OSD2を使用した。FatFsと転送先を模擬し、合成データを読み込む。診断版のnegotiated転送では、転送へ渡すheaderとpayloadを照合した。実機の映像・音声・入力と `FRAME ACK` は実機報告に基づく。

IDを得られなかった場合、小型表示は `SAVE N/A` と `RESET N/A`。補助表示は `SAVE: READ ONLY`、`LOADED FROM: BUILT-IN`、`SAVE READ: NO ROM ID`、`ROM ID: UNAVAILABLE`、`DEFAULTS: MISSING`。個別保存recordへのopenはなく、SAVE・RESETは操作対象に入らない。CRTの一時変更は可能で、X/Yで閉じると元の設定に戻った。

通常構成でROMや保存recordの内容を変更して再現する手順は見つからなかった。診断版は既存の通常版を元に、build optionとID取得の終了処理だけを変更した。ROM転送、SD保護、FPGA imageは同じ経路を使う。

## PCでの再実行と診断版の差分

親repositoryが参照する `firmware-bl616` を用意し、WindowsのMSYS2 UCRT64 GCCとPython 3で実行する。

```powershell
python tools/test_osd2_no_rom_id.py --firmware firmware-bl616 --output ../no-id-normal
```

診断版を確認するときは、firmwareの基点 `95871ef8e9ef547767b145cee4e85577e8bb4972` の別作業treeに `tools/osd2_no_rom_id_diagnostic.patch` を `git apply` する。実機で使った差分はこのpatchに収録した。PCでの試験には `--firmware` でその作業treeを指定し、`--diagnostic` を付ける。実機用のfirmware buildは通常版のConsole138K／BL616／UI16の設定に `-DTC_DIAG_ROM_ID_CLOSE_FAILURE=ON` を追加する。optionの既定値はOFF。

## 実機結果と通常版への復元

USB P1でスーパーマリオコレクションを1回起動した。ユーザーから「想定通り。boot接続済み」と報告を受けた。映像・音声・通常操作は正常で、OSD2には `SAVE N/A` と `RESET N/A` があり、選択位置はそれらを飛ばした。補助表示は `SAVE: READ ONLY`、`LOADED FROM: BUILT-IN`、`SAVE READ: NO ROM ID`、`APPLY: FRAME ACK`、`ROM ID: UNAVAILABLE`、`DEFAULTS: MISSING` だった。CRTをONにして取り消すと、通常操作が戻り、OSD2を開き直すとCRT OFFと `SAVE READ: NO ROM ID` が表示された。

試験後のBOOT接続で診断版のFlash全体を2回照合してから、試験前の退避からアプリ領域を復元した。別の読取りで全4 MiBが試験前と全byte一致した。診断版を適用するときも通常版を復元するときも、書込みと読戻しは同じ接続で行った。microSDは装着したまま、SAVE・RESETは各0回だった。

実機の起動・画面・操作はユーザー報告、Flashの退避・適用・復元は読戻しに基づく。実機で再現したのはROM ID取得時の終了結果だけの失敗であり、SDの物理障害は別の試験範囲となる。microSDは装着したままなので、試験後のSD内容照合は未実施。結果は `verification/osd2-no-rom-id-20261116/` に記録した。
