"""Fresh read-only SD capture after compact OSD tests; never rewrites records or metadata."""
from pathlib import Path
import argparse,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('compact_deploy',HERE/'deploy.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d);k=d.k
def run(args):
    m=d.package();session=HERE/'session-01';s=k.load(session/'session.json')
    k.require(s['manifest_sha256']==k.digest(HERE/'manifest.json') and s.get('flash_installed'),'Verified compact firmware installation required')
    root,card=d.identity(args.drive);k.require(card==s['sd']['identity'],'Different card')
    dest=(HERE/args.snapshot).resolve()
    k.require(dest.is_relative_to(HERE.resolve()) and dest!=HERE.resolve() and not dest.exists(),'Use a new snapshot directory inside this kit')
    dest.mkdir();entries={}
    for name,p in sorted(k.user_files(root).items()):
        before=d.file_entry(p);target=dest/'sd'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        k.require(k.digest(target)==before['sha256'] and d.file_entry(p)==before,'SD changed during capture: '+name);entries[name]=before
    d.check_sd_files(root,entries)
    observed=dict(at=d.now(),identity=card,files=entries,audit='pending',read_only_card_access=True,flash_operations=0)
    k.save(dest/'snapshot.json',observed)
    k.require(entries==s['sd_installed']['files'],'SD content or attributes changed; fresh capture preserved; inspect without restoring actual user data')
    observed['audit']='passed';k.save(dest/'snapshot.json',observed)
    report=dict(at=d.now(),files_checked=len(entries),all_file_contents_and_attributes_unchanged=True,actual_USER_and_Reset_records_unchanged=True,metadata_unchanged=True,read_only_card_access=True,flash_operations=0,auditor_sha256=k.digest(Path(__file__)))
    k.save(HERE.parent/'crt-osd2-20261101/verification/osd2-compact-start-release-20261107/post-runtime-sd-audit.json',report)
    state=k.load(HERE/'STATE.json');state.update(post_runtime_SD_invariance='passed',post_runtime_snapshot=dest.name);k.save(HERE/'STATE.json',state)
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--drive',required=True);p.add_argument('--snapshot',default='post-runtime-01');run(p.parse_args())
