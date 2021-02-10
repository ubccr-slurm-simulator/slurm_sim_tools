#include <iostream>
#include <vector>
#include <cstdlib>
#include <stdint.h>
#include <random>
#include <chrono>
#include <thread>
#include <unistd.h>
using namespace std;


void sleep(int sleepSeconds){
    cout << "Sleep\n";
    this_thread::sleep_for (std::chrono::seconds(sleepSeconds));
    return;
}

void printMatrix(vector<double>&matrix, int stride){
    for (int i = 0; i < matrix.size(); i++) {
        if (i %  stride== 0) {
            cout<<endl;
        }
        cout<<matrix[i];
    }
}

void mulitilicationHelper(vector<double> &matrix,int n){
    vector<double>temp = matrix;
    //cout<<"temp is :"<<temp[0]<<" "<<temp[1]<<endl;
    for(int i = 0; i < n; i++){
        for(int j = 0; j< n; j++){
            double sum = 0;
            #pragma simd
            for(int k = 0;k<n;k++){
                sum += temp[i * n + k] * temp[k * n + j];
            }
            matrix[i*n+j] = sum;
        }
    }
}

void multiplication(vector<double> &matrix, int n, int calcSeconds){
    cout << "Calculate\n";
    auto start = std::chrono::high_resolution_clock::now();
    int64_t calcSum = 0; // floating point calculation
    while(true){
        mulitilicationHelper(matrix, n);
        calcSum ++;
        // runing time is up, put to sleep
        if((std::chrono::high_resolution_clock::now()- start) >= std::chrono::seconds(calcSeconds)){
            //cout<<"Running time is up, " << "sleeping"<<endl;
            break;
        }
    }
    auto end = std::chrono::high_resolution_clock::now();
    cout<<"FLOPS: "<< 2.0*calcSum*n*n*n / calcSeconds <<endl;
}

int grow(int mib_per_second, int grow_seconds){
    cout << "Grow\n";
    int elements_mib_per_second = 4 * mib_per_second * 1024 * 1024;
    vector<int*> allocated_arrays;

    auto start = std::chrono::high_resolution_clock::now();
    int64_t calcSum = 0;
    while(true){
        int * new_array = new int[elements_mib_per_second];
        for(int j=0;j<elements_mib_per_second;j++) {
            new_array[j]=j%1024;
        }
        allocated_arrays.push_back(new_array);
        calcSum += new_array[0];
        this_thread::sleep_for (std::chrono::seconds(1));
        // runing time is up, put to sleep
        if((std::chrono::high_resolution_clock::now()- start) >= std::chrono::seconds(grow_seconds)){
            //cout<<"Running time is up, " << "sleeping"<<endl;
            break;
        }
    }
    for(int k=0; k<allocated_arrays.size(); k++) {
        delete [] allocated_arrays[k];
    }
    return calcSum;
}

int main(int argc, char*args[]){
    if(argc < 4){
        cout<<"Required <matrix size> <rough seconds to calculate> <mib_per_second> <grow seconds> <sleep in seconds>"<<endl;
        cerr<<"Not enough arguments"<<endl;
        exit(0);
    }
    int n = atoi(args[1]);
    int calcSeconds = atoi(args[2]);
    int mib_per_second = atoi(args[3]);
    int grow_seconds = atoi(args[4]);
    int sleepSeconds = atoi(args[5]);

    cout<<"n="<<n<<"\n";
    cout<<"calcSeconds="<<calcSeconds<<"\n";
    cout<<"mib_per_second="<<mib_per_second<<"\n";
    cout<<"grow_seconds="<<grow_seconds<<"\n";
    cout<<"sleepSeconds="<<sleepSeconds<<"\n";

    vector<double> matrix(n * n,1);
    double timeCounter = 0;

    //generate random inital sleep time
    srand(time(NULL));
    int initSleepTime = (rand() % sleepSeconds)+1;
    //sleep(sleepSeconds);
    //cout<<"Initial sleep is over, begin multiplcation"<<endl;

    //working stage
    while(true){
        multiplication(matrix, n, calcSeconds);
        grow(mib_per_second, grow_seconds);
        sleep(sleepSeconds);
        for(auto elem : matrix) elem = 1;

    }

    return 0;
}