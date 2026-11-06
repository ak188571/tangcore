"""Parse exact deployment metadata through production C++ parsers; no card access."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];FW=ROOT/'firmware-bl616'
KIT=ROOT.parent/'snes-crt-stage4c-hardware-20261106';OUT=ROOT/'verification/snes-crt-stage4c-20261106'
source=OUT/'fixture-parser.cpp'
source.write_text(r'''
#include "ui16_titles.h"
#include "ui16_crt_defaults.h"
#include <cassert>
#include <fstream>
#include <iterator>
#include <sstream>
extern "C" {
#include "ff.h"
FRESULT f_open(FIL *,const char *,unsigned char){assert(false);return FR_DISK_ERR;}
FRESULT f_read(FIL *,void *,UINT,UINT *){assert(false);return FR_DISK_ERR;}
FRESULT f_close(FIL *){assert(false);return FR_DISK_ERR;}
}
static std::string read(const char *p){std::ifstream f(p,std::ios::binary);assert(f);return {std::istreambuf_iterator<char>(f),{}};}
static Ui16GameList parse(const std::string &data,const std::vector<std::string> &names){
    Ui16GameList g;g.names=names;g.status=Ui16ListStatus::Ready;g.directories.resize(names.size(),false);
    Ui16TitlesParser p(g);for(char c:data)assert(p.feed(&c,1));assert(p.finish());return g;
}
int main(int argc,char **argv){
    assert(argc==4);const auto original=read(argv[1]),fixture=read(argv[2]);
    std::istringstream lines(original);std::string line;std::vector<std::string> names;
    assert(std::getline(lines,line));while(std::getline(lines,line))if(!line.empty())names.push_back(line.substr(0,line.find('\t')));
    const auto a=parse(original,names),b=parse(fixture,names);assert(a.names==b.names&&a.titles==b.titles&&a.directories==b.directories);
    unsigned assigned=0;
    for(unsigned i=0;i<b.names.size();++i){
        const bool target=b.names[i]=="Super Mario Collection (Japan).sfc";
        assert(b.crt_recommendations[i].present==target);if(target){++assigned;assert((b.crt_recommendations[i].settings==Ui16CrtSettings{true,2,1}));}
    }
    assert(assigned==1);const auto text=read(argv[3]);
    const auto snes=ui16_parse_crt_defaults(text,2),nes=ui16_parse_crt_defaults(text,1);
    assert(snes.state==Ui16CrtDefaultsState::Ready&&snes.source==Ui16CrtDefaultsSource::System&&snes.recommendation.present);
    assert((snes.recommendation.settings==Ui16CrtSettings{true,3,2}));
    assert(nes.state==Ui16CrtDefaultsState::Ready&&!nes.recommendation.present);
}
''',encoding='utf-8')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;C:/msys64/usr/bin;'+env['PATH']
exe=FW/'build-ui16-host/snes-stage4c-fixture-parser.exe'
cmd=['C:/msys64/ucrt64/bin/g++.exe','-BC:/msys64/ucrt64/bin/','-std=c++17','-Wall','-Wextra','-Werror','-pedantic','-DUI16_SYSTEM_MENU',
     '-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(FW/'tests/ui16'),'-I'+str(FW/'ui'),str(source),
     str(FW/'ui/ui16_titles.cpp'),str(FW/'ui/ui16_crt_defaults.cpp'),'-o',str(exe)]
original=ROOT.parent/'snes-crt-stage4b-hardware-20261106/post-save-01/sd/snes/titles.csv'
inputs=[original,KIT/'payload/snes-titles-s4c.csv',KIT/'payload/defaults-s4c.tsv']
with (OUT/'fixture-parser.log').open('wb') as log:
    subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run([str(exe),*map(str,inputs)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
result=dict(passed=True,production_parsers=True,all_names_Japanese_titles_and_order_preserved=True,
            only_target_has_CSV_recommendation=True,SNES_only_defaults_preserves_NES_recommendation=True,
            input_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},device_access=False)
(OUT/'fixture-parser.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
