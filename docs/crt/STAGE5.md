# 第5段階：推奨初期値、ゲーム別保存、Reset to Recommended

## 対象と現在の状態

初版の実機試験では、複数のNESゲームでFPGA image再構成後の `Usercode=0, status=0` 表示から先へ進まないことが報告された。保存試験は未到達。JTAG終了状態と失敗時のinterrupt復帰を修正し、関連8本の自動試験とfirmware buildを完了したが、修正版の起動・保存は実機再試験待ちである。詳細は `STAGE5_STARTUP_FIX.md` を参照する。以下の初版の導入実績は保持し、第5段階を完了扱いにしない。

実機確認済み `crt-stage4b-hw-20261103` を基準に、BL616 firmwareへ保存機能を追加する。対象は現在CRTに対応するConsole138K／NES。NESの映像・UART・設定bit配置は変更せず、実機確認済み4bのNES imageをそのまま組み合わせる。第5段階の自動試験とfirmware build、実機導入・全flash読戻し照合は完了した。通常起動後の保存・再起動試験は利用者の確認待ち。記録は `verification/crt-stage5/` に保存する。

日本語一覧、16×16 font、titles.csv順序、OSDの5位置・排他・入力遮断・終了後の全解放待ちを既存の前提とする。GitHubへのpushは行わない。

## この段階の設計決定

- 設定は、保存済みゲーム個別値→同じfolderのtitles.csv推奨値→system既定値→global既定値の順に解決する。組として3項目を選び、項目ごとの部分上書きは行わない。
- 保存keyはcoreのsystem ID、起動前の非圧縮ROM全byteのCRC32/IEEE、64 bit size。NESのheaderやtrainerを含み、loaderによる処理前に計算する。filename、表示名、CSV行番号を保存keyにしない。
- ROMを実際に起動した `sd:` または `usb:` に設定を保存する。もう一方のvolumeへ暗黙に切り替えない。CRCを読み取れなければNO ROM IDを表示し、個別保存を行わない。
- CloseまたはX/YでOSD2を閉じるとき、変更がある場合だけ保存する。設定値を調整するたびには書かない。保存とFPGAのFRAME ACKは別の状態として表示する。
- OSD位置・controller profile・hotkeyはこのゲーム別recordへ保存しない。POSは従来どおり実行中の共通値を保持する。

## titles.csvの互換拡張

従来のUTF-8 TAB区切り2列 `name<TAB>title` を引き続き受理する。任意の推奨値を持たせる形式は、headerが次の3列の場合だけ受理する。

```text
name<TAB>title<TAB>crt_v1
game001.nes<TAB>表示名<TAB>1:1:2
game002.nes<TAB>別の表示名<TAB>
```

`<TAB>`は実際のTABへ置き換える。`crt_v1` は `enable:blur:scanline`。enableは0/1、blurとscanlineは0=OFF、1=WEAK、2=STANDARD、3=STRONGである。空欄は下位の推奨階層へ進む。上の数値は形式説明用であり、そのゲームに公式に推奨する画質ではない。

2列・3列ともBOM/CRLF、空の表示名、タイトルの改行escape、ASCII filename、重複禁止、CSV順序と未登録名の後続配置を維持する。未知column、列数不一致、範囲外の値、folderへの推奨値指定は受理しない。不正なファイルを一部だけ採用せず、表示名・順序・推奨値を従来のerror経路へ戻す。推奨値を持つ行と表示名・元filenameを同じ並べ替えで移動する。

PC側のcheck_titles.py、read_titlesを使うfont生成処理にも同じ形式を接続した。新firmwareからtitles.csvへ利用者の調整値を書き戻すことはない。旧firmwareは3列形式に非対応なので、旧版へ戻す際は退避した2列のtitles.csvも対応して戻す。すべての既存CSVを3列へ移行する必要はない。

## systemとglobalの既定値

ROMと同じvolumeの `/crt/defaults.tsv` を任意で置ける。こちらもUTF-8 TAB区切りで、次の形式とする。

```text
system<TAB>crt_v1
*<TAB>0:0:0
nes<TAB>1:1:1
```

system名は `nes`、`snes`、`gba`、`genesis`、`sms`、`pc`、globalは `*`。未知名、重複、範囲外値、未知形式があればファイル全体を不採用とし、BAD DEFAULTSを表示する。空欄は継承。ファイルや指定がなければ組込みのglobal値 `0:0:0` を使う。現在の他coreがCRTに対応済みという意味ではない。

起動時に解決した推奨値を同sessionのResetでも使う。静的推奨値ファイルの変更は次のゲーム起動から反映する。

## 2世代recordと復旧

保存先は `/crt/SS-CCCCCCCC-ZZZZZZZZZZZZZZZZ.a` と `.b`。SSはsystem IDの16進2桁、CはROM CRC32の8桁、Zはsizeの16桁である。例としてCRC32がcbf43926、sizeが9のNESは `01-cbf43926-0000000000000009.a/.b` となる。

各recordは32 byte。magic、schema version、system、ROM CRC、ROM size、3設定値、世代番号、record全体の検査用CRC32を持つ。全項目を検証し、正常なrecordの新しい世代を採用する。世代番号の32 bit折返しも扱う。

保存時は両slotを読み直し、最新の正常recordがあるslotを残して反対側へ書く。全byte書込み、f_sync、f_close、再open後の内容一致を確認してからSAVEDにする。前回の失敗で実際には正常な新世代が残った場合も、再読込でその世代を保護する。片方が破損していれば正常な世代へ復旧してRECOVERED、両方が破損していれば推奨階層へ戻してBAD SAVEを表示する。

読出しI/O errorや未知schemaがある場合は安全に書込先を決められないため上書きを止める。FAT全体の損傷やSD内部の書込みcacheまで、この32 byteの仕組みで完全に復旧できるとは保証しない。物理的な電源断耐性・媒体抜去は実機で未確認である。

現targetのNESでは、設定I/Oはmain taskが担当し、ROM loaderと順次実行する。FatFsの既存設定は非reentrantであり、別taskがdisk I/Oを行うcoreへ拡張する場合は排他を別途照合する。

## OSD2と保存失敗

対応するNESでは `CRT READY - STAGE5`、`CLOSE SAVES CHANGES` を表示する。設定3項目、APPLYに加えてSAVE、SOURCE、必要なNOTE、RESET TO RECOMMENDED、CLOSE、POSを表示する。

SAVEはSAVED、RECOMMENDED、UNSAVED、FAILED、NO ROM ID等を区別する。SOURCEはUSER、GAME、SYSTEM、GLOBAL。保存済みであることを、FPGAへ適用済みという意味に読み替えない。

保存失敗時もRAM上の調整値とゲーム映像を維持し、OSDを開いたままFAILEDを表示する。CLOSEまたはX/Yを押し直すと再試行できる。追加されるLEAVE UNSAVEDを選べば保存せずゲームへ戻れる。同ゲームで再びOSD2を開けばRAM値を保持し、再試行も可能である。別ゲームへの移動や再起動では未保存のRAM値を破棄する。失敗したResetでは旧個別recordが残り得る。

通常dialogの終了後のbutton解放待ちは維持する。保存失敗によるCloseの拒否は共通Menuのon_closeで扱い、押しっぱなしで拒否を迂回しない。設定とResetのA/B操作は引き続き押下edgeで1回だけ処理し、保持中も描画・ACK問い合わせを続ける。

## Reset to Recommended

ゲーム自体のResetは行わない。保存済み個別値を無視し、起動時に解決した推奨値へRAM値を戻してFPGAへ送り直す。Close時には推奨値そのものを固定保存せず、overrideを無効にするtombstoneを新世代へ保存する。このため後日の推奨値更新に追従できる。Reset後に再調整して推奨値と異なる値にした場合は、その一式を個別値として保存する。

## 実機導入記録

2026年11月3日20:44頃、既知のConsole138KとTANGCONSOLEのmicroSDを確認し、58ファイルを新たに退避した。firmwareと試験用のnes/titles.csvだけを更新した。NES imageを含む他57ファイルは退避時と一致した。firmwareの基板側SHA-256と4 MiB全flashの読戻しを照合し、0x40000未満と0x80000以降が直前の実機確認済み4bと一致した。SDK設定も元のbyteへ復元した。

最初の全flash読取は接続確立に失敗したため、firmwareを再書込みせず、読取方式を切り替えて照合した。成功・失敗のlogを保持している。復旧用flashは前回の実機合格4bの検証済み全読戻しからコピーしたもので、今回書込み前に新しく読取を行った意味ではない。元の2列CSVも今回のSD退避に保存した。

導入実績は `verification/crt-stage5/deployment.json` を参照する。通常起動後の画質・保存・再起動試験はまだ実施していない。試験用ZIPとそのmanifestはbuild時点のsnapshotとして保持する。

## 自動試験と実機試験

7本の関連試験で、設定階層、ROM内容・size・system・volumeの分離、ROM改名、Close保存、古い返信の拒否、Resetと推奨値更新、実際のpopupでの保存失敗・再試行・未保存終了を確認した。32通りの途中書込み長、32箇所の1 byte破損、世代折返し、open/write/sync/close/mkdir/read失敗、読戻しでの破損検出、未知schemaの保持、失敗したResetの旧override保持も確認した。OSD、起動、拡張CSV、font生成、日本語folder、scroll、改行表示の回帰試験も成功した。

firmwareは228,048 byte。NES imageは4bと同一であり、第5段階で新しいFPGA buildを行ったと記録しない。既存4bのsetup/hold 0/0と実機確認を参照する。

実機では次の順に確認する。

試験用配布物の `sd-test/nes/titles.csv` は、直前に退避したNES一覧の表示名と順序を保ち、ドクター・マリオの1行だけ `1:1:2`（CRT ON、H BLUR WEAK、SCANLINE STANDARD）を付けた確認用データである。公式のゲーム別推奨値ではない。他の行は継承とする。実機へ置く前に現行CSVとROMの検査値を照合し、元のCSVを退避する。

1. 起動・映像・音声・操作、日本語一覧とCSV順序、OSD位置・排他・入力遮断・解放待ちを確認する。
2. 設定変更でUNSAVED、Close後の再openでSAVEDとなり、同ゲーム再起動・電源再投入後にも復元することを確認する。別ROMへ誤適用しないことも確認する。
3. 既存2列CSVで安全な既定値を使うこと、試験用の3列CSVで推奨値を読み、保存済み個別値がそれより優先することを確認する。
4. ResetとCloseで推奨値へ戻り、再起動でも推奨値を使うこと、推奨値を更新した後には新しい値へ追従することを確認する。
5. 保存失敗・破損の実機評価は、退避・復旧手順を伴う別試験として扱う。PC上の故障模擬試験だけで物理的電源断耐性を確認済みにしない。

未確認事項は実機での保存時間・再起動後の復元・SD機器固有の動作、他coreのstorage排他と能力差、圧縮ROMの識別方式である。controller profileの登録・VID:PID転送はこの保存機能へ混在させない。
