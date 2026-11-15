# SNES OSD2 MISSINGと初回保存

2026年11月15日（日本時間）。保存slotが両方とも存在しない状態から、SNES起動1回でMISSINGと初回USER保存を確認する。実機報告と試験後の照合結果は `verification/osd2-missing-20261115/result.json` に記録する。

## 構成と接続方針

- 親の起点：`527f2bf2305717af56e8f5e1365b47db0a9d57f9`。
- firmware：`95871ef8e9ef547767b145cee4e85577e8bb4972`。製品ソースの変更なし。
- SNESTang：`9a1360fd764b7ca85e3b0013ac684a36ec3a04a9`。SD image SHA-256は `b3df3e53444acdc083f45d11e194772e50ee91226dbcf9b23424e6732957737e`。
- 直前のCONFLICT確認で読取り照合済みの通常版Flashを継続使用する。今回はUSBの再接続とFlash再読取り・書込みを行わない。この試験時点で新しくFlashを読み取ったという意味ではない。
- 開始時にmicroSDはPCへ接続済み。新規退避・準備を同じ接続中にまとめ、本体で1回試験し、PCへ戻した同じ接続中に照合・復元する。USBケーブルの挿抜は要求しない。復元後の本体への返却はユーザーの都合に合わせる。

## 元データと試験条件

SD全215ユーザーファイルを内容・属性込みで新しく退避した。直前のCONFLICT試験後に復元した全ファイルと一致。Windows管理領域 `System Volume Information` と `$RECYCLE.BIN` は対象外。

対象はスーパーマリオコレクション、raw CRC32 `232bb5b8`、2,097,152 byte。`titles.csv` にCRT指定はなく、`crt/defaults.tsv` もない。試験前の `.a` はReset generation 7、`.b` はUSER generation 6、ON/OFF/OFF。

今回の新規退避を確認してから、対象の保存slot 2件だけを一時的に除去する。残る213ファイルは内容・属性を維持する。これにより `BUILT-IN`、`MISSING`、全OFFで起動する。

## PC試験

`tools/test_osd2_missing.py` は指定した現行firmwareの製品parser、保存処理、OSD処理を直接compileする。空の保存領域でMISSINGを確認し、ON/OFF/OFFへ変更して初回SAVEを1回実行する。

- 小型表示はSAVE OK、補助表示はSAVE: SAVED。OSDは開いたまま。
- LOADED FROM: BUILT-INとSAVE READ: MISSINGは起動時情報として維持。
- `.a` だけに32 byteのUSER、generation 1、値1を保存。write・sync・書込み用open各1回。
- 生成された保存byteが独立に作った期待recordと完全一致し、製品parserでもUSERとして読める。
- その後の未保存OFF previewを取消すと、最後に保存したONへ戻る。追加書込みなし。
- 新しいsessionでUSERとして復元する処理はPCで確認。実機の電源再投入後のUSER読込みは今回の1起動試験に含めない。PCのFRAME ACKも模擬入力であり、実応答は実機報告で確認する。

Windows、Python 3、`C:/msys64/ucrt64/bin/g++.exe` を使用する。親が指定するfirmware submoduleを準備し、親repositoryのルートで実行する。

```powershell
python tools/test_osd2_missing.py --firmware firmware-bl616 --output ../osd2-missing-pc
```

## 実機手順（SNES起動1回）

USB P1で対象ゲームを起動。日本語一覧と並び順、映像・音声・通常操作を確認する。各操作後は全ボタンを離す。

小型OSD2は見出し→CRT OFF→BLUR OFF→SCAN OFF→SAVE→RESET（実行しない）→POS→START:INFOの表示順で確認。

補助表示はSAVE: RECOMMENDED→LOADED FROM: BUILT-IN→SAVE READ: MISSING→APPLY: FRAME ACK→ROM ID: 232bb5b8→DEFAULTS: MISSING→RESET = RECOMMENDED→POS→START:HIDEの順で確認。

同じ起動中にCRTだけONへ変え、SAVEを1回実行。SAVE OKとOSDの継続表示、補助表示のSAVED／BUILT-IN／MISSING／FRAME ACKを確認する。続いてCRTをOFFへ変えるが保存せず、XまたはYで取消す。全解放後に開き直してON/OFF/OFF、SAVE OKとSAVE: SAVEDへ戻ることを確認する。

終了後は電源を切り、SDだけPCへ戻す。

## 試験後の照合と復元

全ファイルを新たに退避し、`.a` の期待record新規作成以外に内容・属性の変化がなく、`.b` が存在しないことを確認する。期待recordは32 byte、SHA-256 `949fd17b3837882af159aab5825400e344ef61cb4c3dbe246c432009b40bca59`。実際の保存byteを製品parserへ通してUSER、generation 1、ON/OFF/OFFと確認する。

予定外の変更は退避したうえで処理を止める。一致した場合は今回退避した元の2件を属性とともに復元し、試験前の全215ファイルと内容・属性の一致を確認する。追加のSNES起動は要求しない。ROM、実際の保存record、Flash原本や機器固有IDはローカルで保持する。
