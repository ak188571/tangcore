# SNES S3b：現在の取込み行に対応した走査線

2026年11月6日。S3aの実機報告を基準に、Console138Kだけで走査線を追加する。作業branchは`tangcore-integrated`。共有firmwareはS3aの`3560c1b`と同じbinaryを使い、NES/monitorと保存機能は変更しない。

## 先に行った映像modeの調査

`src/ppu.v`はOVERSCANに応じ224/239行を生成し、`X_OUT={OUT_X,DOT_CLK}`、`Y_OUT={FIELD,OUT_Y}`を出力する。high-resolution/pseudo-high-resolution時はDOT_CLKの両相へ別の色を出す。INTERLACEはBGINTERLACEに対応し、内部のBG/OBJ処理にFIELDを使う。

一方、現在のConsole用`src/snes2hdmi.v`はDOTCLK立上りだけで、`!hblank && !vblank && ys[7:0]<224`の画素を取込み、X addressは`xs[8:1]`、Y addressは`ys[4:0]`を使う。従って既存の取込みは256×224、239行modeでも後ろ15行を取込まない。high-resolutionの両相保存やfieldを分離した保持も行っていない。BRAMは5bit行addressなので32行分であり、古い16行というcommentは実寸ではない。

Console topはHIGH_RES/FIELD/INTERLACEを未接続にし、mainはV224_MODEを捨てている。さらにSNES内部のPPU接続ではHIGH_RESも未接続である。これらの信号が有効なmode情報としてHDMIへ届いているとは扱わない。

出力側はXを256/960、Yを224/720で進め、横160画素の余白を置く。Yは各出力行で`ycnt += 224`し、720を超えると1行進む。fieldはこの読出し位相に寄与しない。S3bはこの現在表示している224行の位相へ走査線を合わせる。239行・half-dot・interlaceの再構成やPAL cadenceを改善する変更ではなく、元のsampling・buffer・pause・音声は維持する。

## 明暗配分と遅延

各出力行が占めるsource座標の幅を224、各取込み行の周期を720とする。取込み行末の区間[496,720)を暗くし、出力行の区間[p,p+224)との重なりを積分する。pは現行ycnt。強度の最大減光DはOFF/WEAK/STANDARD/STRONGの順に0/2/4/8、各出力行の減光は`round(D * overlap / 224)`、RGBは`round(rgb * (16-depth) / 16)`とする。

到達可能なpは16刻みの45通り。720出力行には45行の位相周期が16回あり、減光depthの総和はそれぞれ0/448/896/1792になる。NESと定数・LUTは結果的に一致するが、SNES側の現在の取込み・拡大比から別途導出した。別の表示高さへ定数だけを流用しない。

走査線単独の登録済みRGBの遅延は1出力画素なので、`xcnt>=704`でsource列を1つ先読みする。ぼかし併用はS3aの3画素先読みを優先する。Yは左右の余白中に確定しており、旧counter blockを変更しない。全OFF・master OFFは元のread addressをそのまま使う。OSD合成は処理後で、背景余白の色も変更しない。

## 能力通知と範囲

CRT_SCAN/SUPPORT_SCANはdefault 0。Console topだけで有効にし、CRTBLR1とCRTSCN1を通知する。既存firmwareは能力通知に従ってSCANLINEを選択可能にできる。previewは全OFF開始、保存・Reset・ID・推奨値は無効のまま。X/Yで全OFFへ戻る。共有firmwareを書き直す必要はない。

## 試験と実機操作

旧公開SNESの実buffer/scalerを参照し、独立した重なり計算とFIR/gain計算で画素を比較する。720行の位相・積分強度、ぼかし/走査線16組合せ、左右端・位置、live書込み中のOFF一致、OSD5位置、取込みaddress/data、音声、frame同期を確認する。S3a/S1 default parameterの互換性、2 Mbaud UARTとframe ACK、ROM保持型restartも回帰する。

利用者の要望に従い実機のSNES起動は1回にまとめる。通常の同じゲームの起動後、OSD表示順に必要な項目を確認し、走査線3強度・ぼかし併用・master OFF・取消しを同じ起動中に試す。変更していないfirmware/NESの再書込みや、過去に合格したrestart/listのための追加SNES起動は行わない。PC試験をSNES実機合格へ読み替えず、実機結果は別に記録する。

## PCで確認した結果

SNES実装commitは`8cf63536f4c355b1abe2fc05854584cb41f57936`。FPGA buildは1,095.59秒で完了し、setup/hold違反は0/0、reportの最小pulse幅のslackも正だった。既存のPLL/routing等のwarningは残る。imageは5,066,442byte、SHA256は`bcc879e4f6da1194b8fa43edb487f71ac13c8b6037086558a42b6fa80b0dc429`。

S3a比でregister +6、LUT +96、ALU +2、MULT12X12 +3。BSRAM 84、MULTALU27X18 22、MULT27X36 4は変わらない。新しいframe/行bufferは追加しなかった。

関連6commandが合格した。新しい統合試験は4,700万画素で16組合せと720行の幾何学的な位相参照を確認し、S3aの1,450万画素・S1の4,400万画素の互換試験も通った。UARTは実clock相当・2 Mbaudで能力通知、全32設定、frame適用を確認した。未変更のfirmwareに両能力を通知したpreviewも全32設定で試験し、SCANLINE選択、保存/Reset無効、FRAME ACK、取消しを確認した。SDのみを更新する導入手順は、代替媒体による保護・復旧試験12件に合格した。

共有firmwareは229,168byte、SHA256 `c19bffa18855ffd38ea56ce5bc0f452463551bf6239bf05a5a0cdfcae3d42e5c`のS3a binaryを維持する。新しいflash読取り・書込みは行わない。SD移動後に現在の全file・属性を改めて退避し、SNES imageだけを更新する。S3bの実機確認は未実施。

## SDへの導入

同日、利用者のmicroSD接続報告後にvolume・物理disk情報と旧imageを照合し、全63fileを新しいsessionへ退避した。現在のSNES imageは確認済みS3aと一致し、S3a導入後の全63fileの内容・属性にも変更はなかった。

SNES imageだけを1回更新し、別commandで全fileを再読取りした。新imageのSHA256一致、他62fileの内容不変、SNESを含む全file属性の維持、退避の完全性を確認した。flash読取り・書込みはともに0回。直前のS3aへ戻すSNES imageと手順を保持している。S3bの実機画質は確認待ちで、1回のSNES起動中に必要な比較をまとめる。
