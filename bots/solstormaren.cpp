/*#include <cassert>
#include <iostream>
#include <string>
#include <vector>
#include <memory>*/
#include <bits/stdc++.h>
using namespace std;
typedef pair<int, int> pi;

string NAME = "Solstormaren";

int sh[]{2,3,3,4,5};
int a[10][10];
int cnt[10][10];

vector<tuple<int, int, char>> rf(){
    vector<tuple<int, int, char>> r;
    for(int s : sh){
        if(rand()%2){
            r.emplace_back(rand()%10, rand()%(11-s), 'H');
        }
        else{
            r.emplace_back(rand()%(11-s), rand()%10, 'V');
        }
    }
    return r;
}

int cf(vector<tuple<int, int, char>> f){
    for(int i = 0; i < 5; i++){
        for(int j = 0; j < i; j++){
            if(get<2>(f[i]) == 'H' && get<2>(f[j]) == 'H'){
                if(abs(get<0>(f[i])-get<0>(f[j]))<=1 && get<1>(f[i])-sh[j]<=get<1>(f[j]) && get<1>(f[j])<=get<1>(f[i])+sh[i])
                    return 0;
            }
            if(get<2>(f[i]) == 'V' && get<2>(f[j]) == 'V'){
                if(abs(get<1>(f[i])-get<1>(f[j]))<=1 && get<0>(f[i])-sh[j]<=get<0>(f[j]) && get<0>(f[j])<=get<0>(f[i])+sh[i])
                    return 0;
            }
            if(get<2>(f[i]) == 'H' && get<2>(f[j]) == 'V'){
                if(get<1>(f[i])-1<=get<1>(f[j]) && get<1>(f[j])<=get<1>(f[i])+sh[i] && get<0>(f[j])-1<=get<0>(f[i]) && get<0>(f[i])<=get<0>(f[j])+sh[j])
                    return 0;
            }
            if(get<2>(f[i]) == 'V' && get<2>(f[j]) == 'H'){
                if(get<0>(f[i])-1<=get<0>(f[j]) && get<0>(f[j])<=get<0>(f[i])+sh[i] && get<1>(f[j])-1<=get<1>(f[i]) && get<1>(f[i])<=get<1>(f[j])+sh[j])
                    return 0;
            }
        }
    }
    return 1;
}

int cvr[10][10];
void cv(vector<tuple<int, int, char>> f){
    memset(cvr, 0, sizeof(cvr));
    for(int i = 0; i < 5; i++){
        int r = get<0>(f[i]);
        int c = get<1>(f[i]);
        for(int s = 0; s < sh[i]; s++){
            cvr[r+s*(get<2>(f[i])=='V')][c+s*(get<2>(f[i])=='H')] = 1;
        }
    }
}

int known[5];
vector<tuple<int, int, char>> knownpos(5);
vector<array<array<int, 10>, 10>> mem;
int fastrand(){
    int tmp[12][12]={0};
    vector<tuple<int, int, char>> p;
    for(int si = 0; si < 10; si++){
        int s = sh[si%5];
        int kn = si<5;
        if(kn && !known[si]) continue;
        if(!kn && known[si%5]) continue;
        char dir;
        int r, c;
        int i = 0;
        while(1){
            if(kn){
                tie(r, c, dir) = knownpos[si];
                r++,c++;
            }
            else{
                dir = "HV"[rand()%2];
                if(dir == 'H'){
                    r = rand()%10+1;
                    c = rand()%(11-s)+1;
                }
                else{
                    r = rand()%(11-s)+1;
                    c = rand()%10+1;
                }
            }
            int ok = 1;
            for(int x = 0; x < s; x++){
                ok &= !tmp[r+x*(dir=='V')][c+x*(dir=='H')] && a[r+x*(dir=='V')-1][c+x*(dir=='H')-1] != 1;
                if(dir == 'H'){
                    if(r != 1) ok &= a[r-2][c+x-1] != 2;
                    if(r != 10) ok &= a[r][c+x-1] != 2;
                }
                else{
                    if(c != 1) ok &= a[r+x-1][c-2] != 2;
                    if(c != 10) ok &= a[r+x-1][c] != 2;
                }
            }
            if(kn) assert(ok);
            if(ok) break;
            i++;
            if(i > 50) return 0;
        }
        if(dir == 'H'){
            tmp[r-1][c-1] = -1;
            tmp[r][c-1] = -1;
            tmp[r+1][c-1] = -1;
            tmp[r-1][c+s] = -1;
            tmp[r][c+s] = -1;
            tmp[r+1][c+s] = -1;
            for(int x = 0; x < s; x++){
                int cc = c+x;
                tmp[r][cc] = 1;
                tmp[r-1][cc] = -1;
                tmp[r+1][cc] = -1;
            }
        }
        else{
            tmp[r-1][c-1] = -1;
            tmp[r-1][c] = -1;
            tmp[r-1][c+1] = -1;
            tmp[r+s][c-1] = -1;
            tmp[r+s][c] = -1;
            tmp[r+s][c+1] = -1;
            for(int x = 0; x < s; x++){
                int cr = r+x;
                tmp[cr][c] = 1;
                tmp[cr][c-1] = -1;
                tmp[cr][c+1] = -1;
            }
        }
        p.emplace_back(r, c, dir);
    }
    for(int r = 1; r <= 10; r++) for(int c = 1; c <= 10; c++)
        if(tmp[r][c] == -1) tmp[r][c] = 0;
    for(int r = 0; r < 10; r++){
        for(int c = 0; c < 10; c++){
            if(a[r][c] == 1 && tmp[r+1][c+1] || a[r][c] == 2 && !tmp[r+1][c+1]){
                return 0;
            }
        }
    }
    array<array<int, 10>, 10> t{};
    for(int r = 0; r < 10; r++){
        for(int c = 0; c < 10; c++){
            cnt[r][c] += tmp[r+1][c+1];
            t[r][c] = tmp[r+1][c+1];
        }
    }
    if(mem.size() < 200)
        mem.push_back(t);
    return 1;
}

vector<tuple<int, int, char>> start_game(string opponent, int pnum){
    memset(a, 0, sizeof(a));
    vector<tuple<int, int, char>> f;
    do{
        f = rf();
    } while(!cf(f));
    return f;
}

void find_known(){
    memset(known, 0, sizeof(known));
    for(int r = 0; r < 10; r++){
        for(int c = 0; c < 10; c++){
            if(a[r][c] != 2) continue;
            char dir = 'x';
            if(r != 9 && a[r+1][c] == 2) dir='V';
            else if(c != 9 && a[r][c+1] == 2) dir='H';
            if(dir == 'x') continue;
            int s;
            for(s = 0; r+s*(dir=='V')<10&&c+s*(dir=='H')<10&&a[r+s*(dir=='V')][c+s*(dir=='H')]==2; s++){}
            if(s == 5){
                known[4] = 1;
                knownpos[4] = {r, c, dir};
            }
        }
    }
}

pi s2(){
    memset(cnt, 0, sizeof(cnt));
    int samples = 0;
    clock_t start = clock();
    for(int i = 0; i < (int)mem.size(); i++){
        for(int r = 0; r < 10; r++){
            for(int c = 0; c < 10; c++){
                cnt[r][c] += mem[i][r][c];
            }
        }
        samples++;
    }
    find_known();
    while((clock()-start)/(double)CLOCKS_PER_SEC < 0.4){
        samples += fastrand();
    }
    cout << samples << " samples\n";

    int mx = -1;
    for(int r = 0; r < 10; r++){
        for(int c = 0; c < 10; c++){
            if(!a[r][c])
                mx = max(mx, cnt[r][c]);
                /*
            if(a[r][c] == 1) cout << "x\t";
            else if(a[r][c] == 2) cout << "##\t";
            else cout << cnt[r][c] << "\t";*/
        }
        //cout << "\n";
    }
    int r, c;
    do{
        r = rand()%10;
        c = rand()%10;
    } while(a[r][c] || cnt[r][c]!=mx);

    return {r, c};
}

int sr, sc;
pair<int, int> shoot(){
    tie(sr, sc) = s2();
    return {sr, sc};
}

void result(string r){
    if(r == "miss"){
        a[sr][sc] = 1;
        for(int i = 0; i < (int)mem.size(); i++){
            if(mem[i][sr][sc]){
                mem.erase(mem.begin()+i);
                i--;
            }
        }
    }
    else if(r == "hit"){
        a[sr][sc] = 2;
        for(int i = 0; i < (int)mem.size(); i++){
            if(!mem[i][sr][sc]){
                mem.erase(mem.begin()+i);
                i--;
            }
        }
    }
    else assert(0);
}

void opp_shot(int row, int col){
}

int wins = 0;
int losses = 0;
void game_over(string r){
    if(r == "won"){
        wins++;
        cout << "Jag vann spelet!" << endl;
    }
    else if(r == "lost"){
        losses++;
        cout << "Jag förlorade spelet :(" << endl;
    }
    else assert(0);
    cout << wins << " vinster och " << losses << " förluster" << endl;
}





/////////////////////////////////////////////////////////////////////////

#include <boost/beast/core.hpp>
#include <boost/beast/websocket.hpp>
namespace websocket = boost::beast::websocket;
namespace net = boost::asio;
using tcp = boost::asio::ip::tcp;

vector<string> split(string s){
    vector<string> r;
    string t = "";
    for(char x : s){
        if(x == ' '){
            r.push_back(t);
            t = "";
        }
        else{
            t.push_back(x);
        }
    }
    r.push_back(t);
    return r;
}

vector<int> split_int(string s){
    vector<string> a = split(s);
    vector<int> b;
    for(string x : a) b.push_back(stoi(x));
    return b;
}

string recv(websocket::stream<tcp::socket>& ws){
    boost::beast::flat_buffer buffer;
    ws.read(buffer);
    return boost::beast::buffers_to_string(buffer.cdata());
}

void send(string s, websocket::stream<tcp::socket>& ws){
    ws.write(net::buffer(s));
}

void play_loop()
{
    string host = "localhost";  // byt ut mot serverns ip
    string port = "1234";

    net::io_context ioc;
    tcp::resolver resolver{ioc};
    websocket::stream<tcp::socket> ws{ioc};
    net::connect(ws.next_layer(), resolver.resolve(host, port));
    ws.handshake(host+":"+port, "/");


    send(NAME, ws);
    string r = recv(ws);
    if(r != "ok"){
        cout << r << endl;
        return;
    }
    while(1){
        vector<string> msg = split(recv(ws));
        assert(msg[0] == "play");
        string opponent = msg[1];
        int pnum = stoi(recv(ws));
        vector<tuple<int, int, char>> ships = start_game(opponent, pnum);
        string s = "";
        for(int i = 0; i < (int)ships.size(); i++){
            auto x = ships[i];
            s += to_string(get<0>(x)) + " " +
                 to_string(get<1>(x)) + " " +
                 get<2>(x);
            if(i != (int)ships.size()-1) s += " ";
        }
        send(s, ws);
        string res = recv(ws);
        if(res != "ok" && res != "won" && res != "lost"){
            cout << res << endl;
            return;
        }
        if(res != "lost"){
            cout << "Placering godkänd" << endl;
        }
        int turn = 1;
        while(res != "won" && res != "lost"){
            if(turn == pnum){
                int r, c;
                tie(r, c) = shoot();
                send(to_string(r) + " " + to_string(c), ws);
                res = recv(ws);
                if(res == "won" || res == "lost") break;
                result(res);
            }
            else{
                res = recv(ws);
                if(res == "won") break;
                int r = split_int(res)[0];
                int c = split_int(res)[1];
                res = recv(ws);
                opp_shot(r, c);
            }
            turn ^= 3;
        }
        game_over(res);
    }
}

int main(){
    srand(time(0));
    if(NAME == "")
        NAME = "Player_" + to_string(rand()%900+100);
    while(1){
        try{
            play_loop();
        }
        catch(const exception& e){
            cout << e.what() << endl;
        }
        cout << "\n\nConnection lost. Retrying in 10s..." << endl;
        sleep(10);
    }
}