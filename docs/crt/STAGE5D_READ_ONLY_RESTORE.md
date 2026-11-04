# 第5d段階：ゲーム別保存値の読取り専用復元

## 基準と範囲

実機確認済み第5c（crt-stage5c-hw-20261103、親4e4ba09、FW83d7055）を基に、取得済みROM IDから保存recordを読み、起動成功後に設定へ反映する部分だけを追加する。FW commitは42359d6976edf98089bdbc91ac8725fce2fd0bef。基準branch tangcore-integratedからの既存履歴を維持し、FWはcrt-stage5d-restore-20261104、親はcrt-osd2-stage1で作業する。

JTAG、FPGA、ROM loader、日本語表示、titles.csvの表示順、CSV選択時のsnapshot、OSD入力を変更しない。全体の第5段階は未完了。firmwareからの保存、directory作成、defaults読込み、Reset操作はまだ追加しない。旧第5段階の起動停止原因が解明したとは扱わない。

## 読取り位置と所有

第5cのROM ID読取り後、既存ROM loaderを呼ぶ前に2個のrecordをFA_READで順番に読む。loader用のnoncacheable fcoreと64 byte整列fbufを再利用する。各fileはopen後の成功・失敗いずれもcloseを試み、close後に次のfileまたはloaderへ進む。追加の大きいstack/heap領域は持たない。今回の実機対象はConsole138K/NESであり、他coreの並行storage利用を検証済みとはしない。

IDが無効、volumeがsd/usb以外、systemが1〜255外、sizeが0の場合はfileへアクセスしない。取得・読取り失敗だけではゲーム起動を止めない。新しいprogram、ROM load開始、load失敗時に前ゲームのIDと復元結果をclearする。

## keyと32 byte record

同じROM volumeの `/crt/SS-CCCCCCCC-ZZZZZZZZZZZZZZZZ.a` と `.b` を読む。SSはsystemの2桁hex、CはROM全byte CRC32の8桁hex、Zは64 bit sizeの16桁hex。volumeはdirectory自体で分かれる。filename・日本語表示名をkeyに含めない。

| offset | byte数 | 内容 |
| --- | ---: | --- |
| 0 | 4 | magic CRT1 |
| 4 | 1 | schema 1 |
| 5 | 1 | system ID |
| 6 | 1 | kind 0＝user override、1＝推奨値へ従うtombstone |
| 7 | 1 | reserved＝0 |
| 8 | 4 | ROM CRC32、little endian |
| 12 | 8 | ROM size、little endian |
| 20 | 1 | bit0 enable、bit1〜2 blur、bit3〜4 scanline。上位bitは0、tombstoneは全0 |
| 21 | 3 | reserved＝0 |
| 24 | 4 | generation、little endian |
| 28 | 4 | byte0〜27のCRC32/IEEE、little endian |

file sizeと読取byte数がちょうど32であり、magic、record CRC、schema、key、kind、reserved、設定範囲が正しいものだけを有効とする。最大33byteを既存bufferへ読み、過長fileも拒否する。

2個とも有効ならgeneration差を32 bitで比較する。差が1〜0x7fffffffなら後者が新しく、wrapを扱う。同世代・同内容は受理、同世代・異内容または差0x80000000はCONFLICTとして両方を使用しない。片側が破損して他側が有効なら有効側をRECOVEREDとして使う。I/O失敗またはCRCが正しい未知schemaが片側にあれば、古い値を選ばず推奨値へ戻す。fileを変更・削除・修復しない。

## 適用順位とOSD2

有効なuser override ＞ 選択時のtitles.csv推奨値 ＞ builtin全OFF。明示的な全OFF保存値もCSVより優先する。有効tombstoneはuser値を適用せず、起動時のCSV推奨値またはbuiltinに従う。system/global defaultsは将来の別段階とする。

OSD2はCRT RESTORE - STAGE5D、READ ONLY / NO SAVEと表示する。INITIALはUSER/CSV/DEFAULT、空き行のSTOREはUSER/RESET/RECOVERED/MISSING/BAD SAVE/READ ERROR/NEW SCHEMA/CONFLICT/NO ROM IDを表示する。STOREは起動時に読んだ結果であり、現在の調整値が保存済みという意味ではない。APPLYは従来どおりFPGAのFRAME ACKと独立する。

CLOSEとPOS、選択行、外形は変更しない。開き直しは調整値とIDを保持し、ゲームの起動し直し・電源再投入では保存値を再読取りする。この版でOSDから変更して閉じてもSDへ保存しない。Reset UIはまだないが、将来の形式との整合のためtombstoneの読取りは試験する。

## PCでの確認

関連9本（crt_restore、rom_id、crt、osd、launch、titles、folders、scroll、wrap）とfirmware buildが成功。実readerをfake FatFsで実行し、2世代・wrap・tombstone・明示OFF、record全byteの破損、size、reserved、key、未知schema、I/O/close失敗、世代競合、片側からの復帰、volume/system分離を確認した。main adapterの実sourceから、ID→record読取り→既存loaderの順序、失敗後の起動継続とclear、session受渡しを確認した。OSDではCSVより保存値を優先することと、再表示時の保持を確認した。

新firmwareは224576 bytes、SHA256 9609a2dabb64f1e5c1fff3caf3622680b5c73487c0867eed8ffd4e13b69996e7。readerのcompiler stack usageは240bytes、number helperは32bytes（下位FatFs/driverを含めた全呼出深さではない）。記録はverification/crt-stage5d-restore。FPGAの新buildは行わず、実機合格第4bと同じNES imageを使う。

## 実機試験：A（firmwareのみ）

直前の第5c全flash照合済みsnapshotとmicroSD全体を保全する。最初はSDを変更せず、firmwareだけ更新する。ROM/CSV/font/NES/monitor/既存logを維持し、未承認の保存fileがあれば上書きせず確認する。

1. 日本語一覧・順序、Dr. Mario/Pac-Manの起動・映像・音声・操作を確認する。
2. Dr. MarioはCRC7623dffd、ON/WEAK/STANDARD、INITIAL CSV、STORE MISSING、APPLY FRAME ACK。
3. Pac-ManはCRCebbb19bf、全OFF、INITIAL DEFAULT、STORE MISSING、APPLY FRAME ACK。
4. OSD閉じ→開き直しで調整値保持、ゲーム再起動でCSV/builtinへ復帰する。

## 実機試験：B（PCで作成した試験record）

A正常後にmicroSDをPCへ戻して再退避し、未使用の3pathへ試験recordを追加する。既存fileがある場合は置換しない。firmwareは再書込みしない。ROMを配布物へ含めない。

- Dr. Marioのa：generation1、全OFF。b：generation2、ON/STRONG/WEAK。新しいbが適用され、INITIAL USER、STORE USER、FRAME ACKとなる。
- Pac-Manのa：32byte全0の破損record。全OFF、INITIAL DEFAULT、STORE BAD SAVE、FRAME ACKへ戻り、起動できる。
- OSD開き直し、ゲーム切替、通常の電源再投入で同じ復元結果となる。OSDで調整して閉じても保存せず、起動し直すと試験recordの値へ戻る。
- 5位置・入力遮断・解放待ち・OSD1排他を確認する。終了後にSD全byteが試験record追加時と一致することを確認する。PC上で試験recordを退避して元のSDへ戻す。tombstone、I/O失敗などの実機試験は別途区別し、PC成功から推定しない。

実機合格tagは依頼した試験の報告後に作る。現時点で実機は未確認。

## 試験A用firmwareの実機反映

2026-11-04T10:30:10.486556+09:00、既知Console138Kへfirmwareだけを反映した。基板SHA、新FW全byte、4MiB全flash読戻しと更新範囲外を照合した。SD全59filesを新たに退避し、CSV/ROM/NES/monitor/font/既存logを含む全fileが同一と確認した。保存recordはまだ追加していない。初回mode0 READの接続確立に失敗し、再programせずmode2 READで成功した。SDK設定を元のbyteへ復帰した。

復旧用は直前の実機合格第5c全読戻しをコピーしたもので、新たな書込み前flash読取りを行ったとはしない。導入照合はverification/crt-stage5d-restore/deployment.json。通常起動・日本語一覧・2本の起動とCSV/defaultへの復帰・STORE MISSING・FRAME ACKは利用者の実機確認待ちである。試験Bと第5d完了tagは未着手。

## 試験A：起動と保存データなしの復帰結果

2026年11月4日、利用者が「1-3正常」と回答した。日本語NES一覧と順序、Dr. Mario/Pac-Manの起動・映像・音声・操作、STAGE5D表示、ROM ID 7623dffd/ebbb19bf、Dr. MarioのCSV ON/WEAK/STANDARD、Pac-ManのDEFAULT全OFF、両方のSTORE MISSINGとFRAME ACKを確認した。OSD1による一覧への復帰と別ゲーム起動も正常だった。結果はverification/crt-stage5d-restore/hardware-results.json。

試験Aの残りは、調整した値がOSD開き直しで保たれることと、ゲームを起動し直すとCSV値へ戻ること。追加書込みは不要。試験B用recordはまだ追加しておらず、保存値の実機復元を確認済みとはしない。第5d完了tagはまだ作らない。

## 試験Aの依頼項目完了

2026年11月4日、利用者が残り2項目を「1-2正常」と回答した。Dr. Marioのblur/scanlineをSTRONGへ変更し、OSD2を閉じて開き直しても値が保持され、ROM ID 7623dffd、INITIAL CSV、STORE MISSING、FRAME ACKが正常だった。OSD1の一覧へ戻り同ゲームを起動し直すと、ON/WEAK/STANDARDのCSV値へ戻ることも確認した。これで保存データがない場合の試験Aは依頼項目をすべて完了した。

次は試験B用の3recordをPCからmicroSDへ追加する。直前に全fileを再退避・照合し、既存recordは上書きしない。Dr. Marioの新しい世代のON/STRONG/WEAK復元とPac-Manの破損record拒否は実機未確認。firmware再書込みは不要。第5d全体は未完了で、完了tagはまだ作らない。

## 試験B用recordの追加

2026-11-04T10:44:25.176429+09:00、前回と同じ物理identityのF:TANGCONSOLEへ試験用3recordを新規追加した。直前にSD全59fileを新しい退避先へコピーしてSHA照合し、試験A前と全fileが同一であることを確認した。既存crt directoryがないことを確認し、既存fileは上書きしていない。追加後は計62fileを列挙・SHA照合し、元の59fileが同一であることを確認した。firmwareとflashにはアクセスしていない。

Dr. Marioのaはgeneration1・全OFF、bはgeneration2・ON/STRONG/WEAK。Pac-Manのaは32byte全0の破損record。確認済みの試験recordとSHAはverification/crt-stage5d-restore/phase-b-fixture-installation.jsonに記録した。通常起動後の保存値復元・破損時の復帰は実機報告待ちであり、まだ第5dを完了としない。試験後のSD不変照合と3recordの保全・取外しも未実施。
