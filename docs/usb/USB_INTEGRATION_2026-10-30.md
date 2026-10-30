# console138k USB反映記録（2026年10月30日）

指定4機種（0810:0001、0079:0006、ELECOM11ff:3331緑/赤、Xbox045e:028e）をP1/P2へ直結する検証済みUSB処理を、monitor/NES/SNESの通常build.tcl console138k経路へ反映した。

各core内のsrc/usb/へ同一の共通moduleとcore adapterを配置し、src/*_console138k_usb_top.*をconsole138k用topとして選ぶ。既存top、legacy USB、UI16/UART等のsourceは維持。他deviceのbuild経路は元のTclをそのまま実行する。既存.gprjは変更せず、今回の検証入力は以下のTcl buildを正とする。

## build

検証に使用したGowinはC:/Gowin/Gowin_V1.9.12.03_x64/IDE/bin/gw_sh.exe。各core directoryを作業directoryにして実行する。

```
# monitor/
gw_sh.exe build.tcl console138k
# nestang/ または snestang/
gw_sh.exe build.tcl console138k ds2
```

既存buildall.batのtoolchain指定は維持しているため、使用するGowin versionを確認する。上記scriptは最後にconsole138k_combined.sdcを渡し、検証時と同じRTL/constraint/optionを使用する。新moduleはcore内にあるため親directoryの共通USB folderには依存しない。

## 検証と保全

buildの有効入力をTclとして評価し、順序付きのsource hash、device/options、最後のSDCまで実機確認済みbuildと一致することを確認。その他のadvertised device/controller経路は反映前と同じTcl command列を維持する。今回はファイル配置・build入口の統合で、検証済みRTL内容の追加変更はない。

先行確認はmonitor292条件、NES/SNES各185条件、3全体buildのsetup/hold違反0。4機種/両端子/両game基本操作、各LSとXboxの同時、代表LS/LS同時、押下中抜去・再接続、S1後復帰、OSD切替の操作を実機確認。個別全buttonや正式なUSB電気適合、全復帰組合せは未測定。monitorの10頁PMOD診断表示は検証した版を維持する。

MODEで一覧へ戻らない挙動とNESロード直後の音声fade-inは従来からとのuser報告で、今回は変更していない。他game coreは後日。Flash/ROM/fontの追加書込み、commit/push、Git index更新は行わない。

元の未commit差分とindexは作業前の記録に照合。対象build.tclの退避と反映前snapshot、詳細なinput同値確認記録はCodex projectのusb-repo-integration-2026-10-30へ保存。検証済みimage一式はverification/usb-host-2026-10-30へ保全し、既存のbuild成果物やmicroSDを上書きしない。
