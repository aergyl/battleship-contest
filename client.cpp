#include <cassert>
#include <iostream>
#include <string>
#include <tuple>
#include <vector>
#include <memory>
using namespace std;

string NAME = "";

vector<tuple<int, int, char>> start_game(string opponent, int pnum){
    cout << "Spelar mot " << opponent << endl;
    cout << "Jag är spelare " << pnum << endl;

    // Lista med skepp i ordningen 2,3,3,4,5
    // (rad, kolumn, riktning)
    // Koordinater är för översta/vänstra hörnet
    // 'H' = horisontell, 'V' = vertikal
    return {
        {1, 1, 'H'},  // 2
        {1, 4, 'H'},  // 3
        {3, 1, 'V'},  // 3
        {3, 3, 'H'},  // 4
        {5, 3, 'H'},  // 5
    };
}

pair<int, int> shoot(){
    int row = rand()%10;
    int col = rand()%10;
    cout << "Jag skjuter på " << row << " " << col << "." << endl;
    return {row, col};
}

void result(string r){
    if(r == "miss"){
        cout << "Jag missade." << endl;
    }
    else if(r == "hit"){
        cout << "Jag träffade!" << endl;
    }
    else if(r == "sunk"){  // bara om det är påslaget
        cout << "Jag träffade och sänkte!" << endl;
    }
    else assert(0);
}

void opp_shot(int row, int col){
    cout << "Motståndaren sköt på " << row << " " << col << "." << endl;
}

void game_over(string r){
    if(r == "won"){
        cout << "Jag vann spelet!" << endl;
    }
    else if(r == "lost"){
        cout << "Jag förlorade spelet :(" << endl;
    }
    else assert(0);
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
#ifdef _WIN32
        Sleep(10000);
#else
        sleep(10);
#endif
    }
}