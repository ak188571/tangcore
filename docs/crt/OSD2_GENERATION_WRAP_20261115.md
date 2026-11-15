# SNES OSD2 保存世代番号の折返し

2026年11月15日（日本時間）。SNES起動1回、設定変更とSAVEを2回行い、保存世代の `0xffffffff → 0 → 1` を確認した。試験後のSD照合と元データの復元も完了した。結果は `verification/osd2-generation-wrap-20261115/result.json` に記録する。

## 構成と接続

- 親の起点：`4a27ca26586eb46240caa90292a69763c2a18e80`。
- firmware：`95871ef8e9ef547767b145cee4e85577e8bb4972`。製品ソースの変更なし。
- SNESTang：`9a1360fd764b7ca85e3b0013ac684a36ec3a04a9`。
- SNES image SHA-256：`b3df3e53444acdc083f45d11e194772e50ee91226dbcf9b23424e6732957737e`。
- 同じ作業中のCONFLICT試験前にFlash全体を読取り照合した通常版を継続使用。それ以降のfirmware書込みなし。今回はFlash再読取り・書込みや追加のBOOT／USB接続を要求しない。
- 開始時のmicroSDはPC接続済み。退避・準備をまとめ、PC→本体→PCの移動で試験と復元を完了する計画。2回のSAVEを同じ起動中に行うことで、中間状態のSD読取りや追加起動を省く。

## 新規退避と試験条件

試験直前のSD全215ユーザーファイルを内容・属性込みで新しく退避し、直前のUSER／RECOVERED試験後の復元状態と全件一致した。Windows管理領域 `System Volume Information` と `$RECYCLE.BIN` は対象外。

対象はスーパーマリオコレクション、raw CRC32 `232bb5b8`、2,097,152 byte。`titles.csv` にCRT指定はなく、`crt/defaults.tsv` もない。元の `.a` はReset generation 7、`.b` はUSER generation 6、ON/OFF/OFF。

両slotともschema 1・USER・CRC有効の32 byte recordを用いる。

| 段階 | slot a | slot b | 採用対象 |
| --- | --- | --- | --- |
| 導入直後 | 世代 `0xffffffff`、ON/WEAK/STD | 世代 `0xfffffffe`、OFF/OFF/OFF | a |
| 1回目SAVE後 | 導入時のaを保持 | 世代 `0`、OFF/WEAK/STD | b |
| 2回目SAVE後 | 世代 `1`、ON/WEAK/STD | 1回目のbを保持 | a |

1回目はCRTをOFFへ変更して保存し、2回目はONへ変更して保存する。変更を伴うため、同値SAVEの省略処理には入らない。2回目の保存処理はSDから再読取りし、折返し後の0を最新として選択しなければ、期待するa世代1を作れない。

## PC試験

`tools/test_osd2_generation_wrap.py` は初期2件と各SAVE後の期待byteを独立に生成し、現行の製品parser・保存処理・OSD処理を直接compileして検証する。

- 導入するそのままの2件でa世代 `0xffffffff` をUSERとして選択。
- 1回目SAVEでb世代0のbyte・CRCが期待値と一致し、aは全byte不変。製品parserはb世代0を選択。
- 2回目SAVEが再読取りを行い、a世代1のbyte・CRCが期待値と一致。b世代0は全byte不変。
- write・sync・書込み用open各2回、順序はb→a。
- 各SAVEでSAVE OK／SAVED、OSD継続、起動時情報USER／USERを保持。
- 2回目の保存後、未保存のOFF previewを取消し、ON/WEAK/STDへ復帰。追加保存なし。
- PC上のFRAME ACKは模擬入力。実応答は実機報告で確認する。

Windows、Python 3、`C:/msys64/ucrt64/bin/g++.exe` を使用。親が指定するfirmware submoduleを準備し、親repositoryのルートから実行する。

```powershell
python tools/test_osd2_generation_wrap.py --firmware firmware-bl616 --output ../osd2-generation-wrap-pc
```

## 実機手順（1起動、SAVE 2回）

USB P1で対象ゲームを1回起動。日本語一覧・並び順、映像・音声・通常操作を確認し、各操作後は全ボタンを離す。RESETは実行しない。

小型OSD2の表示順：見出し→CRT ON→BLUR WEAK→SCAN STD→SAVE OK→RESET→POS→START:INFO。

補助表示の追加行の順：SAVE: SAVED→LOADED FROM: USER→SAVE READ: USER→APPLY: FRAME ACK→ROM ID: 232bb5b8→DEFAULTS: MISSING→RESET = RECOMMENDED→POS→START:HIDE。

1回目はCRTだけOFFへ変えてSAVE。SAVE OK、OSD継続、補助表示SAVED／USER／USER／FRAME ACKを確認する。BLURとSCANはWEAK／STDのまま。

2回目はCRTだけONへ戻してSAVE。同じ保存成功表示とFRAME ACKを確認する。続いてCRTをOFFへ変えるが保存せず、XまたはYで取消し、全解放後に開き直してON/WEAK/STDとSAVE OK／SAVEDへ戻ることを確認する。

世代番号自体はOSDには表示されない。終了後は電源を切りSDだけPCへ戻し、保存された世代を直接照合する。

## 試験後の照合と復元

全ファイルを新規退避し、最終a世代1・b世代0の全byte・属性が期待値と一致することと、他213ファイルの内容・属性が不変であることを確認する。実際の2件を製品parserへ通し、a世代1を選択すること、bも単独で有効な世代0として読めることを確認する。

実機ではSAVE間のSD読取りを行わない。中間状態の完全一致はPC試験で確認し、実機は2回のSAVE報告と最終的に残る世代0・1の2件で確認する。電源再投入後の読込みは今回の実機範囲外。

未知の変更は現状を退避して復元前に停止する。一致した場合は今回退避した元の2件と属性を復元し、試験前の全215ファイルと再照合する。追加のSNES起動は不要。ROM、保存record原本、Flash原本、機器固有IDはローカルで管理する。

## 実機結果と復元完了

ユーザー報告は「想定通り。microsd接続済み」。SNES起動1回、SAVE実行2回、RESET 0回で、上記の全項目を確認した。OSD表示・操作・SAVE成功、映像・音声・入力はユーザー報告に基づく。

試験後の全215ファイルを新たに退避した。実際の.aはUSER世代1（ON/WEAK/STD）、.bはUSER世代0（OFF/WEAK/STD）で、両CRC有効、全byte・属性が期待値と一致。他213ファイルは内容・属性が不変だった。現物2件を製品parserへ通してa世代1の採用と、b単独での世代0の読取りも確認した。世代0を保存した後、次の保存でそれを最新として読み直し世代1へ進める動作が、2回のSAVE報告とSDの最終状態で確認できた。

今回退避した元の.a（Reset世代7）と.b（USER世代6、ON/OFF/OFF）を属性込みで復元し、試験前の全215ファイルとの一致を確認した。SDは復元済みでPC接続のまま。追加USB接続は要求せず、SD移動はPC→本体→PCにまとめた。追加のSNES起動は不要。
