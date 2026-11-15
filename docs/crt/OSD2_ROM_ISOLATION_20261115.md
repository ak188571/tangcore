# SNES OSD2 ROMごとのCRT設定と保存先

2026年11月15日（日本時間）。2本のROMを順に起動し、それぞれ自身のCRT設定を読み込むことと、各1回のSAVEが対応するROMのrecordだけを更新することを確認した。試験後のmicroSD照合と元データの復元も完了した。

## 試験条件

- 親repositoryの起点は `d45e04b8fc001cc2aa9e1e3fb456f2a7222fcaa1`。firmwareは `95871ef8e9ef547767b145cee4e85577e8bb4972`、SNESTangは `9a1360fd764b7ca85e3b0013ac684a36ec3a04a9`。先行試験でFlashを照合した構成を使う。
- 開始時の全215ユーザーファイルを内容・属性とともに新規退避した。前回の復元状態と一致する。Windows管理領域は対象外。両ROMの実CRC32・サイズを退避から照合した。`snes/titles.csv` はタイトル指定のみで、`crt/defaults.tsv` はない。
- 導入ではスーパーマリオコレクションのaの置換とパネルでポンのaの追加だけを行う。マリオのbは元のUSER世代6（ON/OFF/OFF）を保持する。パネルでポンのbはSAVE時に新規作成される。

| 順 | ROM | CRC32・サイズ | 起動時に採用するa | SAVE後に最新となるb |
| --- | --- | --- | --- | --- |
| 1 | スーパーマリオコレクション | `232bb5b8`・2,097,152 byte | USER世代7、ON/WEAK/STD | USER世代8、OFF/WEAK/STD |
| 2 | パネルでポン | `14d70786`・1,048,576 byte | USER世代20、OFF/STD/WEAK | USER世代21、ON/STD/WEAK |

## PC試験

試験用recordと保存後に期待するrecordを独立に生成し、firmwareの読込み、SNES OSD2 session、保存処理をcompileして確認した。1本目から2本目へ切り替えたときの初期設定・ROM ID・USER表示、各1回のSAVEと期待するbyte・世代・書込み先、各aの不変、SAVE後の選択を確認した。`FRAME ACK` はPCで模擬した。

```powershell
python tools/test_osd2_rom_isolation.py --firmware firmware-bl616 --output ../osd2-rom-isolation-pc
```

## 実機手順

microSDをPCから本体へ戻して通常起動する。USB P1で1本目を起動し、日本語一覧・並び順と通常操作を確認する。各操作後は全ボタンを離す。SELECT＋左でOSD2を開き、見出し、CRT、BLUR、SCAN、`SAVE OK`、`RESET`、`POS`、`START:INFO` の順で確認する。START単独で補助表示を開き、`SAVE: SAVED`、`LOADED FROM: USER`、`SAVE READ: USER`、`APPLY: FRAME ACK`、対応する `ROM ID`、`DEFAULTS: MISSING`、`RESET = RECOMMENDED`、`POS`、`START:HIDE` の順で確認する。

STARTで小型表示へ戻り、CRTだけを表のSAVE後の値に変え、`SAVE *` を確認する。SAVEを1回行い、OSDが開いたまま `SAVE OK` になり、補助表示が `SAVED`／`USER`／`USER`／`FRAME ACK` になることを確認する。RESETは各ROMで0回。

1本目のSAVE確認後にXかYでOSD2を閉じ、全ボタンを離す。SELECT＋右でOSD1を開き、`Return to Game List` を実行する。2本目を一覧から起動し、初期値のBLURとSCANが1本目の保存値と入れ替わっていること、ROM IDが2本目のものに切り替わったことを確認してから同じ手順でSAVEする。各ROMは1回だけ起動する。

2本目の確認後に電源を切り、microSDだけPCへ戻す。内容・属性と名前を全件照合し、2件のbが期待するROMキー・世代・値・CRCで、両方のaと他のファイルが導入直後と一致することを確認する。マリオのa/bを復元し、新規作成したパネルでポンのa/bを除去して、試験前の全215ファイルと再照合する。

## 実機結果とSD復元

ユーザーから「すべて想定通り。microsd接続済み」と報告を受けた。1本目はON/WEAK/STDからOFF/WEAK/STDへ変更して保存し、一覧から起動した2本目は自身のOFF/STD/WEAKを読み込んだ。2本目はON/STD/WEAKへ変更して保存した。両方でROM ID、USERの読込み、SAVE成功、`FRAME ACK`、日本語一覧と並び順、映像・音声・通常操作を確認した。

PCに戻ったmicroSDの全217ファイルが、予定した試験後の状態に内容・属性ともに一致した。1本目のbは世代8、2本目のbは世代21で、対応するROM ID・サイズ・CRCと上表の保存値が一致した。導入直後から変わったのは各ROMのbの2件だけだった。採取した実データを製品の読込み処理に通し、両方がそれぞれの新しいbを選ぶことをPCで確認した。実機の起動は各1回で、SAVE後の再読込みの検証はこのPC試験で行った。

退避した元のマリオのa/bを復元し、試験用に作ったパネルでポンのa/bを取り除いた。全215ファイルの内容・属性が試験前と一致し、microSDは復元済みでPCに接続している。microSDの移動はPCと本体の1往復、USBケーブルの挿し直しは0回。詳細は `verification/osd2-rom-isolation-20261115/result.json` に記録した。
