#include <winsock2.h>

#include <ws2tcpip.h>

#include <string>

#include <iostream>

#include <thread>

#include <atomic>

#include <chrono>



#define NODLLEXPORT

#include "vdjPlugin8.h"



static const GUID IID_IVdjPluginDsp8_Local = { 0x7cfcf3f5, 0x6fb9, 0x434c, { 0xb6, 0x03, 0xd7, 0x3a, 0x88, 0xf6, 0x72, 0x26 } };



class IVdjPluginDsp8 : public IVdjPlugin8 {

public:

    virtual HRESULT VDJ_API OnStart() {return S_OK;}

    virtual HRESULT VDJ_API OnStop() {return S_OK;}

    virtual HRESULT VDJ_API OnProcessSamples(float *buffer, int nb) = 0;



    int SampleRate;

    int SongBpm;

    double SongPosBeats;

};



class FariaLightFXPlugin : public IVdjPluginDsp8 {

private:

    std::atomic<double> currentBeatPos;

    SOCKET udpSocket;

    sockaddr_in serverAddr;

    bool socketReady;

    

    std::thread workerThread;

    std::atomic<bool> stopThread;



    std::string escapeJsonString(const std::string& input) {

        std::string output;

        for (char c : input) {

            if (c == '\\') output += "\\\\";

            else if (c == '"') output += "\\\"";

            else output += c;

        }

        return output;

    }



    std::string doubleToStr(double val) {
        char buf[64];
        snprintf(buf, sizeof(buf), "%f", val);
        std::string s(buf);
        for(char& c : s) if(c == ',') c = '.';
        return s;
    }



    void TimerLoop() {

        while (!stopThread.load()) {

            if (socketReady && cb) {

                double isPlaying = 0;

                double bpm = 0;

                double lengthMs = 0;

                double timeMs = 0;

                double beatPos = currentBeatPos.load();



                cb->GetInfo("play", &isPlaying);

                if (cb->GetInfo("get_bpm", &bpm) != S_OK || bpm <= 0) cb->GetInfo("bpm", &bpm);

                // Recupera o tempo exato em milissegundos
                cb->GetInfo("get_time elapsed", &timeMs);
                cb->GetInfo("get_time total", &lengthMs); 



                char filepath[1024] = {0};

                cb->GetStringInfo("get_filepath", filepath, sizeof(filepath));



                double pluginDeck = 0;

                cb->GetInfo("get_plugindeck", &pluginDeck);

                

                double pitch = 0;

                cb->GetInfo("get_pitch", &pitch);

                

                double volume = 0;

                if (cb->GetInfo("volume", &volume) != S_OK) volume = 1.0;

                

                double crossfader = 0.5;

                if (cb->GetInfo("crossfader", &crossfader) != S_OK) crossfader = 0.5;

                

                double eq_low_1 = 0.5;

                HRESULT hr1 = cb->GetInfo("deck 1 eq_low", &eq_low_1);

                

                double eq_low_2 = 0.5;

                HRESULT hr2 = cb->GetInfo("deck 2 eq_low", &eq_low_2);

                

                double filter_1 = 0.5;

                cb->GetInfo("deck 1 filter", &filter_1);

                



                std::string safePath = escapeJsonString(std::string(filepath));

                

                // Se safePath for vazio, manda tambem! Python filtra!

                std::string payload = "{\"track\":\"" + safePath + "\",\"pos\":" + std::to_string((int)timeMs) + 

                                      ",\"beat\":" + doubleToStr(beatPos) + 

                                      ",\"play\":" + (isPlaying > 0.5 ? "true" : "false") + 

                                      ",\"bpm\":" + doubleToStr(bpm) + 

                                      ",\"length_ms\":" + std::to_string((int)lengthMs) + 

                                      ",\"deck\":" + std::to_string((int)pluginDeck) + 

                                      ",\"pitch\":" + doubleToStr(pitch) + 

                                      ",\"vol\":" + doubleToStr(volume) + 

                                      ",\"cross_result\":" + doubleToStr(crossfader) + ",\"eq_low_1\":" + doubleToStr(eq_low_1) + ",\"eq_low_2\":" + doubleToStr(eq_low_2) + "}";



                sendto(udpSocket, payload.c_str(), payload.length(), 0, (struct sockaddr*)&serverAddr, sizeof(serverAddr));

            }

            std::this_thread::sleep_for(std::chrono::milliseconds(33)); // 30 FPS

        }

    }



public:

    FariaLightFXPlugin() : udpSocket(INVALID_SOCKET), socketReady(false), stopThread(false) {
        currentBeatPos.store(0.0);
    }



    virtual ~FariaLightFXPlugin() {

        stopThread.store(true);

        if (workerThread.joinable()) {

            workerThread.join();

        }

        if (socketReady) {

            closesocket(udpSocket);

            WSACleanup();

        }

    }



    HRESULT VDJ_API OnLoad() override {

        WSADATA wsaData;

        if (WSAStartup(MAKEWORD(2, 2), &wsaData) == 0) {

            udpSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

            if (udpSocket != INVALID_SOCKET) {

                u_long mode = 1;

                ioctlsocket(udpSocket, FIONBIO, &mode);

                serverAddr.sin_family = AF_INET;

                serverAddr.sin_port = htons(9666);

                inet_pton(AF_INET, "127.0.0.1", &serverAddr.sin_addr);

                socketReady = true;

            }

        }

        workerThread = std::thread(&FariaLightFXPlugin::TimerLoop, this);

        return S_OK;

    }



    HRESULT VDJ_API OnGetPluginInfo(TVdjPluginInfo8* infos) override {

        infos->PluginName = "FariaFX";

        infos->Author = "JBLController";

        infos->Description = "Faria Light Sincronizador v5";

        infos->Version = "5.0";

        infos->Flags = 0;

        return S_OK;

    }



    HRESULT VDJ_API OnStart() override { return S_OK; }

    HRESULT VDJ_API OnStop() override { return S_OK; }

    HRESULT VDJ_API OnProcessSamples(float *buffer, int nb) override { 
        currentBeatPos.store(this->SongPosBeats);
        return S_OK; 
    }



    ULONG VDJ_API Release() override {

        delete this;

        return S_OK;

    }

};



STDAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, LPVOID* ppObject) {

    if (memcmp(&rclsid, &CLSID_VdjPlugin8, sizeof(GUID)) == 0 &&

        memcmp(&riid, &IID_IVdjPluginDsp8_Local, sizeof(GUID)) == 0)

    {

        *ppObject = new FariaLightFXPlugin();

        return S_OK;

    }

    return CLASS_E_CLASSNOTAVAILABLE;

}

