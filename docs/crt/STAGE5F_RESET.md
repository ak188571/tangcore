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
