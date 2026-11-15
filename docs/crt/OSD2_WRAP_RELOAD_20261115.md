# SNES OSD2 世代折返し後の電源再投入による読込み

2026年11月15日（日本時間）。PC試験・元データ退避と対象2件の導入・全215ファイル照合を完了し、実機確認待ち。対象以外の213ファイルは内容・属性とも不変。実機結果、試験後のSD照合、復元は未完了。

## 目的と構成

前回は同じ起動中の2回のSAVEにより `0xffffffff → 0 → 1` を確認した。今回は電源を切った本体を通常起動し、SNESの新しいsessionで世代0を旧世代 `0xffffffff` より新しいrecordとして採用することを確認する。

- 親repositoryの起点：`e66afcadb8c9822d735ea349e3f7db65582467f8`。
- firmware：`95871ef8e9ef547767b145cee4e85577e8bb4972`。製品ソースの変更なし。
- SNESTang：`9a1360fd764b7ca85e3b0013ac684a36ec3a04a9`。
- SNES image SHA-256：`b3df3e53444acdc083f45d11e194772e50ee91226dbcf9b23424e6732957737e`。
- 先行するCONFLICT試験前のFlash全体の照合と、それ以降にfirmwareを書き換えていない作業履歴を引き継ぐ。今回のFlash再読取り・書込み、BOOT接続、USB挿し直しは行わない。
- microSDは開始時点でPCに接続済み。PC→本体→PCの移動、SNES起動1回、SAVE・RESETとも0回を予定する。

## 退避とrecordの由来

microSDの全215ユーザーファイルを内容・属性込みで新規退避し、前回の復元済み状態との一致を確認した。Windows管理領域 `System Volume Information` と `$RECYCLE.BIN` は対象外。

対象ゲームはスーパーマリオコレクション。ROM IDはCRC32 `232bb5b8`、サイズ2,097,152 byte。元のaはReset世代7、bはUSER世代6（ON/OFF/OFF）。`crt/defaults.tsv` はなく、組込み推奨値はOFF/OFF/OFF。

| slot | 世代 | 設定 | 由来 |
| --- | --- | --- | --- |
| a | `0xffffffff` | ON/WEAK/STD | 前回の実機試験前に導入したrecordと同一byte |
| b | `0` | OFF/WEAK/STD | 前回の実機SAVEが生成し、2回目SAVE後のSDから退避したrecordと同一byte |

両方ともschema 1・USER・CRC有効の32 byte record。独立生成した試験用byteが上記の退避済み証拠と完全一致することを確認した。この組合せは前回の1回目SAVE後の状態を再構成したもの。前回の中間SDを直接読み取ったものではない。前回の最終a世代1／b世代0をそのまま再投入する試験とは区別する。

世代0のOFFは旧aのONと異なり、WEAK／STDは組込み値のOFF／OFFと異なる。したがって、起動直後のOFF/WEAK/STDとUSER表示を併せて確認することで、採用した保存値を識別する。

## PC試験

`tools/test_osd2_wrap_reload.py` は2件を独立生成し、現行の製品parser・SNES session・OSD処理をcompileする。新しいprocessでSD読取りを模擬し、次を確認済み。

- b世代0をUSERとして選択し、OFF/WEAK/STDを適用。
- SAVE OK／SAVED、LOADED FROM: USER、SAVE READ: USER。
- CRT ONの未保存previewはSAVE *／UNSAVED。取消し・再表示でOFF/WEAK/STDとSAVEDへ復帰。
- mkdir・書込み用open・write・syncの試行回数はすべて0。
- FRAME ACKはPCでは模擬応答。実応答は実機で別途確認する。

```powershell
python tools/test_osd2_wrap_reload.py --firmware firmware-bl616 --output ../osd2-wrap-reload-pc
```

復元前の防止処理もPC上の一時領域で確認した。record変更・record欠落・無関係なファイルの変更・2件目の元データ退避の破損について、観測結果を保持したまま書込み前に停止する。

## 実機確認手順：1起動、保存なし

microSDを安全に取り外し、電源を切った本体へ戻して通常起動。USB P1で対象ゲームを1回だけ起動する。日本語一覧・並び順、映像・音声・通常操作を確認。各操作後は全ボタンを離す。SAVEとRESETは実行しない。

SELECT＋左で開く小型OSD2の表示順：CRT X/Y:BACK → CRT OFF → BLUR WEAK → SCAN STD → SAVE OK → RESET → POS → START:INFO。

START単独で開く補助表示の追加行：SAVE: SAVED → LOADED FROM: USER → SAVE READ: USER → APPLY: FRAME ACK → ROM ID: 232bb5b8 → DEFAULTS: MISSING → RESET = RECOMMENDED → POS → START:HIDE。

小型表示に戻りCRTだけONへ変更。SAVE *、補助表示UNSAVED／USER／USER／FRAME ACKを確認する。保存せずXまたはYで閉じ、全ボタンを離して開き直す。OFF/WEAK/STD、SAVE OK、補助表示SAVED／USER／USER／FRAME ACKへの復帰を確認する。

終了後は電源を切りmicroSDだけPCへ戻す。相違があれば追加SAVE・再起動を行わず、その段階と表示を記録する。

## 試験後のSD照合と復元計画

試験後の全ファイルを新規退避し、導入直後の全215ファイルと内容・属性が一致することを確認する。現物recordを製品parserとOSD試験に通し、b世代0の採用を再確認する。元の2件の退避が正常であることを両方とも検証してから復元し、全215ファイルを試験前の状態と再照合する。未知の変更があれば退避したうえで復元書込み前に停止する。

ROM、保存データ、Flash原本、機器固有ID、SD全退避はrepository外でローカル管理する。今回の公開操作は未依頼・未実施。
