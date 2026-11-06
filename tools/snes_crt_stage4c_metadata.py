"""Guarded temporary metadata for S4c; preserve actual USER/Reset records."""
from pathlib import Path
import argparse,importlib.util,json,os,shutil,struct,sys,zlib
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('s4c_deploy',HERE/'deploy.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d);k=d.k
A='crt/02-232bb5b8-0000000000200000.a'
B='crt/02-232bb5b8-0000000000200000.b'
T='snes/titles.csv';D='crt/defaults.tsv'

def context(args):
    path,state=d.load_state(args);m=d.package()
    k.require(state.get('s4b_sd_audit_passed') and state.get('flash_installed'),'Verified S4c firmware and S4b SD audit required')
    d.before_flash(args,state)
    root=d.checked_card(args,state)
    original=args.session/'sd'/T
    k.require(k.digest(original)==state['sd']['files'][T]['sha256'],'Original titles backup corrupted')
    return path,state,m,root

def install(args):
    path,state,m,root=context(args)
    k.require(not state.get('metadata_install_started'),'Metadata installation already started; inspect before retrying')
    d.check_sd_files(root,state['sd_installed']['files'])
    k.require(D not in state['sd']['files'] and not (root/D).exists(),'Existing defaults must not be overwritten')
    original=(args.session/'sd'/T).read_bytes();fixture=d.image('titles_fixture').read_bytes()
    stripped=b''.join(line.rstrip(b'\r\n').rsplit(b'\t',1)[0]+line[len(line.rstrip(b'\r\n')):] for line in fixture.splitlines(keepends=True))
    k.require(stripped==original,'Names, Japanese titles or order changed')
    state['metadata_install_started']=dict(at=d.now());k.save(path,state)
    # New defaults is exclusive; all metadata preconditions were checked before writes.
    with (root/D).open('xb') as stream:
        contents=d.image('defaults_fixture').read_bytes()
        k.require(stream.write(contents)==len(contents),'Short defaults write')
        stream.flush();os.fsync(stream.fileno())
    d.copy_with_attrs(d.image('titles_fixture'),root/T)
    expected={name:dict(row) for name,row in state['sd_installed']['files'].items()}
    expected[T].update(bytes=m['artifacts']['titles_fixture']['bytes'],sha256=m['artifacts']['titles_fixture']['sha256'])
    expected[D]=d.file_entry(root/D)
    k.require(expected[D]['sha256']==m['artifacts']['defaults_fixture']['sha256'],'Defaults readback differs')
    d.check_sd_files(root,expected)
    path,state=d.load_state(args);state['metadata_installed']=dict(at=d.now(),files=expected)
    state['sd_installed']=dict(at=d.now(),files=expected);k.save(path,state)
    d.event(args,'temporary-metadata-installed',changed=[T,D],names_titles_order_preserved=True,records_written=False)
    print('Temporary SNES-only recommendations installed; names/titles/order and all actual records preserved.')

def capture(args,root,state):
    dest=(HERE/args.snapshot).resolve()
    k.require(dest.is_relative_to(HERE.resolve()) and dest!=HERE.resolve() and not dest.exists(),'Use a new snapshot directory inside this kit')
    dest.mkdir();entries={}
    for name,p in sorted(k.user_files(root).items()):
        before=d.file_entry(p);target=dest/'sd'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,target)
        k.require(k.digest(target)==before['sha256'] and d.file_entry(p)==before,'SD changed during capture: '+name)
        entries[name]=before
    d.check_sd_files(root,entries)
    k.save(dest/'snapshot.json',dict(at=d.now(),identity=state['sd']['identity'],files=entries,audit='pending',card_writes=0,flash_operations=0))
    return dest,entries

def record(data,kind,generation,value):
    k.require(len(data)==32 and data[:8]==b'CRT1'+bytes([1,2,kind,0]),'Record schema/system/kind differs')
    k.require(struct.unpack_from('<IQ',data,8)==(0x232bb5b8,2097152),'Record identity differs')
    k.require(data[20:24]==bytes([value,0,0,0]),'Record settings/reserved bytes differ')
    k.require(struct.unpack_from('<I',data,24)[0]==generation,'Record generation differs; same-mode SAVE may have written twice')
    k.require(struct.unpack_from('<I',data,28)[0]==zlib.crc32(data[:28])&0xffffffff,'Record CRC differs')
    return dict(system=2,kind=kind,generation=generation,value=value,sha256=k.sha(data))

def audit_restore(args):
    path,state,m,root=context(args)
    k.require(state.get('metadata_installed') and not state.get('metadata_restore_started'),'Installed temporary metadata required; restoration must not already have started')
    dest,entries=capture(args,root,state) # Preserve every observed file before assertions.
    expected=state['metadata_installed']['files']
    k.require(set(entries)==set(expected),'Unexpected file set; fresh capture preserved')
    for name,row in expected.items():
        if name!=B:k.require(entries[name]==row,'Unrelated content/attributes or fixture changed: '+name)
    k.require(entries[B]['attributes']==expected[B]['attributes'],'Reset slot attributes changed')
    records=[record((dest/'sd'/A).read_bytes(),0,3,27),record((dest/'sd'/B).read_bytes(),1,4,0)]
    report=dict(at=d.now(),files_checked=len(entries),records=records,same_Reset_SAVE_generation_unchanged=True,
        previous_USER_a3_preserved=True,all_other_file_contents_and_attributes_unchanged=True,
        actual_records_must_not_be_deleted=True,auditor_sha256=k.digest(Path(__file__)))
    snapshot=k.load(dest/'snapshot.json');snapshot.update(audit='passed',record_audit=report);k.save(dest/'snapshot.json',snapshot)
    # The current fixture bytes and every unrelated file were checked before any restoration.
    state['metadata_restore_started']=dict(at=d.now(),snapshot=dest.name);k.save(path,state)
    d.copy_with_attrs(args.session/'sd'/T,root/T)
    k.require(k.digest(root/D)==m['artifacts']['defaults_fixture']['sha256'],'Defaults changed before removal')
    (root/D).unlink() # Only the exact temporary metadata; never touch record slots.
    clean={name:dict(row) for name,row in entries.items() if name!=D};clean[T]=dict(state['sd']['files'][T])
    d.check_sd_files(root,clean)
    path,state=d.load_state(args);state['metadata_restored']=dict(at=d.now(),files=clean,record_audit=report)
    state['sd_installed']=dict(at=d.now(),files=clean);k.save(path,state)
    k.save(HERE/'post-reset-sd-audit.json',report)
    d.event(args,'original-metadata-restored',titles_byte_exact=True,temporary_defaults_removed=True,records_written=False)
    print(json.dumps(report,indent=2));print('Original Japanese titles/order restored; temporary defaults removed; a3 USER and b4 Reset retained.')

def audit_clean(args):
    path,state,m,root=context(args)
    k.require(state.get('metadata_restored'),'Original metadata restoration required')
    dest,entries=capture(args,root,state)
    k.require(entries==state['metadata_restored']['files'],'SD changed after restoration; fresh capture preserved')
    snapshot=k.load(dest/'snapshot.json');snapshot.update(audit='passed',all_contents_and_attributes_unchanged=True);k.save(dest/'snapshot.json',snapshot)
    d.event(args,'post-cold-boot-sd-invariance-verified',snapshot=dest.name,files=len(entries))
    print('Post-cold-boot contents and attributes unchanged; card and flash were not written.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['install','audit-restore','audit-clean'])
    p.add_argument('--drive',required=True);p.add_argument('--session',type=Path,default=HERE/'session-01');p.add_argument('--snapshot',default='post-reset-01')
    args=p.parse_args();{'install':install,'audit-restore':audit_restore,'audit-clean':audit_clean}[args.operation](args)
