# 第5g段階：system/global defaults

## 基準と範囲

実機確認済み第5f（crt-stage5f-hw-20261104、親672a61d、FWe82e5ea）からdefaults読込みだけを追加する。基準branch tangcore-integratedの履歴を維持し、親crt-osd2-stage1、FW crt-stage5g-defaults-20261104で作業する。FW commit 8faebdeca1a24a1e14c9c8100e2b1c0e3e56f381。JTAG、FPGA、ROM loader、保存writerとrecord reader、日本語メニュー・titles.csv順序、OSD1・入力遮断/解放待ちは変更しない。

## 設定の解決

保存user値 ＞ 選択時のtitles.csv推奨値 ＞ system defaults ＞ global defaults ＞ builtin全OFF。3項目を一組として採用し、項目ごとの部分上書きはしない。明示0:0:0も有効な値で、空欄とは異なる。

最新recordがResetのtombstone(kind1)ならuser overrideを採用せず、起動時に解決した推奨値を使う。Resetボタンも同じ起動時snapshotをpreviewする。SAVEで推奨値への追従モードを確定、X/Yで未保存の値と意図を取り消す第5fの動作を維持する。defaultsやCSVをゲーム実行中に再読取りせず、次回のゲーム起動から変更を反映する。

## defaults.tsvの形式

ROMと同じvolumeの `/crt/defaults.tsv` を任意で置く。sd:/ とusb:/は分離し、反対のvolumeを探さない。firmwareからこのfileを作成・編集しない。UTF-8、TAB区切り、最大4096byte（BOM/改行を含む）。BOMとCRLF/LF、終端改行なしを受理する。

```text
system<TAB>crt_v1
*<TAB>1:1:3
nes<TAB>1:2:1
```

<TAB>は実際のTABへ置き換える。crt_v1はenable:blur:scanlineで、enable0/1、blur/scanline0〜3（OFF/WEAK/STANDARD/STRONG）。上の値は試験例で、公式の画質推奨値ではない。

system keyはnes/snes/gba/genesis/sms/pc、globalは*。現在のcore ID1〜6との対応をcore/cores.cppで照合した。対応するsystem行の値が非空なら優先し、空欄または行なしならglobal、globalも空欄/行なしならbuiltin全OFFへ進む。headerのみも有効でbuiltinを使う。header後の完全な空行は許容するが、comment行や余分な空白は許可しない。

未知header/column/key、重複key（空欄でも重複不可）、値範囲外、途中で不正な行があればfile全体を不採用にする。現在選択していないsystem行の不正も無視しない。正常な行だけの部分採用はしない。fileがない場合は正常な任意file未設定として扱う。I/O/close失敗、size不一致、4096byte超過も採用しない。失敗だけを理由にゲーム起動を止めず、上位のCSV/userを維持し、下位推奨値がなければbuiltinへ戻る。

## 読取りと資源

JTAG/core ID/能力確認・ROM ID・保存record読取りの後、既存ROM loaderの前にmain taskで順次読む。既存noncacheable fcoreと64byte整列fbuf（8192byte）を使い、新しいFILや大きいtext bufferをstackへ置かない。f_sizeを4096までに制限し最大4097byteを1回読取り、読取byte数との一致を確認してcloseを試みる。parserはstring_viewと固定配列を使い、推奨値だけをコピーしてbufferをloaderへ返す。snapshotへstring_viewを残さない。

ROM ID取得が失敗してもROM pathからvolumeが分かればdefaultsを読める。保存は従来どおり有効IDが必須でNES-onlyの資源guardを維持する。他core/別taskとの並行storage動作を新たに検証済みとはしない。

## OSD2

識別はCRT DEFAULTS - STAGE5G。INITIALはUSER/CSV/SYSTEM/GLOBAL/DEFAULTで起動時sourceを示す。SAVE/STORE/APPLY/ROM ID、SAVEとReset行は維持する。DEFAULTS行を1行追加し、MISSING/OK/BAD FILE/READ ERROR/UNAVAILABLEを表示する。不正なdefaultsがあっても上位CSV/userが適用される場合があり、sourceとfile状態を別に確認できる。

DEFAULTS OKでも対象行とglobalが空ならINITIAL DEFAULTとなる。SAVE SAVEDは数値の保存状態または確定済みReset状態であり、defaults file自体へ書き込んだ意味ではない。1行増えるためPOS5位置の文字欠けを実機確認する。

## PC試験とbuild

関連11本（crt_defaults、crt_save、crt_restore、rom_id、crt、osd、launch、titles、folders、scroll、wrap）とfirmware buildが成功。実readerをfake FatFsで動かし、全key、system/global、空欄・明示OFF、BOM/CRLF、size4096境界、不正/未知/重複の原子的拒否、volume分離、read-only buffer、open/read/close失敗とsize不一致を確認した。UI実sourceでUSER/CSV/SYSTEM/GLOBAL/builtinの優先、Resetによる推奨snapshot使用と変更後defaultsへの追従、無効defaultsでも上位値を維持することを確認。main実adapterで順序、handoff、load失敗時のclear、対応core以外で追加アクセスしないことを確認した。

firmware 227792bytes、SHA256 27c8107c0dca076d3dfce8f2f2fea7008137cc9c6771387060ee4dd7c4286b5f。parser自身のstack frameは240byte、readerは48byteで、下位呼出深さ全体ではない。記録はverification/crt-stage5g-defaults。FPGA buildは行わず実機確認済みNES imageを再利用する。

## 実機試験計画

直前の第5f全flash照合済みsnapshot、SD63file、現在の4recordを保全する。初回導入はfirmwareのみで、defaults fileをまだ置かない。

1. 日本語一覧/順序・2本の映像音声操作、旧Reset記録の保持、Dr. MarioのCSV ON/WEAK/STANDARDとPac-ManのbuiltinOFF、DEFAULTS MISSING・FRAME ACKを確認する。
2. fresh SD退避後、system.tsv fixtureをcrt/defaults.tsvへ新規追加。Dr. MarioはCSV優先のまま、Pac-ManはSYSTEM ON/STANDARD/WEAKとなることを確認。Pac-Manで手動user値ON/STRONG/STANDARDをSAVEし、defaultsより優先することと、Reset previewがsystem値を使いX/Yでuser値へ取消せることを確認する。
3. defaults fileをglobal.tsv（nes空欄）へ替える。user値優先のまま、Reset previewと確定後の再launch/電源再投入でGLOBAL ON/WEAK/STRONGへ従うことを確認する。
4. invalid.tsvは非選択snes行が不正なfixture。file全体が不採用となり、Dr. MarioはCSVを維持、Pac-ManはbuiltinOFF、DEFAULTS BAD FILEとなることを確認する。user保存の優先とResetの上位CSV使用も確認する。
5. POS5位置・OSD1排他・入力遮断/解放待ち、再launch時のsnapshot更新を確認。最後に全SDを新たに退避し、record CRC/key/size/kind/generationと他file不変を照合する。試験用defaults fileは退避して取り外し、元のCSVと原属性を維持する。試験中に作ったuser overrideはResetで推奨追従へ戻して記録する。最終状態で2本の通常起動と推奨値復帰を確認する。

既存defaults fileがあれば上書きせず保全して調査する。file/I/O失敗や他volumeのhost試験成功を実機合格へ読み替えない。現時点で実機は未確認。第5gおよび第5段階全体の完了は必要な実機結果・最終SD復帰照合後に判定する。
