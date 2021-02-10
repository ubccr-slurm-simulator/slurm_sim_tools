#include <iostream>
#include <cstdlib>
#ifdef _WIN32
#include <Windows.h>
#else
#include <unistd.h>
#endif
using namespace std;

int main(int argc,char *args[]){
   if(argc < 2){
        cerr<<"Not enough arguments"<<endl;
        exit(1);
   }
   else{
        cout<<"Sleep for "<< atoi(args[1])<<" seconds "<<endl;
        sleep(atoi(args[1]));
        cout<<"Waking up"<<endl;
   }
   return 0;
}