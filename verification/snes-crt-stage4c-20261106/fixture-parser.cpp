
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
