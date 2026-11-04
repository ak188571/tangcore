# 第5e段階：ゲーム別設定の明示的な保存

## 基準と範囲

実機確認済み第5d（crt-stage5d-hw-20261104、親daa79d2、FW42359d6）を基に保存だけを追加する。基準branch tangcore-integratedの履歴を維持し、親crt-osd2-stage1、FW crt-stage5e-save-20261104で作業する。FW commit 0051516f442552b68677adec064a8a0c62daea61。Reset UI、tombstone作成、system/global defaultsは別段階であり、追加しない。JTAG、FPGA、ROM loader、CSVの日本語表示と順序を変更しない。

当初のsave-on-close実装commit875dd11は未導入の経過として残す。2026年11月4日の利用者の指定により、正式な操作は以下の明示SAVEとX/Y破棄へ変更した。OSD終了時の自動保存は行わない。

## OSD2の操作と値

- 起動時は第5dと同じく、有効な保存user値 ＞ 選択時CSV推奨値 ＞ builtin全OFF。
- 調整は実映像へ即時に反映するpreview。変更後はSAVE: UNSAVED。
- 従来のCLOSE行をSAVEへ変更する。A/BでSAVEを選ぶと現在の3値を保存し、OSD2は開いたまま。成功後はSAVE: SAVED、失敗時はSAVE: FAILED。再度SAVEで再試行できる。
- X/YだけでOSD2を閉じる。保存処理は呼ばず、最後に保存成功した値まで未保存の変更を戻し、FPGAにも戻した設定を再送する。まだ保存成功がない場合は、起動時の保存読取り値・CSV値・builtin値へ戻す。反映は既存のframe境界で行う。
- 保存成功後さらに調整してX/Yを押した場合は、直前の保存成功値へ戻す。初期値へ一律に戻す処理ではない。確認dialogを追加しない。
- CSV値と同じ値でも、初回SAVEの明示操作はuser overrideとして記録する。すでに保存済みで値が同一なら追加書込みはしない。調整やPOS移動だけでは書き込まない。

識別はCRT SAVE - STAGE5E。SAVE: RECOMMENDEDはまだuser保存せず起動基準の値であること、SAVEDは読取り済みまたは保存確認済み、UNSAVEDはpreviewとの差、FAILEDは直近SAVE失敗を示す。INITIALとSTOREは起動時のsource/読取り結果であり、SAVE後も起動時の記録を維持する。APPLY: FRAME ACKは映像への適用確認であり、保存成功とは別である。SAVE行にX/Y: CANCELを併記する。OSD1の操作、POS5位置、入力遮断・解放待ちは維持する。

## file形式と保存手順

第5dで実機確認した同volumeの `/crt/SS-CCCCCCCC-ZZZZZZZZZZZZZZZZ.a/.b`、32byte CRT1/schema1形式を使う。保存keyはsystem ID・ROM全byte CRC32/IEEE・64bit size、volumeはdirectoryで分離する。recordはkind0のuser overrideだけを作る。全OFFも明示的な保存値となる。推奨値と同じ値でもtombstoneへ変換しない。

1. 毎回、両slotを第5dと同じ検証で読み直す。失敗した前回SAVEが有効な世代を残した場合もそれを保護する。
2. I/O失敗、未知schema、世代競合、無効IDなら保存せずFAILEDとする。
3. 有効な最新slotの反対側へgeneration+1を用意する。有効slotがなければa・generation1とする。wrap比較、破損片側からの復帰は第5dと同じ。
4. crt directoryを作成または存在確認し、対象slotをFA_WRITE|FA_CREATE_ALWAYSでopenする。現在の有効なslotは上書きしない。
5. 既存の整列noncacheable bufferから32byteを全量書込み、f_sync、f_closeを成功確認する。
6. 対象をFA_READで再openし、size32・全32byte一致・close成功まで確認してから成功とする。

どこかで失敗した場合はRAMの保存成功値を更新せずOSDを開いたままにする。SAVE再試行は両slotを再読取りする。同期/close/確認で失敗してもSDに完全な新recordが残る場合があり、再起動の読取り結果は有効recordの世代比較に従う。X/YはRAMと映像previewを破棄する操作であり、失敗した書込みをSD上で巻き戻す処理ではない。試験中にSDを抜いて失敗を起こさない。

## 所有と実装範囲

UI16の同一main taskから同期的に実行する。既存fcore/fbufを一時的に専有し、大きいFILやbufferを追加stackへ置かない。main callbackはcore_running・active_core NES・CRT対応・identity.system NESを確認する。他coreはbackgroundのdisk処理など所有関係を未検証のため、保存を許可しない。現時点の対象はConsole138K/NES。SAVE中も入力の所有はOSD2のままで、ISR側の設定ACK処理は維持する。

## PC試験とbuild

関連10本（crt_save、crt_restore、rom_id、crt、osd、launch、titles、folders、scroll、wrap）が成功。writerの実sourceをfake FatFsで試験し、交互slot、generation wrap、明示OFF、短い/途中書込み、mkdir/open/write/sync/close/確認失敗、失敗後の再試行、有効世代の保護、破損slotの復帰、I/O/未知schema/競合時の上書き拒否を確認した。UI実sourceではSAVE後に開いたまま・再試行・同値の重複書込み抑止・初回の推奨値保存、XとYの両方で書込みせず実際のconfigを戻すことを確認した。main callbackのNES以外の拒否も試験した。

firmwareは226192bytes、SHA256 e7534a59b1cb5837eddf3f8ff34893e560c9a267ae841da63a41ebdc3aa6e223。writer自身のstack frameは208bytesで、下位reader/FatFs/driverを含む全深さではない。初回host shimのenum警告は修正済み。実機試験とPC試験を区別する。新FPGA buildはなく、NES imageは第4b以来の確認済み版を再利用する。

## 実機試験の順序

導入前にSD全fileを新たに退避・照合し、直前の第5d全flash照合済みsnapshotを保全する。最初の導入はfirmwareだけとし、CSV/ROM/NES/font/既存logに触れない。

1. 日本語一覧・順序・2本の起動/映像/音声/操作、初期CSV/defaultとROM ID、FRAME ACKを確認する。初回はSAVE RECOMMENDED、STORE MISSING。
2. Dr. Marioのpreviewを変更し、SAVEせずX/Yで閉じる。再表示で起動基準へ戻り、別gameも初期値のままであることを確認する。
3. Dr. MarioをON/STRONG/STRONGへ変更し、SAVEを選ぶ。OSDが開いたままSAVE SAVED、FRAME ACKになる。さらに別の値へ変更してX/Yで破棄し、保存値へ戻ることを確認する。
4. 一覧から再起動・通常の電源再投入で保存値が復元され、別gameとは分離することを確認する。別gameでも異なる値と明示全OFFを保存する。
5. 複数回SAVEでa/bの2世代が作られ、変えずにSAVEしてもfileが増えないことをPCで確認する。全SDを再退避し、recordのCRC・ROM ID・size・世代・値、元のROM/CSV/NES/font/log不変を照合する。
6. 保存失敗は、PC退避後に試験対象recordのread-only属性を設定して起こす。再起動して新しい値のSAVEを試し、FAILEDでもOSDが消えず、X/Yで最後の保存確認値へ戻して終了できることを確認する。SD抜去や書込み中の電源断は行わない。属性を戻して再試験する。
7. POS5位置・OSD1排他・入力遮断・全button解放待ちも確認する。保存fileを残すか試験用として退避するかは実機結果を整理して記録する。

現時点で実機は未確認。実機合格tagは依頼した試験の完了後に作る。Reset UI/defaultsと第5段階全体は未完了。

## 第5e版の実機反映

2026-11-04T11:40:59.086709+09:00、既知Console138KへFW0051516のみを反映した。基板SHA、新FW全byte、4MiB全flash読戻しと更新範囲外を照合した。SD全59fileは退避時と同一で、保存recordの追加はまだない。初回mode0 READの接続確立に失敗し、再programせずmode2 READで成功した。SDK設定を元のbyteへ戻した。

復旧用は直前の実機合格第5dの検証済み全読戻しをコピーしたもので、新たな書込み前flash読取りを行ったとはしない。verification/crt-stage5e-save/deployment.jsonに記録。通常起動、明示SAVE、X/Y破棄、再起動時復元、保存失敗は利用者の実機確認待ち。

## 初回起動の実機結果

2026年11月4日、利用者が初回3項目を「1-3正常」と回答した。日本語NES一覧と順序、Dr. Mario/Pac-Manの起動・映像・音声・操作、STAGE5EとSAVE行、Dr. MarioのROM ID 7623dffd・CSV ON/WEAK/STANDARD、Pac-ManのROM ID ebbb19bf・DEFAULT全OFF、両方のSAVE RECOMMENDED・STORE MISSING・FRAME ACKが正常だった。X/Yで閉じてOSD1から一覧へ戻る経路も確認した。

今回は値変更やSAVEを依頼していないため、保存および未保存previewの破棄を確認済みとはしない。続いて現在の版で、保存前のX破棄、明示SAVEのstay-openとSAVED表示、保存後の追加調整をYで破棄、再launch時復元と別ゲームへの分離を確認する。追加firmware書込みは不要。

## 明示SAVEとX/Y破棄・再launchの実機結果

2026年11月4日、利用者が次の3項目を「1-3正常」と回答した。Dr. MarioでSAVEせずXで閉じるとpreviewがCSV ON/WEAK/STANDARDへ戻り、再表示でSAVE RECOMMENDED・FRAME ACKとなった。ON/STRONG/STRONGをSAVEするとOSD2を開いたままSAVE SAVED・FRAME ACKになり、その後の調整をSAVEせずYで閉じると、映像と表示値が保存成功値ON/STRONG/STRONGへ戻った。

一覧からDr. Marioを起動し直すと保存値が復元され、INITIAL USER・STORE USER・SAVE SAVED・FRAME ACKを確認した。別のPac-Manは全OFF・INITIAL DEFAULT・STORE MISSING・SAVE RECOMMENDED・FRAME ACKのままで、ゲーム間の分離も正常だった。

電源再投入後の復元、複数回のSAVEと明示全OFF、OSD操作の回帰、保存recordと他SDファイルのPC照合、保存失敗と属性復帰の実機試験は未完了。現在のSDには実機SAVEで作られたDr. Marioのrecordがあるが、世代・CRCの実byte照合はまだ行っていない。

## 電源再投入・複数SAVE・全OFF保存とOSDの実機結果

2026年11月4日、利用者が次の4項目を「1-4正常」と回答した。通常電源再投入後にDr. MarioのON/STRONG/STRONG・USER/SAVED/FRAME ACKが復元され、映像・音声・操作も正常だった。その後ON/STANDARD/WEAKをSAVEし、同値での再SAVEと一覧からの再launchも正常だった。

Pac-ManではON/WEAK/STANDARDをSAVEして再launchで復元し、続いて明示的に3項目全OFFをSAVE・再launchして、全OFF・INITIAL USER・STORE USER・SAVE SAVED・FRAME ACKを確認した。Dr. MarioのON/STANDARD/WEAKは別ゲームの保存で変わらなかった。POS5位置で文字欠けなし、OSD1との排他・中央表示、入力遮断とX/Y保持・全button解放後の復帰も正常だった。

現在の最終保存値はDr. Mario ON/STANDARD/WEAK、Pac-Man全OFF。recordの世代数や同値SAVEでの書込み抑止はPCで実byteを照合するまで確認済みとしない。残りはSD全fileの新たな退避、recordのCRC/key/size/generation/value照合と無関係file不変確認、およびread-only属性による保存失敗・再試行・X/Y破棄と属性復帰後の保存回復である。

## 保存recordのPC照合：値の確認待ち

2026年11月4日、同じ物理identityのmicroSD全63fileを新しい退避先へコピー・SHA照合した。元の59fileはすべて導入前と同一で、追加は2本のROMのa/bの計4recordのみだった。全recordはsize32、magic/schema/system/kind/reserved、ROM CRC/size、record CRCが正常だった。

ただし操作手順から予想した世代・値と一致しなかった。Dr. Marioのaはgeneration3・ON/STRONG/STRONG、bはgeneration4・ON/WEAK/STANDARDだった。Pac-Manのaはgeneration1・ON/STANDARD/WEAK、bはgeneration2・全OFFだった。最新のDr. Mario値は依頼したON/STANDARD/WEAKと異なる。追加操作の結果か、表示・保存の不一致かはまだ判定しない。同値SAVEによる世代増加がないことも、この実機記録からは確認済みとしない。

退避後に保存内容を編集・修復したり、read-only属性を設定したりしていない。利用者へ最後の保存値と追加操作の有無を確認中。記録はverification/crt-stage5e-save/record-audit-pending-clarification.json。これまでの「正常」は利用者の各報告を記録したものであり、このPC実byteの差異を解消済みとするものではない。

## 追加操作の確認とread-only試験準備

利用者が「PCで読んだ値になるよう追加・変更して保存した」と回答した。前節の手順上の予想値との差異は追加SAVEの結果として確認できた。保存内容を編集・修復せず、そのまま試験基準にする。Dr. Marioの最新値はgeneration4・ON/WEAK/STANDARD、Pac-Manの最新値はgeneration2・全OFF。4recordのCRC/key/size/schema/kind/reserved、世代と値、元59file不変をPCで確認した。追加SAVEがあるため、このsnapshotだけで同値SAVEの世代抑止を証明済みとはしない。

2026-11-04T12:09:28.525863+09:00、退避と全file再照合後、Dr. Marioのa/bの2fileだけを一時的にread-only属性へ変更した。元の全file属性をprivate sessionへ記録し、全63fileの内容および他fileの属性は同一と確認した。firmware・CSV・ROM・Pac-Man recordは変更していない。記録はrecord-inspection.jsonとread-only-protection.json。前節の確認待ちはこの回答で解消した経過として残す。

次は通常起動し、Dr. Marioの基準ON/WEAK/STANDARDから異なる値をSAVEしてFAILEDとなりOSDが消えないこと、再SAVEでもFAILED、X/Yで基準値へ戻せることを確認する。その後SDをPCへ戻して全fileを新たに退避・照合し、元の属性へ戻す。失敗試験・属性復帰・保存回復はまだ確認待ち。

## read-only属性による保存失敗の実機結果

2026年11月4日、利用者が保存失敗試験の3項目を「1-3正常」と回答した。Dr. Marioの基準ON/WEAK/STANDARD・USER/SAVED/FRAME ACKは正常に読めた。ON/STRONG/STRONGへ変更してSAVEするとOSD2が開いたままSAVE FAILEDとなり、再SAVEもFAILEDだった。Xで閉じると映像と値が基準へ戻り、開き直しでSAVE SAVED・FRAME ACKを確認した。

同じ変更・失敗後にYでも基準へ戻せ、一覧からの再launchでも保存値ON/WEAK/STANDARDとUSER/SAVED/FRAME ACK、映像・音声・操作が正常だった。これによりread-onlyによる書込み拒否時のstay-open、再試行、X/Y破棄を実機で確認した。sync/close失敗や書込み中の電源断を実機試験したことにはしない。

残りは試験後SD全63fileの新たな退避・不変照合、元属性への復帰とその後の保存成功/復元確認、制御した同値SAVEで世代が進まないことのPC確認。Dr. Marioの2fileはまだread-onlyのままであり、保存回復を確認済みとはしない。

## 保存失敗試験後のSD照合と属性復帰

2026-11-04T12:33:14.724067+09:00、同じ物理identityのF:から全63fileを新たに退避・SHA照合した。全file内容は保存失敗試験前と同一で、2世代のrecordは破壊されていなかった。全fileの属性も試験準備時と一致していた。

2026-11-04T12:33:48.423107+09:00、Dr. Marioのa/bだけを記録済みの元属性へ戻し、全63fileの内容と全fileの元属性が一致することを確認した。firmware、ROM、CSV、Pac-Man recordに変更はない。post-failure-sd-verification.jsonに記録。現在の保存値はDr. Mario ON/WEAK/STANDARD（generation4）、Pac-Man全OFF（generation2）のまま。

残りは属性復帰後のSAVE成功・再launch/電源再投入での復元、および同値SAVEで世代が進まないことのPC照合。制御した1回の変更SAVE（ON/STRONG/WEAK）と同値SAVEのみを行い、その後最新generation5であることを確認する予定で、まだ実施済みではない。
