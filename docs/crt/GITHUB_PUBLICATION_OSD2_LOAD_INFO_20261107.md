# OSD2 補助表示の実機合格構成のGitHub公開

2026年11月7日。公開対象branchは各repositoryのtangcore-integrated。
合格構成の注釈付きtagはosd2-load-info-hw-20261107。
既存の合格tagを維持し、branchはfast-forward、tagは新規作成のみとする。

| Repository | tagが示す内容 |
| --- | --- |
| ak188571/tangcore | 実機結果commit 95e08ead76b26289f96e23025df70b8bff699db3と、本公開情報を含む構成 |
| ak188571/firmware-bl616 | 95c4416187bf19d42793336ba0390b75946d1614 |
| ak188571/snestang | 8cf63536f4c355b1abe2fc05854584cb41f57936 |
| ak188571/nestang | ec33410f2e6078fa20378df3cdae20f84aaf03e9 |
| ak188571/monitorcore | e12b253838b45407dc4de99848218e24112b787c |

親repositoryの95e08ea以降は公開情報の整理のみで、firmwareのsourceやFPGAのgitlinkは変更しない。
変更のないSNES/NES/monitorのtagは構成を固定するもので、全機種・全入力・全映像modeの新たな実機合格を意味しない。

今回の実機範囲はConsole138K・USB P1、スーパーマリオコレクションの3回の起動依頼と、ドクターマリオの1回の起動依頼。
SNESではSYSTEM／RECOVERED、GLOBAL／BAD SAVE、BUILT-IN／NEW SCHEMA／BAD FILE、SAVE拒否と取消しを確認した。
NESでは通常動作、CSV／RESETの補助表示、START保持中の入力遮断、preview・FRAME ACK・取消しを確認した。
実機観察はユーザー報告として記録し、NESの結果からSNES合格を推定していない。

通常の小型表示と英語を維持し、INITIALはLOADED FROM、STOREはSAVE READへ改称した。
共有firmwareは230976 byte、SHA256は次の通り。

```text
f033d8c2240fc9c9d658ba95aa5e46b8a05d9eb95c6a9d6c7bdaeb73401348ba
```

host試験16群、導入保護30件、一時file保護12件が合格。
元のa7 Reset／b6 USERを復元し、一時defaultsを除去した。
最後の新しい読取り退避で、開始時の全65 user file・属性、titles.csv、NES設定との一致を確認した。
CONFLICTの実機表示、物理的なSD読取り故障・電源断、P2/DS2/BL616側USB、全SNES PPU modeは今回の合格範囲に含まれない。

実機結果はverification/osd2-load-info-20261107/results.jsonと、docs/crt/OSD2_LOAD_INFO_20261107.mdを参照。
公開時は依存repositoryを先にpush・照合し、最後に親repositoryをpushする。
各repositoryのbranch、tag object、tagの参照先commitをGitHubから再取得して照合する。
