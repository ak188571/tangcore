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

## 第5g版の実機反映

2026-11-04T17:29:12.286390+09:00、既知Console138KへFW8faebdeのみを反映した。基板SHA、新FW全byte、4MiB全flash読戻しと更新範囲外を照合した。SD全63fileは新たな退避時および第5f最終退避と同一で、4保存record/CSV/ROM/font/logを維持した。defaults fileはまだ置いていない。初回mode0 READの接続確立に失敗し、再programせずmode2 READで成功した。SDK設定を元のbyteへ戻した。

復旧用は直前の実機合格第5fの検証済み全読戻しをコピーしたもので、新たな書込み前flash読取りを行ったとはしない。verification/crt-stage5g-defaults/deployment.jsonに記録。まず値変更/Reset/SAVEなしで通常起動と任意defaults file未設定時の従来動作を確認する。defaultsの実機試験は未確認。

## defaults未設定での初回起動の実機結果

2026年11月4日、利用者が初回3項目を「1-3正常」と回答した。日本語NES一覧と順序、Dr. Mario/Pac-Manの起動・映像・音声・操作、CRT DEFAULTS - STAGE5GとDEFAULTS MISSING、Dr. MarioのROM ID 7623dffd・CSV ON/WEAK/STANDARD、Pac-ManのROM ID ebbb19bf・builtin全OFF、両方のSTORE RESET・SAVE SAVED・FRAME ACKを確認した。OSD1からの一覧復帰も正常だった。

defaults fileがない場合の既存動作とReset記録保持を実機確認した段階であり、system/global defaults自体の実機合格とはしない。次はSDを新たに退避し、system.tsv fixtureをcrt/defaults.tsvへ新規追加して、CSV優先とsystem適用を確認する。追加firmware書込みは不要。

## system defaults試験ファイルの追加

初回起動の正常報告後、同じTANGCONSOLE microSDの63ファイルを新たに退避し、導入前と全内容・全属性が一致することを照合した。4個の保存記録のCRC・ROM識別情報・世代・kind・値も確認した。既存defaults.tsvがないことを確認し、試験用system.tsvをcrt/defaults.tsvへ新規作成した。追加後は64ファイルを照合し、元の63ファイル、CSV、保存記録、属性は不変だった。firmwareの追加書込みは行っていない。

試験値はglobal 1:1:3、NES 1:2:1であり、画質推奨を確定したものではない。Dr. MarioのCSV ON/WEAK/STANDARD優先と、Pac-ManのSYSTEM ON/STANDARD/WEAK適用は、これから実機確認する。両ゲームは既存Reset記録のままとする。試験完了後、この新規試験ファイルだけを保全して取り外す。PC照合の根拠はverification/crt-stage5g-defaults/system-fixture-installation.jsonに記録した。

## system適用・CSV優先の実機結果

利用者はsystem試験ファイル追加後の3項目を「1-3正常」と回答した。日本語NES一覧と順序、両ゲームの起動・映像・音声・操作は正常だった。Dr. MarioはCSVのON/WEAK/STANDARD・INITIAL CSVを保持し、Pac-ManはNES用defaultsのON/STANDARD/WEAK・INITIAL SYSTEMとなった。両方のSTORE RESET・SAVE SAVED・DEFAULTS OK・FRAME ACKとROM IDを確認した。これにより、system defaultsの適用とCSV優先を実機確認した。

利用者の指定により、以後の確認手順で画面項目を列挙する際はOSDの上からの表示順に揃える。現在の順序は、見出し、SAVE状態、INITIAL、CRT ENABLE、H BLUR、SCANLINE、STORE、APPLY、ROM ID、SAVE操作行、RESET TO RECOMMENDED、DEFAULTS、POSである。OSD自体の項目順は変更しない。次は手動保存値の優先、ResetのX/Y取消し、および追加行を含む表示・入力を確認する。

## USER優先・Reset取消し・OSDの実機結果

利用者は続く4項目を「1-4正常」と回答した。Pac-ManでON/STRONG/STANDARDを手動SAVEし、OSDが開いたままSAVEDとなり、一覧からの起動し直し後もINITIAL USER・STORE USER・保存値・FRAME ACKを確認した。Resetのpreviewはsystem推奨ON/STANDARD/WEAKとなり、保存せずXまたはYで閉じると手動保存値へ戻った。これにより、USERのsystem defaultsへの優先とResetの両終了buttonによる取消しを実機確認した。

追加DEFAULTS行を含む5位置で文字欠けがないこと、OSD1との排他と中央表示、ゲームへの入力遮断、全button解放待ちも正常だった。保存記録の世代・CRCと他ファイルの不変は次のPC照合で確認する。global継承や不正defaultsの試験はまだ完了していない。

## system試験後のPC照合とglobal継承試験の準備

microSDの64ファイルを新たに退避した。変更はPac-Manの保存slot bだけで、第4世代・USER・ON/STRONG/STANDARD、ROM識別情報とCRCが正常だった。他の63ファイルと全属性は不変で、defaults.tsvもfirmwareによって変更されていなかった。1回のSAVEによる1世代の更新と、ResetをX/Yで取り消した際に保存が行われないことをPC側でも確認した。

退避したsystem試験ファイルのSHAを確認し、今回追加したcrt/defaults.tsvだけをglobal.tsvへ切り替えた。global値は1:1:3、NES欄は空である。差替え後も全64ファイルを照合し、他の63ファイル・保存値・CSV・全属性は不変だった。firmwareの追加書込みは行っていない。次はUSER優先の継続、Reset previewのglobal継承、SAVE後の再起動・電源再投入での追従、CSV優先の継続を実機確認する。globalの実機合格はまだ記録しない。

## global継承・USER優先・Reset保存後の実機結果

利用者はglobal試験の4項目を「1-4正常」と回答した。Pac-Manは変更したdefaultsよりUSER保存値ON/STRONG/STANDARDを優先した。Reset previewでは空のNES欄からglobal値ON/WEAK/STRONGを継承し、SAVEを1回行うとOSDが開いたままSAVEDとなった。一覧からの起動し直しと通常の電源再投入後も、SAVE SAVED・INITIAL GLOBAL・ON/WEAK/STRONG・STORE RESET・FRAME ACK・ROM ID ebbb19bf・DEFAULTS OKを確認した。

Dr. MarioはSAVE SAVED・INITIAL CSV・ON/WEAK/STANDARD・STORE RESET・FRAME ACK・ROM ID 7623dffd・DEFAULTS OKを保持した。日本語一覧と順序、両ゲームの映像・音声・操作も正常だった。global継承と優先順位、Reset保存後の追従は実機確認済みとする。新しい保存記録の世代・CRCと他ファイルの不変は、次のPC照合で確認する。不正defaultsファイルと最終復帰の試験は未完了である。
