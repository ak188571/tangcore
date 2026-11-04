# SNESTang CRT風表示・OSD2：S0調査と最初の実装範囲

作成日：2026年11月4日。対象：Tang Console138K。変更前SNESのS0基本操作は利用者から正常との報告を受けた。CRT/OSD2は未実装・実機未確認。NESの実機結果をSNESの合格根拠にはしない。

## 1. 基準と今回の変更

GitHubから対象5repositoryの`tangcore-integrated`をfetchし、引継ぎ後の更新がないことを確認した。

| repository | 基準commit |
| --- | --- |
| tangcore | `3aacc1d0402d3457602aebe048fb99fc0937be36` |
| firmware-bl616 | `dc5ff3faded02215042ebd4e9cffb7adf480a37d` |
| nestang | `84b73f76e8a08bdcff45c208349955271bb2d2a1` |
| snestang | `f6cfb942f473aea27af84fb0e42290eb5c560839` |
| monitorcore | `e12b253838b45407dc4de99848218e24112b787c` |

作業先は`crt-osd2-20261101`。SNESは空のsubmodule directoryへ既存cloneから独立したcloneを作成し、GitHubの`tangcore-integrated`をtrackingする同名branchへ切り替えた。元の`build-integrated-20261101/snestang`はdetached HEAD・cleanのまま保全した。SNES作業先の`origin`はlocal clone、`github`はGitHubである。親のSNES gitlinkは変更していない。

S0では調査記録と再現build用scriptのみを追加する。RTL・共通firmware・日本語一覧・CSV・NES・monitorを変更しない。SDおよびflashへの書込みはしていない。

## 2. Console138Kの実際のbuild経路

正しい入口は`snestang/build_console138k_usb.tcl console138k ds2`、topは`src/snestang_console138k_usb_top.v`の`snestang_top`、board設定は`src/boards/console138k.v`、deviceは`GW5AST-LV138PG484AC1/I0` revision B。board設定はDS2、USB1、USB2、DSPnを有効化する。`snestang_console138k.gprj`は存在しない。mega138k用projectや通常の`build.tcl`をConsole138K USB版の代用にしない。

既存SDCは`src/snestang.sdc`と`console138k_combined.sdc`。後者は実PLLに合わせmclk約21.505376 MHz、SDRAM fclk約64.516129 MHz、hclk 74.25 MHz、hclk5 371.25 MHz、USB 12/96 MHzを指定している。UART instanceのFREQ指定は21.484 MHzで、実mclkとわずかに異なる。この差をCRT作業に紛れて変更せず、実clockでもUART試験する。

再現commandは親で`python tools/build_snes_crt_s0.py`。実行前にSNESのbranch・元commit・clean状態を検証し、追跡file全体のSHA256を前後で照合する。結果・timing・資源量・warning・生成物SHA256は`verification/snes-crt-s0/fpga-build.json`と同directoryのreportに記録する。build成功と実機合格を分ける。

今回のbuildは635.55秒実行後、利用者の停止依頼を優先し配置処理中（Placement Phase 2）に終了した。追跡file全体の前後SHA256は一致。これはbuild不具合の再現ではなく、明示的な中断である。bitstream生成・setup/hold判定・最終資源比較は未完了。部分生成物は実機へ導入しない。logには元からの`audio_en`未駆動、PLLのPA1019等のwarningが出ており、無warningの基準版とはしない。再開時はまずこの変更前buildを完了する。

## 3. 映像経路とNESとの差

| 項目 | 現在のSNESTang | NESとの差・適用方針 |
| --- | --- | --- |
| PPUからの入力 | `main.v`→top→`snes2hdmi.v`、BGR555、DOTCLK、9bit X/Y、blanking | NESのpalette index/RGB変換をコピーしない |
| 書込み | mclkでDOTCLK立上り、非blank、`ys[7:0]<224`の画素を採用。addressは`{ys[4:0],xs[8:1]}` | SNES既存のsample条件を維持する |
| 既存buffer | 256画素×32行×15bit、mclk書込み/hclk同期読出し | commentの「16 lines」ではなくBUF_WIDTH=5が実装。追加bufferはまず不要 |
| 拡大 | 256×224相当を960×720へ分数拡大。左右各160画素は`0x303030` | 表示寸法は現在NESと同じだが、read latencyと色変換は別に照合する |
| 色変換 | bufferのBGR各5bitに下位0を3bit付加してRGB888化 | 31を255へ正規化する変更は混ぜない（現行最大248を保持） |
| 合成 | 現行はOSD maskに応じてOSD背景ごとRGBを置換し、その後HDMI | CRTはRGB888化の後、OSD合成の前へ挿入する |
| 同期 | SNESの最初の行の生成後にrefreshで一時停止しHDMIへ同期 | OSDによるpauseではない。この機構とaudio FIFOを維持する |
| 音声 | 32kHz、既存dual-clock FIFO | CRTのために再設計しない。既存`audio_en`未駆動warningは記録して実機で独立確認する |

PPUにはHIGH_RES、FIELD、INTERLACE、224/239行のOVERSCANが存在する（`ppu.v`のSETINI処理および出力）。しかしtopではHIGH_RES/FIELD/INTERLACE出力を接続せず、HDMI側は`ys[8]`を無視し、224行未満だけをbufferへ書き、Xを`xs[8:1]`へ縮約している。

したがって「SNESの全modeを完全表示している」とはしない。最初は既存の表示変換をそのまま保ち、通常224行表示を対象とする。239行・high-resolution・pseudo high-resolution・interlace・PALの本来の再現は未確認で、S3b前にmode信号の接続とfallback方針を決める。単にNESの224定数と走査線位相を移植して全mode対応と表示しない。

## 4. UARTと設定の差

`src/iosys/iosys_bl616.v`は2 Mbaud、`AA / length16 / command / payload`の既存経路を持つ。設定command 0x03は4byte big endianだが、SNES topでは`core_config`出力自体が未接続。0x10のwindow更新と0x11のOSD key更新は既に存在する。

| 項目 | SNES現行 | NES現行から再利用するもの |
| --- | --- | --- |
| 能力通知 | OSDWIN1のみ | S1でOSDWIN1+CRTSTG1。blur/scanline未実装時はCRTBLR1/CRTSCN1を通知しない |
| frame設定 | なし | `tc_crt_config.sv`の保持bus/request/ack、pixel frame開始の一括反映 |
| 適用照会 | 0x12なし | `AA 00 01 12`要求、`AA 00 05 12`+applied32 big endian返信 |
| 返信中のRX | RECV_RESPONSE_ACKでTX終了まで受信停止 | NES修正版のRX継続、pending query集約、返信用snapshotを移植 |
| packet検証 | 0x03で厳密length未確認 | NES側のlength=5検証を再利用し、他commandも回帰試験する |

ACKは受信済み要求値のechoにしない。frame適用後にmclkへ戻った値を返信する。BL616の約100ms poll・250ms再送・保持中のtick処理は既存実装を使う。S1のbypass段階ではFRAME ACKは設定のframe適用確認であり、ぼかしや走査線の画質効果を意味しない。

SDCはNESのinstance名`u_hdmi`をそのまま複写せず、SNESの`s2h/crt_config`に合わせて保持bus/mailboxの実際の境界だけに指定する。全clock間の広いfalse pathは追加しない。

## 5. OSDとcontroller入力

OSDのASCII経路は`iosys_bl616`→`textdisp.v`→`tc_osd_layer.sv`→`snes2hdmi`。論理32×28cell、256×224canvas、2clockのtext読出しに合わせた矩形mask、windowのframe更新は既にある。monitorの16×16日本語一覧とは別経路である。

FPGA直結USB1/USB2は`usb_dual_speed_host`→`usb_game_cdc`→mclkへ入り、DS2とplayer単位でOR合成する。BL616へrawのplayer状態を送り、BL616のUSB HID状態を0x09で戻し、`controller_adapter`でSNESのserial入力へ変換する。実boardではCONTROLLER_SNESは無効だがtopに経路は残っている。

最終`main.JOY1_DI/JOY2_DI`の直前には既に`osd_input_block ? 2'b11 : serial_input`がある。よって直結USB/DS2も遮断対象になる。raw報告はこの遮断より前なのでUI操作を継続できる。ただしadapter内の既存shift registerについて、OSD終了・全解放後の次のlatchまで含め、古い入力が漏れないことをSNES固有に試験する。

現行SNESの予約条件はOSD keyとの完全一致でP2も対象。SELECT+左および追加button保持を予約しない。S1ではNESのP1限定の両chord部分一致予約へ合わせ、左右同時は開かず予約維持、OSD間排他、全button解放待ちを維持する。別source間のbuttonを新たに一つのchordへ合成する変更はしない。DS2/USBがFPGA内でOR合成された後のsource識別は追加できない。

## 6. BL616の共有資源・所有監査

| 資源・処理 | 現在の所有と制約 |
| --- | --- |
| `fcore` / `fbuf` | main.cppのnoncacheable FILと64byte整列buffer。JTAG、ROM ID、保存読取り、defaults、各ROM loaderが共用 |
| 起動順 | Ui16Runtimeはprogram→core ID→能力取得→load。CRT能力がある場合のみ、load adapterがID→restore→defaults→loaderを逐次実行 |
| ROM loader | `core/snes.cpp`は同じfcore/fbufでheader解析、ROM転送。末尾でf_close、以降background ROM読取りなし。ゲームのROM/WRAM/ARAM等はFPGA内SDRAMで処理 |
| ゲームのSRAM | SNES loaderにbackup未実装のTODO。CRT保存recordとSNESのゲームsave RAMを混同しない |
| OSD/session | main_taskがUIとsessionを所有。成功起動・button解放後にnew_session。program/load開始および失敗でID/restore/defaultsをclearする |
| UART受信task | joystick/CRT状態に加えfloppy type4/5を処理。同じfbufを使用し、type4はfloppy有効判定より前にfbufへ書く。core別の受信guardがない |
| FPGAのFDD信号 | SNES topではiosysのmgmt/FDD入力を未接続。S1で未使用入力を明示的に0へ固定し、不要なdisk要求を出さない契約を明確にする |
| FatFs | `fatfs_conf_user.h`: FF_FS_REENTRANT=0、FF_FS_LOCK=0。joypad用state_mutexはstorageの排他ではない |
| USB HID tasks | 入力reportを扱い、調べたapplication側ではfcore/fbufやFatFsを直接使わない。ただしUSB storage transportの処理とは別である |
| SDH/DMA | 保管SDKのdisk read/writeは同期APIを呼び、その内部でADMAを開始し完了/timeoutを待つ。非cache領域・alignmentを維持する。timeout後のDMA停止まで安全と断定しない |
| USB volume | SDKのMSC read10/write10経路。SDと同等の実機確認済みとはしない |
| 明示SAVE | `ui16_hw_save_crt()`はcore_running、CRT能力、active_core=1、identity.system=1を要求。現状SNESでは拒否される |

重要な依存：CRTSTG1を通知するだけで、現在の共通firmwareはSNESのROM全量ID読取り・保存復元・defaults・CSV推奨sessionまで起動する。したがって「SNES FPGAだけ変更し、保存系は何も影響しない」とはできない。最初のS1ではcore別のsession policyを追加し、SNESを全OFF基準のvolatile previewに限定する。NES側の既存経路・読取り順・SAVE/Reset仕様はそのまま維持する。

S4前には受信taskのdisk commandとstorage所有をcore/状態で制限し、実buildで選択されるSDK/config、正常・失敗・timeout時のDMA完了、既存loaderのshort read/close処理を試験する。SNES loaderには読取り途中の終了やclose成功の検証が十分でない箇所があるため、起動失敗時に前ゲームのID/sessionで保存できないことも独立試験する。広いJTAG変更は行わない。

ROM IDは既存方針どおりraw file全byteを対象とする。SNES loaderが除く512byte copier headerもIDには含める。headerあり/なしは別IDになることを明記し、正規化や移行を暗黙に追加しない。system IDは2。

## 7. 最初の実装範囲と以後の区切り

S0の実機基準確認後、S1ではbypass・OSD2と、その表示に必要なS2のframe設定転送を一つの区切りにまとめる。現在のUIがAPPLYを表示してpollするため、返信だけを後回しにしてWAITING常時表示の版は実機へ渡さない。

| 区切り | 実装・commitの範囲 | 合格条件 |
| --- | --- | --- |
| S0（今回） | 調査・変更前SNES build・基準記録 | SNES独自のtiming/資源を採取し、現行起動・音声・入力・日本語一覧・CSV順序・OSD1を実機で確認 |
| S1+S2 | RGB888直通のCRT入口、core_config配線、frame mailbox/ACK、RX継続、OSD2/P1予約、FDD入力0固定。共通firmwareはSNESだけvolatile sessionへ制限 | 変更前との全RGB/位置/blanking比較、全32組の設定・frame原子反映・連打/保持時収束、window5位置、OSD排他、直結USB/DS2/HID/混在の入力遮断と全解放。実FPGA buildとNES回帰 |
| S3a | SNESのread latencyに合わせた水平3点FIRと先読み | 全強度/端/行境界/位置不変/OSD鮮明性、bypassの同時書込み比較、資源とtiming、実機 |
| S3b | SNESのsource行とmode情報を根拠に走査線の位相/減光を接続 | 通常224行とその他modeを分ける。未対応modeの扱いを明記、併用/ちらつき/音声/回帰/実機 |
| S4a（必要に応じ分割） | CSV/defaults適用→raw ROM ID→保存値read-only復元 | system=2、header方針、優先順位、破損/欠落/失敗時clear、SD不変、NES回帰 |
| S4b | 所有制約を満たしたSNESの明示SAVE | X/Y取消し、再起動/電源再投入、失敗/回復、同値SAVE、CRC/世代/他file不変 |
| S4c | ResetとCSV/defaults更新追従 | preview/取消し/SAVE、推奨更新、USER維持、最終SD復帰 |

S1のOSD2はbypassであることを見出しに明示し、blur/scanlineの値は要求値としてのみ表示する。SAVE/Resetは未対応と表示して操作不能とし、未実装機能の保存成功や効果対応を表示しない。行の並びは既存OSD2に合わせる。最終SAVEで開いたまま、X/Yで未保存変更を取り消して終了する仕様はS4で有効にし、CLOSEや自動保存は追加しない。

各区切りで変更した子repositoryを先にcommitし、親にgitlink・試験記録をcommitする。公開する場合は子を先にpushする。実機合格前の状態にはhw確認tagを付けない。

## 8. 実機依頼の順序と回帰

今回のS0は、現在の媒体・firmwareでSNESを1本起動し、日本語一覧/CSV順序、ゲーム名/映像/音声/P1/P2操作、OSD1を開いてゲーム復帰、OSD1の`<< Main Menu`で一覧へ戻ることを依頼した。2026年11月4日に利用者から「1-4について正常に動作」との報告を受けた。controllerはSFC風、利用者の申告表記は`PID:VID=0079:0006`。USB descriptorとの照合をしていないため、VID:PID順へ読み替えない。ゲーム名・接続先・player別の詳細は未記録で、全入力sourceや全modeの網羅確認とはしない。OSD2はまだ要求していない。

利用者の「作業を停止できるところで停止」に従い、変更前buildを明示的に中断し、記録commitで停止した。起動したbuild processのID・親process・commandを照合して対象だけを終了し、記録scriptも終了したことを確認した。S1のruntime変更、SD/flash書込み、GitHub pushは行っていない。再開時は`tangcore-integrated`のremote更新とlocal変更を再確認する。

S1以後、OSD2に関する依頼は、見出し→SAVE状態→INITIAL→CRT ENABLE/REQUEST→H BLUR→SCANLINE→STORE→APPLY→ROM ID→SAVE操作行→RESET TO RECOMMENDED→DEFAULTS→POSの順で列挙する。画面にない項目や未対応機能を合格条件にしない。実際の表示文字列は段階ごとに記録する。

日本語font/全角表示・一覧の選択/scroll・titles.csv順序はmonitorの既存確認を維持する。共有firmwareを変更した段階ではNESのCRT/保存/Reset/defaultsおよびOSD復帰を回帰確認する。NES試験の固定SHA問題は次に該当試験を実行する前に独立したtest修正として扱い、比較対象を現在版へすり替えない。今回、公開済み4aの`f9bf3b74fc6dddc7f783f72986d1546f3999e7f4`が`github/tangcore-integrated`の祖先であり、旧4a commitと比較対象2file（nes2hdmi.sv/crt_filter.sv）が一致することを確認した。test script自体はまだ変更していない。

SDのdrive文字や前回接続を今回の媒体の根拠にしない。導入が必要な時点で媒体identity・全file内容/属性・対象imageのSHAを新しく照合し、復旧用退避を用意する。S0調査時点ではPCにF:は見えておらず、実機内SDの内容と現在のSNES imageはまだ照合していない。

## 9. 根拠source

- SNES：`build_console138k_usb.tcl`、`console138k_combined.sdc`、`src/boards/console138k.v`、`src/snestang_console138k_usb_top.v`、`src/snes2hdmi.v`、`src/controller_adapter.sv`、`src/iosys/iosys_bl616.v`、`src/iosys/tc_osd_layer.sv`、`src/main.v`、`src/ppu.v`、`src/pll/gowin_pll_{snes,hdmi}.v`。
- NES：`src/nes2hdmi.sv`、`src/nestang_top.sv`、`src/iosys/{crt_filter.sv,tc_crt_config.sv,iosys_bl616.v}`、`console138k_combined.sdc`。
- BL616：`main.cpp`、`core/snes.cpp`、`core/cores.cpp`、`fatfs_conf_user.h`、`ui/ui16_launch.*`、`ui/ui16_crt.*`、`ui/ui16_osd*`、`ui/ui16_rom_id.cpp`、`ui/ui16_crt_{restore,save,defaults}.cpp`、`utils/utils.cpp`、`usb/usb_gamepad.cpp`。
- SDK調査は保管済み`build-integrated-20261101/bouffalo_sdk`のFatFs SDH/USB portと`bsp/common/sdcard/sdh_sdcard.c`を参照。次回firmware buildのSDKと同一であるかは別途確認する。
