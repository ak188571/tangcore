# SNES OSD2 `SAVE READ: CONFLICT` 実機確認

2026年11月15日（日本時間）。Console138Kの通常版を維持し、同じ世代で内容が異なる有効な保存recordの拒否を、SNESの起動1回で確認する。

## 構成と事前照合

- 親の起点：`1e8b843efc391f888994adb6215b03758d1597a9`。
- firmware：`95871ef8e9ef547767b145cee4e85577e8bb4972`。
- SNESTang：親が指定する `9a1360fd764b7ca85e3b0013ac684a36ec3a04a9`。
- 実機firmware image SHA-256：`e60ef33db7bf38a02d88bf5e7fee8aac444c502ad4fa3dc7dc2ecbf16458d77a`。
- SD上のSNES image SHA-256：`b3df3e53444acdc083f45d11e194772e50ee91226dbcf9b23424e6732957737e`。11月12日のSPI32通常版build記録と一致。
- 現物のFlash全4 MiBを新規に読み取り、11月15日の通常版復元時の原本と全byte一致。Flash書込みは行わない。
- SDの215ユーザーファイルを新規退避し、11月15日の復元記録のSHA-256と全件一致。診断ログ29件も保存。Windows管理領域 `System Volume Information` と `$RECYCLE.BIN` は対象外。
- SNESの保存・復元・推奨値・OSD関係5ファイルのGit blobは、11月7日の実機合格版と一致。
- 対象ROMはraw CRC32 `232bb5b8`、2,097,152 byte。現在の `titles.csv` は名前と日本語タイトルの2列でCRT指定なし。`crt/defaults.tsv` なし。期待初期値はBUILT-IN・全OFF。

## PC試験

`tools/test_osd2_conflict.py` と `tools/osd2_conflict_test.cpp` は、指定したfirmware checkoutの製品ソースを直接compileする。生成したそのままの32 byte×2件を読み込み、次を確認する。

- 両slotはschema 1、USER、generation 8。値だけが異なり、各CRCは有効。
- 製品parserがCONFLICTを返し、どちらの値も採用しない。
- 小型OSDの全OFF、補助表示のBUILT-IN／CONFLICT／MISSING。
- CRT変更後のUSER SAVEが失敗し、OSDは開いたまま、起動時情報を保持。
- X/Y相当の取消しと再表示で全OFFに戻る。
- Reset modeのSAVEもPCで拒否する。実機では追加のSAVEを要求しない。
- `f_mkdir`、書込み用open、write、syncの呼出しは0件。

PC上のFRAME ACKは模擬入力であり、FPGAからの実応答は実機の報告で別途確認する。

## 実機手順とデータ保護

実機試験前の `.a`／`.b` を、内容と属性を含め新しく退避した。導入はPCで合格した2件だけとし、全215ファイルの内容・属性を導入後に照合した。firmware、FPGA image、日本語一覧、`titles.csv`、NES保存値を維持した。

USB P1でスーパーマリオコレクションを1回起動する。小型表示は見出し→CRT→BLUR→SCAN→SAVE→RESET→POS→START:INFOの順。補助表示はSAVE状態→LOADED FROM→SAVE READ→APPLY→ROM ID→DEFAULTS→RESETの説明→POS→START:HIDEの順に確認する。

同じ起動中にCRTをONへ変更し、SAVEを1回だけ試す。SAVE FAILEDとOSDの継続表示、補助表示のSAVE: FAILED／BUILT-IN／CONFLICT／FRAME ACKを確認。XまたはYで取消し、全解放後に開き直して全OFFと失敗表示の解消を確認する。

終了後は電源を切りSDをPCへ戻す。試験後の全ファイルを先に退避し、導入直後と内容・属性を照合する。予定外の変化があれば原本を保持して復元処理を止める。無変化を確認してから、今回退避した元の2件と属性を復元し、全215ファイルを試験前と再照合する。

実機報告と復元結果は `verification/osd2-conflict-20261115/result.json` に記録する。実機Flash、ROM、個別保存record、機器識別情報を含む退避原本はローカルで管理する。
