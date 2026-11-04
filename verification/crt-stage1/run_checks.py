from pathlib import Path
import os,subprocess,json,time,hashlib,sys
out=Path(__file__).resolve().parent
root=out.parents[1]
git=r'D:/Users/foobaris/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
env=os.environ.copy();env.update(MSYSTEM='UCRT64',PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
env['PATH']=r'C:\msys64\ucrt64\bin;C:\msys64\usr\bin;'+env['PATH']
def revision(repo):return subprocess.check_output([git,'-C',str(root/repo),'rev-parse','HEAD'],text=True).strip()
sources={}
for repo in ['firmware-bl616','nestang']:
    files=subprocess.check_output([git,'-C',str(root/repo),'ls-files','-z']).decode().split('\0')
    for name in files:
        if name:sources[repo+'/'+name]=hashlib.sha256((root/repo/name).read_bytes()).hexdigest()
record={'commits':{repo:revision(repo) for repo in ['firmware-bl616','nestang']},'results':[]}
host=['system_menu','navigation','browser','folders','scroll','wrap','titles','sender','launch','font_sender','sd_font','sd_font_menu','reliable_link','reliable_menu','osd','crt']
checks=[('host-'+n,'firmware-bl616','tools/ui16/test_'+n+'.sh') for n in host]
checks += [('rtl-config','nestang','tests/crt/test_config.sh'),('rtl-integration','nestang','tests/crt/test_integration.sh')]
for name,repo,script in checks:
    start=time.monotonic();log=out/(name+'.log')
    with log.open('wb') as f:
        r=subprocess.run([r'C:\msys64\usr\bin\bash.exe','--noprofile','--norc',script],cwd=root/repo,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=300)
    record['results'].append({'check':name,'exit_code':r.returncode,'seconds':round(time.monotonic()-start,2),'log':log.name})
    (out/'checks.json').write_text(json.dumps(record,indent=2))
    print(name,r.returncode,flush=True)
    if r.returncode:print(log.read_text(errors='replace')[-4000:]);sys.exit(r.returncode)
assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==sha for name,sha in sources.items())
record.update(source_hashes=sources,sources_unchanged_during_checks=True)
(out/'checks.json').write_text(json.dumps(record,indent=2))
print('PASS: 16 host scripts and 3 RTL scenarios in 2 scripts; sources unchanged',flush=True)
