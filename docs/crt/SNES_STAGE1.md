# SNES CRT・OSD2 S1/S2

2026年11月6日。Console138K用。S0の新基準はSNES `32433c5`、共有firmware `7749b60`、NES `ec33410`。いずれも`tangcore-integrated`から作業した。OSD1のROM保持型Restart GameとReturn to Game Listを維持する。

## 実装範囲

SNESのBGR555からRGB888へ変換したゲーム映像に、遅延のないbypass入口を設けた。既存buffer、read address、拡大、左右余白、音声、frame同期は変更しない。OSDは引き続きゲーム映像より後で合成する。

Console138K topでのみCRT_STAGE1/SUPPORT_CRTを有効にする。能力通知はOSDWIN1、CRTSTG1、RSTROM1。CRTBLR1/CRTSCN1を通知せず、ぼかし・走査線はまだ実装しない。frame開始で要求設定を一括反映し、適用後の値をcommand 0x12で返す。返信中もRXを継続し、照会をpendingへ集約する。NESの検証済みmailboxを再利用し、SDCの対象をSNESの実hierarchyへ合わせた。未使用FDD要求入力も0へ固定した。

SNESは全OFFを起動基準とするvolatile previewだけを使う。ROM ID・保存record・defaultsの追加読取りを行わず、CSV推奨値もまだsessionへ渡さない。SAVE/Resetは未対応表示で選択できない。X/Yは要求値を起動基準へ戻して終了する。NESの既存session・SAVE/Reset/defaultsは従来の経路を維持する。

## SNES固有の入力修正

最終JOY_DIの遮断だけでは、serial変換器に保持されたbuttonがOSD終了後の途中の読取りへ漏れる場合を回路試験で再現した。`controller_adapter`へ既定OFFのBLOCK_OSDを追加し、Console138KのP1/P2でだけ有効化した。OSD中は変換器の保持bitも中立にし、全解放後に古いsuffixを露出しない。通常入力の変換・他boardの既定動作は維持する。

この修正前のbuildは配置処理中に中断し、`verification/snes-crt-stage1-20261106/superseded-input-gate`へ記録した。実機には導入していない。旧動作の期待失敗と、修正後の12button・通常入力復帰の合格を別に記録した。

## PC試験

- host回帰12件：OSD、CRT、起動adapter、保存読取り、SAVE、defaults、ROM ID、CSV一覧、folder、scroll、折返し、OSD1 dispatch。SNESの追加I/Oなし、SNES SAVE拒否、preview取消し、次のNES sessionへの復帰も検証する。
- SNES UART：全32値、長さ不正拒否、frame前は旧値、pending集約、設定/文字描画のRX継続、P1予約、能力文字列を確認。実mclk相当の46.5ns周期、FREQ指定21.484 MHz、外部2 Mbaudでも実送受信回路を試験した。
- 映像：公開済みSNES基準の実scaler/buffer/OSD/audioと4,400万画素比較。全32設定、5位置、連続書込み、RGB・位相・余白・read/write address・OSD・音声・frame同期が一致。239行相当やfield bit入力も含むが、本来の全mode表示の認定ではない。
- mailbox：frame外の変更禁止、受信のみではACKしないこと、最新値への集約、reset、bypass 65,536サンプル。
- NES/SNESのOSD1再起動回帰。SNESはCRT能力を有効にした組合せで検証。
- serial入力：旧動作で期待失敗を再現し、修正後は12buttonの保持bit遮断と通常入力復帰に合格。

共有firmwareはConsole138K/UI16/SD fontの既存設定でbuild成功。229,088byte、SHA256 `16efcc8d0b110e075e74f7b11bde29fa42d8a93d5d91476f773505e594c4586d`。source commit `70d39d8`。FPGAの最終build結果は同verificationの`fpga-build.json`を参照する。

SNESの合成・配置配線・bitstream生成は成功し、setup/hold違反は0/0。source commitは`a142a29`。imageは5,050,570byte、SHA256 `37139d5afa3724a7677aca586e7b78d24cc9a5200a918ce1281fdc5a60a77f75`。OSD1基準からregisterは212、LUTは138、ALUは34増加し、BSRAMと3種の乗算資源は増加0。既存PLL・sys_clk_dのrouting等のwarningは残る。無warningの版や全timing項目の保証とはしない。

build中に設計fileが変わらなかったことをSHA256で確認した後、既存の改行形式と追加行の字下げ・末尾空白を整えた。build時sourceとcommitしたsourceの差が行の前後の空白だけであることは`final-source.json`へ記録した。導入scriptの代替媒体/flashによる27試験も合格したが、これは実機への書込みではない。

## 実機の扱いと次段階

この文書のPC試験をSNESの実機合格へ読み替えない。実機結果は独立して記録し、合格するまでS3aのぼかしへ進めない。S1では保存recordを更新しない。実機導入時は今回の媒体identity・file内容/属性・全flashを新しく退避して照合し、更新範囲外と日本語一覧・CSV順序・NES imageを保持する。

実機確認の列挙順は見出し、SAVE状態、INITIAL、CRT REQUEST、H BLUR REQ、SCANLINE REQ、STORE、APPLY、ROM ID、SAVE操作行、RESET操作行、DEFAULTS、POSとする。詳細は同directoryの`SNES_STAGE1_TEST_GUIDE.md`。ODT版はlocal導入用directoryにある。

再現commandは共有firmwareの`tools/ui16/test_*.sh`、SNESの`tests/crt/test_stage1.sh`、親の`tools/test_osd1_restart.sh nes|snes`。親の`tools/test_snes_crt_stage1.py`は関連試験を一括実行してlogを保存する。buildscriptは`tools/build_snes_crt_stage1.py`と`tools/build_snes_crt_firmware.py firmware`。FPGA試験は公開基準SHAを使い、未公開の旧NES SHAへ依存しない。

## 実機確認完了

2026年11月6日、SNES「スーパーマリオコレクション」で通常起動・日本語一覧/CSV順序・映像音声操作、OSD2の表示順1〜13、X/Y取消し/解放待ち、排他/左右同時予約、OSD1再起動/一覧復帰の正常報告を受けた。接続先はUSB P1。続くNES「ドクターマリオ」の既存設定/CRT preview/X/Y取消し/再起動/一覧復帰、およびSNESへ戻った際の全OFF/DEFAULT/UNAVAILABLE復帰も正常との報告を受けた。新しいSAVE/Reset操作は依頼していない。

local tagは`snes-crt-stage1-hw-20261106`。USB P2・DS2・BL616側USB、全ゲーム/映像mode、長時間試験の結果へ広げない。SD内容/属性の一致は導入時に測定したもので、ゲーム試験後に媒体を再読取りしたとの記録にはしない。詳細は`hardware-results.json`。
