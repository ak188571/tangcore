# SNES S0再開：OSD1統合後の基準

2026年11月6日。11月4日の停止を解除して再開した。remoteの`tangcore-integrated`にOSD1の独立した実機確認済み変更があり、親`4f27b84`を取り込んだ。子はfirmware `7749b60`、NES `ec33410`、SNES `32433c5`。前回の調査commitと中断logは保持した。

新しいSNES基準は、OSD1のRestart Game / Return to Game List、RSTROM1 / command 0x13、ROMを保持するゲームresetを含む。P1のSELECT+左も既に予約するが、CRTSTG1がなくOSD2は開かない。11月4日の「OSD1は既存Main Menu」「左chordの予約がない」という記述は歴史的状態で、今回の基準には適用しない。

S0では、保管済みの実SNES buildと、現在のSNES基準のRTL・SDC・Tcl・CST・初期値file計144本を改行正規化の上で照合し、すべて一致した。実bitstreamのSHA256も公開記録の`92e357a3641322fc6b67e843751b53f74eea27eda0499a9a05574a1b752ef987`と一致した。元timing reportのsetup/hold違反は0/0。これを比較基準として採用し、このchatで再buildしたとは記録しない。11月4日の古い基準の未完了buildを再実行する必要はなくなった。

根拠は`verification/snes-crt-s0-resume-20261106`および既存`verification/osd1-20261106/results.json`。SNES実機報告の対象はスーパーマリオコレクションのOSD1・映像音声操作等で、CRT/OSD2は未実装・未確認。SNESのP2や全controller経路の網羅確認ではない。

次はS1+S2として、既存映像のbypass、frame設定/ACK、OSD2接続を行う。共有firmwareはSNESだけvolatile previewとし、CSV/defaults/ROM ID/復元/SAVE/Resetはまだ有効化しない。NESの完成済みCRT設定・保存と両coreのOSD1再起動を維持する。実機合格前に次の効果段階へ進めない。
