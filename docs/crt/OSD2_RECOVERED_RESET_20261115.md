# SNES OSD2 有効なRESET recordを使うRECOVERED

2026年11月15日（日本時間）。一方のCRT保存recordがCRC不一致の場合に、有効なRESET recordを採用し、組込み推奨値と保存済み状態を復元することを確認する。現状はPC試験と元データの退避が完了し、実機結果と試験後の復元を待っている。

## 試験条件

- 親repositoryの起点は `fbeabe1e8a35b6e8f776eb2be0b2f3077c3ec1ab`。firmwareは `95871ef8e9ef547767b145cee4e85577e8bb4972`、SNESTangは `9a1360fd764b7ca85e3b0013ac684a36ec3a04a9`。先行検証でFlashを照合した構成を使う。
- 対象はスーパーマリオコレクション。ROM IDはCRC32 `232bb5b8`、サイズは2,097,152 byte。対象タイトルにCRT指定がなく、`crt/defaults.tsv` もないため組込み推奨値はOFF/OFF/OFF。
- 試験前のmicroSD全215ユーザーファイルを内容・属性とともに退避した。前回復元時の状態と一致した。Windows管理領域は集計の対象外。
- aはCRC有効な既存のRESET世代7、bは試験用のCRC不一致USER世代8（ON/WEAK/STD）。試験用bだけを導入する。元のbはUSER世代6（ON/OFF/OFF）。

## PC試験

`tools/test_osd2_recovered_reset.py` で、現行firmwareの読込み処理とOSDをcompileした。aと同じbyteのRESET recordを生成し、CRC不一致のbと組み合わせた。a世代7を `RECOVERED` として採用し、USER値のoverrideが設定されないことを確認した。

起動時はOFF/OFF/OFFで `SAVE OK`、補助表示は `SAVE: SAVED`、`LOADED FROM: BUILT-IN`、`SAVE READ: RECOVERED`。CRT ONの未保存previewは `SAVE *`／`SAVE: UNSAVED` となり、取消し後にOFF/OFF/OFFと保存済み表示へ戻った。PCでは `FRAME ACK` を模擬し、mkdir・書込み用open・write・syncの試行が0回であることを確認した。

```powershell
python tools/test_osd2_recovered_reset.py --firmware firmware-bl616 --output ../osd2-recovered-reset-pc
```

## 実機手順

SDをPCから本体へ移して通常起動し、USB P1で対象ゲームを1回起動する。日本語一覧と並び順、映像・音声、通常操作を確認する。各操作後は全ボタンを離す。SAVEとRESETは実行しない。

SELECT＋左で小型OSD2を開き、`CRT X/Y:BACK`、`CRT OFF`、`BLUR OFF`、`SCAN OFF`、`SAVE OK`、`RESET`、`POS`、`START:INFO` の順に確認する。START単独で補助表示を開き、追加行を `SAVE: SAVED`、`LOADED FROM: BUILT-IN`、`SAVE READ: RECOVERED`、`APPLY: FRAME ACK`、`ROM ID: 232bb5b8`、`DEFAULTS: MISSING`、`RESET = RECOMMENDED`、`POS`、`START:HIDE` の順に確認する。

STARTで小型表示に戻してCRTだけONにし、`SAVE *` と補助表示の `UNSAVED`／`BUILT-IN`／`RECOVERED`／`FRAME ACK` を確認する。XまたはYで取り消して開き直し、OFF/OFF/OFFと `SAVE OK`、補助表示 `SAVED`／`BUILT-IN`／`RECOVERED`／`FRAME ACK` を確認する。

電源を切ってSDだけをPCへ戻す。全ファイルが導入直後の内容・属性と一致することを照合し、実際に使ったrecordをPCの試験に通す。事前に退避した元のbを復元して、全ユーザーファイルを試験前の状態と再照合する。SDの移動はPC→本体→PCの1往復で、USBケーブルの挿し直しは0回を予定する。
