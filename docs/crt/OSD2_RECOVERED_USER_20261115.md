# SNES OSD2 USER値を採用するRECOVERED

2026年11月15日（日本時間）。片方の保存recordがCRC不正で、他方が有効なUSER recordの条件を、SNES起動1回で確認した。試験後のSD照合と元データの復元も完了した。結果は `verification/osd2-recovered-user-20261115/result.json` に記録する。

## 構成と接続

- 親の起点：`e873600b4ea4b24d2a73ec2b70ba34ed87822387`。
- firmware：`95871ef8e9ef547767b145cee4e85577e8bb4972`。製品ソースの変更なし。
- SNESTang：`9a1360fd764b7ca85e3b0013ac684a36ec3a04a9`。
- SNES image SHA-256：`b3df3e53444acdc083f45d11e194772e50ee91226dbcf9b23424e6732957737e`。
- 同じ作業中のCONFLICT試験前にFlash全体を読取り照合した通常版を継続使用。以降のfirmware書込みなし。今回は新たなFlash読取り・書込み、BOOT接続、USB再接続を要求しない。
- SDは開始時からPC接続済み。新規退避・準備をまとめ、本体で1回確認後にPCへ戻した接続のまま照合・復元する。復元後の返却はユーザーの都合に合わせる。

## 新規退避と試験条件

試験直前のSD全215ユーザーファイルを内容・属性込みで新しく退避し、直前のMISSING試験後の復元状態と全件一致した。Windows管理領域 `System Volume Information` と `$RECYCLE.BIN` は対象外。

対象はスーパーマリオコレクション、raw CRC32 `232bb5b8`、2,097,152 byte。`titles.csv` のCRT指定と `crt/defaults.tsv` はなく、推奨値は全OFF。元の `.a` はReset generation 7、`.b` はUSER generation 6、ON/OFF/OFF。

試験用はschema 1の32 byte×2件。`.a` はUSER generation 9、値31に相当するrecordのCRCだけを1 bit反転する。`.b` は有効なUSER generation 8、値19（ON／WEAK／STD）。不正側に大きい世代番号を置いても、有効な `.b` を選ぶ条件である。実機で試す配置は不正a・有効bの1通り。

## PC試験

`tools/test_osd2_recovered_user.py` が生成したそのままの2件を、現行firmwareの製品parserとOSD処理へ通した。

- RECOVERED、selected slot b、generation 8、USERのON／WEAK／STDを取得。
- BUILT-INの全OFFよりUSER値を優先。小型表示はSAVE OK。
- 補助表示はSAVE: SAVED、LOADED FROM: USER、SAVE READ: RECOVERED、DEFAULTS: MISSING。
- CRTをOFFへpreviewするとSAVE *／UNSAVED。起動時情報USER／RECOVEREDを保持。
- 取消し・再表示でON／WEAK／STDとSAVE OK／SAVEDへ戻る。
- mkdir、書込み用open、write、syncの呼出しは0件。SAVEやRESETの実行試験ではない。
- PC上のFRAME ACKは模擬入力。実応答は実機報告で確認する。

Windows、Python 3、`C:/msys64/ucrt64/bin/g++.exe` を使用。親が指定するfirmware submoduleを準備し、親repositoryのルートから実行する。

```powershell
python tools/test_osd2_recovered_user.py --firmware firmware-bl616 --output ../osd2-recovered-user-pc
```

## 実機手順（1起動、SAVE・RESETなし）

USB P1で対象ゲームを1回起動。日本語一覧と並び順、映像・音声・通常操作を確認し、各操作後は全ボタンを離す。

小型OSD2の表示順：見出し→CRT ON→BLUR WEAK→SCAN STD→SAVE OK→RESET（実行しない）→POS→START:INFO。

補助表示の追加行の順：SAVE: SAVED→LOADED FROM: USER→SAVE READ: RECOVERED→APPLY: FRAME ACK→ROM ID: 232bb5b8→DEFAULTS: MISSING→RESET = RECOMMENDED→POS→START:HIDE。

同じ起動中にCRTだけOFFへ変更し、SAVE *／UNSAVED、USER／RECOVEREDの維持、FRAME ACKを確認する。SAVEせずXまたはYで取消す。全解放後に開き直し、ON／WEAK／STD、SAVE OK／SAVED、USER／RECOVEREDとFRAME ACKへの復帰を確認する。

終了後は電源を切りSDだけPCへ戻す。

## 試験後の照合と復元

試験後の全ファイルを別に退避し、導入直後と全215ファイルのbyte・属性が一致することを確認する。この比較により、有効なUSER値の採用だけで不正slotが自動的に書き換えられていないことも確認する。試験後の2件を製品parser・OSD処理でPC再検証する。

未知の変更は退避して復元前に停止する。無変化なら今回退避した元の2件と属性を復元し、試験前の全215ファイルと再照合する。追加のSNES起動は不要。実際のROM、保存record、Flash原本、機器固有IDはローカルで管理する。

## 実機結果と復元完了

ユーザー報告は「想定通り、microsd接続済み」。SNES起動1回、SAVE・RESET各0回で、上記の全項目、USER／RECOVERED、ON／WEAK／STD、FRAME ACK、未保存previewと取消し後の復帰を確認した。表示・映像・音声・入力はユーザー報告に基づく。

試験後の全215ファイルを新たに退避し、導入直後と全byte・属性が一致した。不正slotを含む保存recordの自動書換えは観測されなかった。退避した現物2件で製品parserとOSD処理のPC再検証も合格。今回退避した元の.a（Reset generation 7）と.b（USER generation 6、ON/OFF/OFF）を属性込みで復元し、試験前の全215ファイルとの一致を確認した。

SDは復元済みでPC接続のまま。追加のUSB再接続は要求せず、SD移動をPC→本体→PCにまとめた。追加のSNES起動は不要。
