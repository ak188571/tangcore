# 第5f段階：Reset to Recommended

## 基準と範囲

実機確認済み第5e（crt-stage5e-hw-20261104、親7c34d16、FW0051516）からResetだけを追加する。基準branch tangcore-integratedの履歴を維持し、親crt-osd2-stage1、FW crt-stage5f-reset-20261104で作業する。FW commit e82e5ea61d318b9511bf5ed76e2e8cc790458cdf。system/global defaultsは今回も実装しない。JTAG、FPGA、ROM loader、日本語メニューとtitles.csv順序、OSD1、入力遮断・全解放待ちは変更しない。

## 正式操作

OSD2のSAVE行の次にRESET TO RECOMMENDEDを追加する。Resetの決定操作はA/B。対象は起動時にコピーした同folderのtitles.csv推奨値で、有効なCSV値がなければbuiltin全OFF。既存のuser保存値を推奨値として扱わない。CSVはゲーム起動中に読み直さない。

Resetを選ぶと推奨値を映像へプレビューし、OSDは開いたまま。まだSDには書き込まない。明示SAVEで確定し、X/Yは未保存の値とResetの意図の両方を取り消す。取り消す際は最後の保存成功値または起動時の値へ、FPGA設定も戻す。SAVE後は開いたままSAVE SAVED、失敗時はFAILED。Reset後にさらに手動調整した場合はResetの意図を解除し、通常のuser overrideとしてSAVEする。

数値が現在のuser保存値と推奨値で偶然同じでも、Resetは将来のCSV追従を回復するための変更なのでUNSAVEDになる。同じ数値のuser overrideを残したまま成功扱いにはしない。すでにResetを確定済みで値と意図が同じなら再SAVEで追加世代を作らない。単に手動操作で推奨値と同じ数値に合わせただけではReset扱いにせず、通常のuser値として保存する。

## tombstoneの保存と復元

第5dで読取り済み、第5eで書込みを確認した同じ32byte CRT1/schema1・a/b形式を使う。ResetのSAVEはkind1、設定byte20は常に0。推奨値の数値をrecordへ固定しない。key、record CRC、世代比較、最新有効slotの反対側への書込み、write/sync/close/全byte読戻し、毎回の再読取りとretry保護は第5eの手順を維持する。

次回起動で最新有効recordがkind1なら、古いkind0を復活させず、その起動時に解決したCSV推奨値またはbuiltin全OFFへ従う。したがって、後からCSV推奨値が変われば新しい値を使う。recordの削除や両slotの一括上書きは行わない。

失敗したSAVEが完全な新recordを残す可能性は第5eと同じである。FAILEDでもRAMの保存成功基準は更新せず、X/YではRAM/映像のpreviewを戻す。SD上の失敗した書込みを巻き戻したと主張しない。再SAVEでは両slotを読み直して有効な世代を保護する。

## OSD表示

識別はCRT RESET - STAGE5F。設定3項目・SAVE・RESET TO RECOMMENDED・POSを表示するため、縦方向に1行増える。5位置で文字欠けを実機確認する。

SAVEはRECOMMENDED/UNSAVED/SAVED/FAILED。Resetの確定後もSAVEDとし、未保存previewとの差は値とResetの意図の両方で判定する。INITIALとSTOREは起動時の記録であり、Reset操作直後に書き換えない。次回起動ではtombstoneを読んでSTORE RESET、INITIAL CSVまたはDEFAULT、SAVE SAVEDとなる。APPLY FRAME ACKは映像の適用確認であり、保存成功とは独立する。

## 実装とPC試験

変更はUIのReset preview状態、保存callbackのreset引数、writerのkind1/value0作成に限定する。読取りparser、slot選択、CSV parser、OSD input loopは変更しない。既存noncacheable fcore/fbufを順に使い、main callbackのNES-only資源所有条件を維持する。他coreへ保存対象を拡張しない。

関連10本（crt_save、crt_restore、rom_id、crt、osd、launch、titles、folders、scroll、wrap）とfirmware buildが成功。Reset previewが書き込まないこと、X/Yの両方で値と意図を戻すこと、同値user値でもtombstoneを作ること、Resetの重複SAVEをしないこと、Reset後の手動調整を通常保存すること、CSV変更追従、CSVなし全OFF、Reset保存失敗・全write/verify fault・途中slot破損からの復帰・retry時の世代保護を確認した。最初の追加試験は片側破損時の期待状態をUSERと誤記しており、既存仕様のRECOVEREDへ修正した。sourceの保存処理変更は不要だった。

firmwareは226528bytes、SHA256 44f6322c9dafb91ff8c2d622f459da85638b6ed2a438a962ac2b83b7f8aa0f3b。writer自身のstack frameは224bytesで、reader/FatFs/driverを含む全深さではない。記録はverification/crt-stage5f-reset。新FPGA buildはなく、NES imageは実機確認済みの版を再利用する。

## 実機試験の計画

導入前にSD全体を新たに退避し、実機確認済み第5e全flash snapshotと現在の保存recordを保全する。最初はfirmwareだけを更新し、SDは変更しない。現在の基準はDr. Mario user ON/STRONG/WEAK（最新generation5）、Pac-Man user全OFF（最新generation2）。

1. 初回はReset/SAVEをせず、日本語一覧と順序、2本の起動/映像/音声/操作、旧保存値とID・USER/SAVED/FRAME ACK、Reset行表示を確認する。
2. Dr. MarioでResetをプレビューし、CSV ON/WEAK/STANDARD・UNSAVED・FRAME ACKを確認。SAVEせずX/Yで元のuser値へ戻り、再launchでも旧保存値が保たれることを確認する。
3. Reset→SAVEで開いたままSAVED。再launch/通常電源再投入でCSV値・STORE RESET・INITIAL CSV・SAVEDとなる。Pac-Manは数値が元々全OFFでもReset previewでUNSAVED、SAVE後の再起動でSTORE RESET・INITIAL DEFAULTとなることを確認する。
4. PCでfresh SD退避・CRC/key/size/generation/kind1/value0、他file不変を照合する。制御した同値Reset/SAVEの繰返しで余分な世代が増えないことを確認する。
5. 退避後、試験用titles.csvのDr. Mario推奨値だけを一時的に変え、表示名・順序を維持する。tombstoneが新推奨値へ追従することを確認し、元CSVへ戻す。system/global defaultsは使わない。
6. Reset後の手動調整をSAVEしてkind0へ戻り、以降はCSVよりuser値が優先することを確認する。Reset SAVE失敗の実機試験はrecordのread-only属性を使い、FAILED/stay-open/retry/X/Y取消し、元属性への復帰と成功を確認する。SDを抜いて失敗を起こさない。
7. OSD5位置・OSD1排他・入力遮断・全button解放待ちも確認。最後にSD全体と属性をPC照合し、試験用CSVは必ず元に戻す。最終保存値は利用者と試験結果に従って保持する。

現時点で実機は未確認。依頼試験の結果を記録してから完了tagを作る。defaultsと第5段階全体は未完了。

## 第5f版の実機反映

2026-11-04T13:19:56.058197+09:00、既知Console138KへFWe82e5eaのみを反映した。基板SHA、新FW全byte、4MiB全flash読戻しと更新範囲外を照合した。SD全63fileは新たな退避時および第5e最終退避と同一で、既存4record/CSV/ROM/font/logを維持した。初回mode0 READの接続確立に失敗し、再programせずmode2 READで成功した。SDK設定を元のbyteへ戻した。

復旧用は直前の実機合格第5eの検証済み全読戻しをコピーしたもので、新たな書込み前flash読取りを行ったとはしない。verification/crt-stage5f-reset/deployment.jsonに記録。まずReset/SAVEを行わず通常起動と旧user値保持を確認する。Reset機能の実機試験は未確認。

## 初回起動と既存user保存値保持の実機結果

2026年11月4日、利用者が初回3項目を「1-3正常」と回答した。日本語NES一覧と順序、Dr. Mario/Pac-Manの起動・映像・音声・操作、CRT RESET - STAGE5FとRESET TO RECOMMENDED行、Dr. MarioのROM ID 7623dffd・既存user ON/STRONG/WEAK、Pac-ManのROM ID ebbb19bf・既存user全OFF、両方のINITIAL USER・STORE USER・SAVE SAVED・FRAME ACKを確認した。X/Y終了とOSD1からの一覧復帰も正常。

初回はReset/SAVE/値変更を依頼していないため、Reset機能の実機合格には読み替えない。続けて現在の版でpreviewのX/Y取消し、明示SAVEによるReset確定と再launchでのCSV/builtin追従を確認する。追加firmware書込みは不要。

## Resetのプレビュー・取消し・確定と再launchの実機結果

2026年11月4日、利用者が次の3項目を「1-3正常」と回答した。Dr. MarioでResetを選ぶとCSV ON/WEAK/STANDARD・UNSAVED・FRAME ACKをプレビューし、SAVEせずXまたはYで閉じると元のuser ON/STRONG/WEAK・SAVEDへ戻った。

ResetをSAVEで確定してもOSDは開いたままSAVEDとなり、同値SAVE2回も画面上は正常だった。再launchでON/WEAK/STANDARD・INITIAL CSV・STORE RESET・SAVED・FRAME ACKを確認した。Pac-Manは数値が元の全OFFと同じでもResetでUNSAVEDになり、SAVE後の再launchで全OFF・INITIAL DEFAULT・STORE RESET・SAVED・FRAME ACKとなった。

これでResetの取消しと、数値が同じ場合も推奨値へ従う意図を確定する動作を実機確認した。保存recordのkind・CRC・世代や同値SAVEで世代が増えないことは、PCで実byteを照合するまで未確認。次は追加のReset/SAVEなしで、通常電源再投入後の両ゲームの推奨値モード保持と、1行増えたOSDの5位置・入力回帰を確認する。

## Reset確定後の電源再投入とOSDの実機結果

2026年11月4日、利用者が追加2項目を「1-2正常」と回答した。通常電源再投入後も、Dr. MarioはCSV ON/WEAK/STANDARD・INITIAL CSV、Pac-Manはbuiltin全OFF・INITIAL DEFAULTとなり、両方のSTORE RESET・SAVE SAVED・FRAME ACK、映像・音声・操作が正常だった。

POS5位置でSAVE/RESET TO RECOMMENDED/POSを含め文字欠けなし、OSD2中のSELECT＋右によるOSD1重なりや設定変更なし、ゲームへの入力流出なし、X/Y保持中の入力遮断と全解放後の復帰、OSD1中央表示も確認した。

次はSD全体をPCへ新たに退避し、両ゲームの最新recordがkind1/value0であること、CRC/key/size/generationと同値SAVEの世代抑止、他file不変を照合する。その後Dr. MarioのCSV推奨値だけを一時的にON/STANDARD/STRONGへ変更し、tombstoneが新しい推奨値へ追従する試験を行う。表示名・順序を維持し、試験後は元のCSVへ必ず戻す。現時点でこのPC照合とCSV追従試験は未実施である。

## tombstoneのPC照合とCSV追従試験の準備

2026-11-04T16:16:00.301699+09:00、同じ物理identityのSD全63fileを新たに退避・SHA照合した。Dr. Marioはa generation5/kind0/value15を保持し、新しいbがgeneration6/kind1/value0。Pac-Manはb generation2/kind0/value0を保持し、新しいaがgeneration3/kind1/value0だった。全4recordのCRC/magic/schema/system/key/size/kind/reserved/valueを確認した。Reset previewの取消しと確定後の同値SAVE2回では余分な世代が増えていなかった。元59file、古い有効slot、元属性は同一。record-inspection.jsonに記録した。

2026-11-04T16:16:20.422697+09:00、退避済みtitles.csvのDr. Mario crt_v1だけを1:1:2から1:2:3（ON/STANDARD/STRONG）へ変更した。表示名・順序・他row・改行を維持し、他62fileの内容と全属性は同一、tombstoneも同一と照合した。firmware書込みは行っていない。csv-trial-installation.jsonとcsv-followingの元/試験CSVに再現情報を残した。試験後は元のCSVへ戻す。

次はReset/SAVEなしに新しいCSV推奨値へ追従することを実機確認し、その後手動調整をON/STRONG/WEAKへSAVEして新CSVよりuser値を優先することを確認する。このCSV追従とuser再保存、元CSV復帰はまだ未実施。

## 変更後CSVへの追従と手動user保存の実機結果

2026年11月4日、利用者がCSV追従試験の3項目を「1-3正常」と回答した。日本語一覧の表示名・順序とDr. Marioの起動は正常。Reset/SAVEを押さずに、新しいCSV推奨値ON/STANDARD/STRONG・INITIAL CSV・STORE RESET・SAVE SAVED・FRAME ACKへ追従した。

その後Resetを押さず手動でON/STRONG/WEAKへ変更して1回SAVEし、OSDを開いたままSAVEDとなった。一覧から再launchすると、手動値ON/STRONG/WEAK・INITIAL USER・STORE USER・SAVED・FRAME ACKへ復元し、CSVよりuser保存値を優先することを確認した。Pac-Manは全OFF・INITIAL DEFAULT・STORE RESET・SAVED・FRAME ACKを維持し、映像・音声・操作も正常だった。

これにより、Reset確定は推奨数値を固定する処理ではなくCSVへ従うモードを保存すること、Reset後の手動SAVEはuser overrideへ戻ることを実機確認した。現在のSDには試験用CSV1:2:3が残っている。次に全SDを新たに退避・record照合し、必ず元CSV1:1:2へ戻してからReset保存失敗試験を準備する。元CSV復帰・属性試験・回復・最終照合は未実施。

## 手動user再保存のPC照合・元CSV復帰・失敗試験準備

2026-11-04T16:25:19.474567+09:00、CSV追従試験後のSD全63fileを別の退避先へコピー・SHA照合した。Dr. Marioのaだけがgeneration7/kind0/value15（ON/STRONG/WEAK）へ変わり、b generation6/kind1/value0は維持されていた。Pac-Manのa generation3/kind1/value0とb generation2/kind0/value0、試験CSVと他file、全元属性は同一。手動調整後のSAVEがResetではなく通常user保存となることを実byteでも確認した。

2026-11-04T16:25:38.290620+09:00、保全済み元CSVへbyte単位で復帰し、SHA e930b82e2fab555d20935b4150675abd20d13f3552037ded1a8188151b747d1eと照合した。Dr. Mario推奨値は元の1:1:2（ON/WEAK/STANDARD）へ戻った。保存recordと他fileの内容・全属性は同一だった。

2026-11-04T16:26:08.746140+09:00、Dr. Mario a/bの2fileだけへ一時的なread-only属性を追加し、CSV復帰後の全63file内容と他fileの属性が同一と確認した。現在の基準user値ON/STRONG/WEAKを保護した状態である。firmware書込みは行っていない。post-csv-trial-verification.jsonとread-only-protection.jsonに記録した。

次はReset previewで元CSV ON/WEAK/STANDARDへ移り、SAVE FAILED/stay-open/retry、X/Yでuser値とuser意図へ戻せることを実機確認する。試験後はSDを新たに退避・照合し、属性を必ず元へ戻して保存回復を確認する。これらの失敗・属性復帰・回復はまだ未確認。

## Reset保存失敗・再試行・取消しの実機結果

2026年11月4日、利用者がReset保存失敗試験の3項目を「1-3正常」と回答した。read-only状態でもDr. Marioの旧user ON/STRONG/WEAK・USER/SAVED/FRAME ACKは正常に読めた。Resetで元CSV ON/WEAK/STANDARD・UNSAVEDをプレビューし、SAVEするとOSDを開いたままFAILED、再SAVEもFAILEDとなった。

Xで閉じると値と映像が旧user値へ戻り、再表示でSAVED・FRAME ACKを確認した。同じReset/SAVE失敗後にYでも取消しでき、一覧からの再launchでも旧user値とINITIAL USER・STORE USER・SAVED・FRAME ACK、映像・音声・操作が正常だった。Resetの意図も未確定のまま破棄されることを確認した。

失敗の実機確認範囲はread-onlyによる書込み拒否であり、sync/close失敗や途中電源断を実機試験したことにはしない。次はSD全63fileを新たに退避・照合し、Dr. Marioの2fileを元属性へ戻す。その後ResetのSAVEが回復して成功することを確認する。属性復帰・回復・最終SD照合はまだ未実施。

## Reset失敗試験後のSD照合と属性復帰

2026-11-04T16:42:04.385560+09:00、同じ物理identityのmicroSD全63fileを新たに退避・SHA照合した。全file内容はReset保存失敗試験前と同一で、user recordとtombstoneの両世代は保護されていた。全fileの属性も準備した試験状態と一致した。

2026-11-04T16:42:37.392897+09:00、Dr. Marioのa/bだけを記録済み元属性へ戻し、全fileの内容と全元属性が同一であることを確認した。CSVも元のSHA e930b82e2fab555d20935b4150675abd20d13f3552037ded1a8188151b747d1eと一致。firmware書込みや保存record内容の編集は行っていない。post-failure-sd-verification.jsonに記録した。

残りは属性復帰後のReset SAVE成功と再launch/通常電源再投入後の推奨値モード復元、および最終SD照合である。回復試験はDr. MarioのReset確定SAVE1回と、その後の同値SAVE2回に操作を限定し、新しいkind1世代が1つだけ増えることをPCでも確認する予定。

## 属性復帰後のReset保存回復の実機結果

2026年11月4日、利用者が回復試験2項目を「1-2正常」と回答した。Dr. MarioでResetを選んでSAVEを1回押すと、OSDを開いたままSAVE SAVED・FRAME ACKとなった。そのまま同値SAVEを2回行い、Xで閉じて開き直してもCSV ON/WEAK/STANDARDとSAVEDが保たれた。

一覧からの再launchおよび通常電源再投入後も、ON/WEAK/STANDARD・INITIAL CSV・STORE RESET・SAVED・FRAME ACKを復元した。Pac-Manは全OFF・INITIAL DEFAULT・STORE RESET・SAVED・FRAME ACKを維持し、両ゲームの映像・音声・操作も正常だった。

これで依頼した画面・操作の実機確認は全項目正常。残りはSD全体の新たな退避とPC最終照合で、Dr. Marioの新しいtombstoneがgeneration8で同値SAVEによる追加世代がないこと、record CRC/key/size/kind/value、元CSV・全属性・無関係file不変を確認する。第5f完了tagはまだ作らない。

## 第5f段階の完了

2026-11-04T16:53:10.446695+09:00、同じ物理identityのSD全63fileを新たに退避・SHA照合した。Dr. Marioのaはgeneration7/kind0/value15、最新bはgeneration8/kind1/value0。Pac-Manの最新aはgeneration3/kind1/value0、bはgeneration2/kind0/value0だった。全recordのmagic/schema/system/ROM key/size/kind/reserved/value/CRCを確認した。

属性復帰後の変更はDr. Marioのbだけで、回復Reset SAVE1回でgeneration7から8へ進み、同値SAVE2回では余分な世代が増えていなかった。直前の有効slotとPac-Man recordは同一。元の59file・CSV（SHA e930b82e2fab555d20935b4150675abd20d13f3552037ded1a8188151b747d1e）・全元属性も同一だった。Windows system folderは従来どおり対象外であり、全sector一致を主張しない。final-sd-verification.jsonに記録した。

実装・関連10試験・firmware build・導入/全flash照合・依頼した実機試験・tombstoneのPC照合・CSV変更追従と元CSV復帰・手動user再保存・read-only保存失敗と原属性復帰・Reset保存回復・最終SD照合まで完了した。local tag crt-stage5f-hw-20261104を実機確認済み基準として保持する。基板はFWe82e5ea、NES c8df819a。SDの4recordを維持し、Dr. MarioはCSV推奨ON/WEAK/STANDARDへ、Pac-Manはbuiltin全OFFへ従うResetモードで終了した。保存recordの手動編集や削除、firmware再書込みは行っていない。

正式操作はResetでpreview、明示SAVEで推奨値へ従う意図を確定、X/Yで未保存の値と意図を取り消す。旧user値と数値が同じ場合もkind1へ変わり、Reset後の手動調整はkind0へ戻る。本文前半の確認待ちは経過で、本節とhardware-results.jsonが最終状態である。

実機確認範囲は現在のConsole138K/NESと記録済み2本のROM。保存失敗の実機確認はread-onlyによる拒否・再試行・X/Y取消し・属性復帰後の回復で、sync/close/途中書込み・世代競合などはPC試験のみ。system/global defaultsは未実装で第5段階全体は未完了。初版第5段階の起動停止原因も特定済みとはしない。
