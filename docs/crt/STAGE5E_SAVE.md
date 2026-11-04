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
