# CRT変更のGitHub公開記録

第5gまでの確認済み変更をGitHubへ公開する。GitHubの非公開email保護（GH007）に対応し、未公開commitとtagのemailをGitHubのnoreplyへ置き換えた公開用の履歴を作成した。元のlocal履歴と実機確認済みtagは変更せず保持している。

| 対象 | 元の確認済みcommit | 公開用commit |
| --- | --- | --- |
| TangCore | acffc53e41a3d3e0424dbd0b54b1faddbf748ed5 | f4a9620abca970d2e645b86114ce9d8ef000a109 |
| BL616 firmware | 8faebdeca1a24a1e14c9c8100e2b1c0e3e56f381 | 3d3f429625a3684a79d59ea8bbd25caf36e61606 |
| NES | c8df819ae6b96f1bc645b2d03b9e7714d8a9117e | a39e60961d8ac49395676ef7ea41321f01333c5d |

firmwareとNESの各commitはtreeが完全に同一。親の既存commitはsubmodule参照だけを対応する公開用commitへ置き換え、それ以外のファイル内容は同一と照合した。commitの名前・日時・messageを保持し、emailと親commit参照の変更によりcommit番号が変わった。実機結果・firmware binaryのSHA・従来の配布ZIPの内容は変わらない。過去の文書にあるcommit番号は元の検証済み履歴を示す。

全79個の親commitとsubmodule側の対応、11個のtagの新旧対応はverification/github-publication-20261104/commit-map.jsonに記録した。公開tagは同名で公開用commitを指す。過去の診断版はfirmwareのcrt-stage5-diagnostics-archive-20261103に保存する。親の作業branchはcrt-osd2-stage1、最新firmwareはcrt-stage5g-defaults-20261104、NESはcrt-osd2-stage1。既存tangcore-integratedとmain/masterは維持する。

この公開記録と対応表だけを、公開用の親branchへ追加commitする。現在のConsole138K/NESでの第1〜第5段階完了と、他core/volume等が実機未確認である範囲はSTAGE5G_DEFAULTS.mdおよびhardware-results.jsonのとおり。
