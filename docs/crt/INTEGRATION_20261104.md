# CRT変更のtangcore-integrated統合

第5gまでの公開済みCRT/OSD2変更を、親と変更したsubmoduleのtangcore-integratedへ統合する。既存の統合履歴と作業履歴を両親に持つmerge commitで区切る。競合はなく、実機確認済みのruntime sourceは変更していない。

| 対象 | 統合前 | 作業履歴 | 統合commit |
| --- | --- | --- | --- |
| BL616 firmware | 6f5e0484c8692eed2b25e3672cbe987b89bd0925 | 3d3f429625a3684a79d59ea8bbd25caf36e61606 | dc5ff3faded02215042ebd4e9cffb7adf480a37d |
| NES | 724994b64e598edf9d11e8824e45895cc2d851a3 | a39e60961d8ac49395676ef7ea41321f01333c5d | 84b73f76e8a08bdcff45c208349955271bb2d2a1 |

親の統合前はa67003941a26ccc856134f0d9142298d94b34483、統合元はc54981127d99132ed7c37ae12f793688fa77b76f。親merge commitは上記submoduleの統合commitを参照し、本書とverification/github-integration-20261104/integration.jsonを追加する。その他のsourceとsubmodule参照は統合元から変更しない。

firmwareとNESは、公開済み作業履歴および元の実機確認済みcommitとtreeが完全に同一であることを照合した。関連11本のhost試験、firmware build、全flash照合、defaults/優先順位/Reset/OSD/入力/不正file拒否/SD復帰/最終起動の既存合格結果を適用する。今回はruntime sourceの変更がないため、追加のbuildや実機への書込みは行わない。実機範囲は現在のConsole138K/NESと記録済み2本のROMで、他core/volume等は従来の未確認範囲を維持する。

非公開email保護への対応による元commitと公開commitの関係はGITHUB_PUBLICATION_20261104.mdとcommit-map.jsonを参照する。既存の作業branch・実機確認tag・元local履歴・配布ZIPを保持する。submoduleの統合branchを先に反映し、その後に親の統合branchを反映する。
