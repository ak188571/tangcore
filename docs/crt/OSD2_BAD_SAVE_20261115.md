# SNES OSD2 両方の保存recordがCRC不一致のときのBAD SAVE

2026年11月15日（日本時間）。2件のCRT保存recordがともにCRC不一致の状態でSNESを起動し、OSD2で `SAVE READ: BAD SAVE` が表示されることを確認した。試験後のmicroSD照合と元データの復元も完了した。

## 試験条件

- 親repositoryの起点は `4d037e84b9daebd42349fc81c1e605ec068e165e`。firmwareは `95871ef8e9ef547767b145cee4e85577e8bb4972`、SNESTangは `9a1360fd764b7ca85e3b0013ac684a36ec3a04a9`。先行試験でFlashを照合した構成を使用する。
- 対象はスーパーマリオコレクション。ROM IDはCRC32 `232bb5b8`、サイズは2,097,152 byte。タイトルのCRT指定も `crt/defaults.tsv` もなく、組込み推奨値はOFF/OFF/OFF。
- microSDの全215ユーザーファイルを内容・属性とともに退避し、前回復元時の状態と一致することを確認した。Windows管理領域は集計の対象外。
- aはRESET世代7、bはUSER世代6（ON/OFF/OFF）。それぞれ元のrecordのCRCフィールドの最下位bitだけを反転した試験用recordを使う。試験前の元recordは両方ともCRC有効。

## PC試験

`tools/test_osd2_bad_save.py` で試験用recordを生成し、現行firmwareの読込み処理とOSDをcompileした。2件ともCRC不一致の場合に読込み状態が `Bad` となり、採用slotとUSER overrideがないことを確認した。

OSD2は組込み推奨値の全OFFを適用し、小型表示は `SAVE`、補助表示は `SAVE: RECOMMENDED`、`LOADED FROM: BUILT-IN`、`SAVE READ: BAD SAVE`。CRT ONの未保存変更では `SAVE *`／`SAVE: UNSAVED`、取消し後は全OFFと `SAVE`／`SAVE: RECOMMENDED` に戻った。`FRAME ACK` はPCで模擬した。mkdir・書込み用open・write・syncの試行は各0回だった。

```powershell
python tools/test_osd2_bad_save.py --firmware firmware-bl616 --output ../osd2-bad-save-pc
```

## 実機手順

microSDをPCから本体へ移し、通常起動する。USB P1で対象ゲームを1回起動し、日本語一覧と並び順、映像・音声、通常操作を確認する。各操作後は全ボタンを離し、SAVEとRESETは実行しない。

SELECT＋左で小型OSD2を開き、`CRT X/Y:BACK`、`CRT OFF`、`BLUR OFF`、`SCAN OFF`、`SAVE`、`RESET`、`POS`、`START:INFO` の順に確認する。START単独で補助表示を開き、`SAVE: RECOMMENDED`、`LOADED FROM: BUILT-IN`、`SAVE READ: BAD SAVE`、`APPLY: FRAME ACK`、`ROM ID: 232bb5b8`、`DEFAULTS: MISSING`、`RESET = RECOMMENDED`、`POS`、`START:HIDE` の順に確認する。

STARTで小型表示に戻してCRTだけONにする。`SAVE *` と補助表示の `UNSAVED`／`BUILT-IN`／`BAD SAVE`／`FRAME ACK` を確認し、XまたはYで取り消して開き直す。全OFFと `SAVE`、補助表示の `RECOMMENDED`／`BUILT-IN`／`BAD SAVE`／`FRAME ACK` に戻ることを確認する。

電源を切りmicroSDだけをPCへ戻す。導入直後と比較し全ファイルの内容・属性を照合する。試験後に採取した2件を製品の読込み処理に通す。退避から元のaとbを復元し、試験前の全ファイルと照合する。

## 実機結果とSD復元

ユーザーから「想定通り。microsd接続済み」と報告を受けた。SNES起動1回で全OFFに設定され、小型表示の `SAVE` と補助表示の `SAVE: RECOMMENDED`、`LOADED FROM: BUILT-IN`、`SAVE READ: BAD SAVE`、`APPLY: FRAME ACK` を確認した。CRT ONの未保存変更を取り消すと、全OFFと推奨値の表示に戻った。日本語一覧・並び順、映像・音声・通常操作も想定どおりだった。

試験終了後の全215ファイルの内容・属性が、試験用record導入直後と一致した。両方のCRCが不一致のままであることを確認し、採取した2件を製品の読込み処理に通して、採用slotなしの `BAD SAVE` を再確認した。

元のa（RESET世代7）とb（USER世代6）の2件を退避から復元し、全215ファイルの内容・属性が試験前と一致した。SAVEとRESETは各0回、USBケーブルの挿し直しは0回、microSDの移動はPCと本体の1往復だった。microSDは復元済みでPCに接続している。詳細は `verification/osd2-bad-save-20261115/result.json` に記録した。
