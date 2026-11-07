"""Guarded temporary record/default transitions; only exact known fixtures may be restored."""
from pathlib import Path
import argparse, importlib.util, os, shutil, sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from osd2_load_info_fixtures import A,B,D,TARGETS,profiles
spec=importlib.util.spec_from_file_location('load_info_deploy',HERE/'deploy.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d);k=d.k

def capture(args,root,state):
    dest=(HERE/args.snapshot).resolve()
    k.require(dest.is_relative_to(HERE.resolve()) and dest!=HERE.resolve() and not dest.exists(),'Use a fresh snapshot inside this kit')
    dest.mkdir(parents=True);entries={}
    for name,p in sorted(k.user_files(root).items()):
        before=d.file_entry(p);target=dest/'sd'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,target)
        k.require(k.digest(target)==before['sha256'] and d.file_entry(p)==before,'SD changed during capture: '+name)
        entries[name]=before
    d.check_sd_files(root,entries)
    k.save(dest/'snapshot.json',dict(at=d.now(),identity=state['sd']['identity'],files=entries,audit='pending',card_writes=0))
    return dest,entries

def expected(state,fixtures,phase):
    entries={n:dict(row) for n,row in state['sd']['files'].items()}
    if phase!='original':
        for name,data in fixtures[phase].items():
            entries[name]=dict(bytes=len(data),sha256=k.sha(data),attributes=entries[name]['attributes'] if name in entries else 32)
    return entries

def write_bytes(path,data,attributes):
    old=d.attrs(path) if path.exists() else None
    if old is not None and old&1:d.set_attrs(path,old&~1)
    try:
        with path.open('wb' if path.exists() else 'xb') as stream:
            k.require(stream.write(data)==len(data),'Short fixture write')
            stream.flush();os.fsync(stream.fileno())
    finally:
        if path.exists():d.set_attrs(path,attributes)
    k.require(path.read_bytes()==data,'Fixture readback differs')

def run(args):
    path,state=d.load_state(args);d.package()
    k.require(state.get('compact_sd_audit_passed') and state.get('flash_installed'),'Verified firmware and fresh baseline SD audit required')
    d.before_flash(args,state);root=d.checked_card(args,state)
    dest,entries=capture(args,root,state) # Preserve observations before rejecting drift.
    original=state['sd']['files']
    k.require(D not in original,'Existing defaults must not be overwritten')
    for name in (A,B):
        p=args.session/'sd'/name
        k.require(d.file_entry(p)['sha256']==original[name]['sha256'],'Actual record backup corrupted')
    fixtures=profiles((args.session/'sd'/A).read_bytes(),(args.session/'sd'/B).read_bytes())
    current=state.get('fixture_phase','original')
    if args.operation=='recover-original':
        # Partial known transitions may be recovered, but never an unknown USER save.
        k.require(set(entries)<=set(original)|{D} and set(original)<=set(entries),'Unexpected file set; capture preserved')
        for name,row in entries.items():
            allowed=[expected(state,fixtures,p).get(name) for p in ('original','system','global','errors')]
            k.require(row in allowed,'Unknown change; do not overwrite user data: '+name)
        target='original'
    else:
        k.require(not state.get('fixture_transition_pending'),'Incomplete transition; inspect or recover known bytes')
        k.require(entries==expected(state,fixtures,current),'SD content/attributes changed; capture preserved; no writes')
        if args.operation=='audit':
            k.require(current=='original','Restore original records/defaults before final audit')
            report=dict(at=d.now(),files_checked=len(entries),all_original_contents_attributes_restored=True,card_writes=0)
            k.save(dest/'audit.json',report);print(report);return
        target=args.operation
        k.require((current,target) in [('original','system'),('system','global'),('global','errors'),('errors','original')],'Unexpected phase order')
    wanted=expected(state,fixtures,target)
    state['fixture_transition_pending']=dict(at=d.now(),source=current,target=target,snapshot=dest.relative_to(HERE).as_posix())
    k.save(path,state)
    for name in TARGETS:
        if name not in wanted:
            if (root/name).exists():(root/name).unlink() # Only the verified temporary defaults.
            continue
        if entries.get(name)==wanted[name]:continue
        data=(args.session/'sd'/name).read_bytes() if target=='original' else fixtures[target][name]
        write_bytes(root/name,data,wanted[name]['attributes'])
    d.check_sd_files(root,wanted)
    state['fixture_phase']=target;state.pop('fixture_transition_pending',None)
    state['sd_installed']=dict(at=d.now(),files=wanted)
    state.setdefault('fixture_transitions',[]).append(dict(at=d.now(),source=current,target=target,snapshot=dest.relative_to(HERE).as_posix()))
    k.save(path,state)
    snapshot=k.load(dest/'snapshot.json');snapshot.update(audit='passed',observed_phase=current,next_phase=target)
    k.save(dest/'snapshot.json',snapshot)
    print('Verified transition:',current,'->',target,'; titles, ROMs, core images, NES records and unrelated attributes unchanged')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation',choices=['system','global','errors','original','recover-original','audit'])
    p.add_argument('--drive',required=True);p.add_argument('--session',type=Path,default=HERE/'session-01');p.add_argument('--snapshot',required=True)
    args=p.parse_args();args.session=args.session.resolve()
    k.require(args.session.is_relative_to(HERE.resolve()) and args.session!=HERE.resolve(),'Keep session inside this kit')
    k.require(args.session.drive.upper()!=args.drive.upper(),'Backups must be on the PC')
    run(args)
