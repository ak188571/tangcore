# 開発branchの方針

今後の変更は、`tangcore-integrated`が存在するrepositoryでは同branchを基準にする。機能ごとに作業branchを作る場合も、ここから分岐してここへ統合する。GitHubの既定branchも同じ設定とした。

| repository | 変更を追加する基準branch |
| --- | --- |
| ak188571/tangcore | tangcore-integrated |
| ak188571/firmware-bl616 | tangcore-integrated |
| ak188571/nestang | tangcore-integrated |
| ak188571/snestang | tangcore-integrated |
| ak188571/monitorcore | tangcore-integrated |
| ak188571/gbatang | main（tangcore-integrated未作成） |
| ak188571/mdtang | master（tangcore-integrated未作成） |
| ak188571/smstang | master（tangcore-integrated未作成） |
| ak188571/pctang | master（tangcore-integrated未作成） |

対象は2026年11月4日に実在を確認したbranchである。main/masterの履歴と既存の作業branch・tagは保持する。対象branchのないrepositoryには新設していない。

## submoduleで変更する場合

firmware-bl616、nestang、snestang、monitorの`.gitmodules`に`branch = tangcore-integrated`を設定した。`git submodule update --remote`を明示実行する場合の取得先を揃える。

通常の`git submodule update --init --recursive`は、親が記録したcommitを再現するためdetached HEADとなる。そこで変更を追加する際は、対象repositoryの`tangcore-integrated`、またはそこから分岐した作業branchへ切り替える。新しいsubmoduleのcommitを先にpushし、そのcommitを指す親の変更をcommit・pushする。親のgitlinkは、追従先の設定変更だけでは進まない。

この設定で実行時sourceや実機確認済みのsubmodule commitは変更しない。現在のConsole138K/NESの確認範囲はCRT関連文書に従う。
