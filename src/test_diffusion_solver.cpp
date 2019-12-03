#include <iostream> //For console output/input
#include <fstream>  //Allows to read/write files 
#include <math.h>   //Basic mathematic functions 
#include <vector>   //For dynamic arrays 
#include <string>   //Operations on strings 
#include <tuple>
#include <cmath>
#include <sstream>
#include <ctime>
#include <chrono>
#include <thread>
#include <sys/resource.h>
#include <omp.h>
using namespace std;


#include "./mathematics.h"
#include "./constants.h"
#include "./read2D.h"
#include "./freader.h"
#include "./fwritter.h"
#include "./out.h"
#include "./logmaker.h"
#include "./tools.h"
#include "./solver1D.h"
#include "./cr_source.h"

// Main function 
int main()
{

    std::clock_t start;
    double duration;
/*
    // Script which defines the limit memory (here 64 MB)
    const rlim_t kStackSize = 64 * 1024 * 1024; 
    struct rlimit rl;
    int result;

    result = getrlimit(RLIMIT_STACK, &rl);
    if (result == 0)
    {
        if (rl.rlim_cur < kStackSize)
        {
            rl.rlim_cur = kStackSize;
            result = setrlimit(RLIMIT_STACK, &rl);
            if (result != 0)
            {
                fprintf(stderr, "setrlimit returned result = %d\n", result);
            }
        }
    }
    //--------------------------------------------------------//
    */

    /*std::string parameters = "./parameters.dat";
    std::string snx = search(parameters, "NX"); int nx = stoi(snx);
    std::string sne = search(parameters, "NE"); int ne = stoi(sne);
    std::string sni = search(parameters,"ni");        double ni = stod(sni);
    std::string sX  = search(parameters,"X");         double Xi = stod(sX); 
    double nt = ni/Xi;
    std::string smn = search(parameters,"mn");        double m_neutral = stod(smn); 
    std::string sT   = search(parameters,"T");        double T  = stod(sT);*/

    


    //cout<<"DIMENSION = "<<DIMENSION<<endl;
    cout<<"NX = "<<nx<<endl;
    cout<<"NE = "<<ne<<endl;
    //cout<<"GRID = "<<GRID<<endl;


    // We get the initial conditions in the ISM
    vector<vector<double>> rVA  = parse2DCsvFile("./data_ini/Alfven.dat", 1);
    vector<vector<double>> rDb  = parse2DCsvFile("./data_ini/DBohm.dat", 1);
    vector<vector<double>> rIp  = parse2DCsvFile("./data_ini/Ip.dat", 1);
    vector<vector<double>> rPcr = parse2DCsvFile("./data_ini/Pcr.dat",1);
    vector<vector<double>> rGd  = parse2DCsvFile("./data_ini/damping.dat",1);





    //We prepare some informations in order to read our input data 
    int NX = pow(2, nx);
    int NE = pow(2, ne); 
    int index_emin = 2; 
    int index_emax = index_emin + NE;

    vector<double> X = readAxis("X", NX);
    vector<double> E = readAxis("E", NE);

    vector<double> log10E = E;
    for (int ei = 0; ei < E.size(); ei++)
    {
        log10E[ei] = log10(E[ei]);
    }

    vector<double> B = readAxis("B", NX);



    vector<vector<double>> VA(NX), Db(NX), Ip(NX), Pcr(NX), Gd(NX); 
    for (int xi = 0; xi < NX; xi++)
    {
        VA[xi].resize(NE); 
        Db[xi].resize(NE);
        Ip[xi].resize(NE);
        Pcr[xi].resize(NE);
        Gd[xi].resize(NE);
    }

    for (int xi = 0; xi < NX; xi++)
    {
        for (int ei = 0; ei < NE; ei++)
        {
            VA[xi][ei]  = rVA[xi][index_emin + ei]; 
            Db[xi][ei]  = rDb[xi][index_emin + ei];
            Ip[xi][ei]  = rIp[xi][index_emin + ei]; 
            Pcr[xi][ei] = rPcr[xi][index_emin + ei];
            Gd[xi][ei]  = rGd[xi][index_emin + ei];
            //cout<<"Db["<<xi<<", "<<ei<<"] = "<<Db[xi][ei]<<endl;
        }
    }


    // Initialisation des vecteurs de variance d'espace 
    vector<double> dX(NX), dE(NE); 
    for (int xi=1; xi<NX-1; xi++){dX[xi] = 0.5*abs(X[xi+1] - X[xi-1]);}
    dX[0] = dX[1]; dX[NX-1] = dX[NX-2]; 
    for (int e=1; e<NE-1; e++){dE[e] = 0.5*abs(log10E[e+1] - log10E[e-1]);}
    dE[0] = dE[1]; dE[NE-1] = dE[NE-2];

    // CFL Conditions 
    double C1 = 0.5;
    double C2 = 0.5;
    double C3 = 0.5;
    double C4 = 0.5;
    double C5 = 0.5;

    vector<double> Vdminvec(NE), Dminvec(NE), Gammadminvec(NE);

    vector<vector<double>> abs_VA = VA, dVAdlog10E = VA, cdVAdX = VA, c2dVAdX = VA;
    for (int xi = 0; xi < VA.size(); xi++)
    {
        for (int ei = 0; ei < VA[xi].size(); ei++)
        {
            abs_VA[xi][ei] = abs(VA[xi][ei]);
            if (ei > 0 and ei < VA[xi].size()-1)
            {
                dVAdlog10E[xi][ei] = -1./3*1./log(10)*(VA[xi][ei+1] - VA[xi][ei-1])/(log10E[ei+1] - log10E[ei-1]);
            }
            if (xi > 0 and xi < VA.size()-1)
            {
                cdVAdX[xi][ei] = (VA[xi+1][ei] - VA[xi-1][ei])/(X[xi+1] - X[xi-1])/(3.*log(10.)); //1e-11 -> Test value
                c2dVAdX[xi][ei] = -(VA[xi+1][ei] - VA[xi-1][ei])/(X[xi+1] - X[xi-1])*1.25;
            }
            cdVAdX[0][ei] = cdVAdX[1][ei];
            cdVAdX[VA.size()-1][ei] = cdVAdX[VA.size()-2][ei];
            c2dVAdX[0][ei] = c2dVAdX[1][ei];
            c2dVAdX[VA.size()-1][ei] = c2dVAdX[VA.size()-2][ei];
        }
        dVAdlog10E[xi][0] = 0.;
        dVAdlog10E[xi][VA[xi].size()-1] = 0.;

    }


    double maxE  = maxElement1D(log10E);
    double minW0 = minElement1D(B); minW0 = pow(minW0,2)/(8*pi);
    double maxVd = maxElement2D(abs_VA);
    double maxDb = maxElement2D(Db);
    double minIp = minElement2D(Ip);
    double maxD  = maxDb/minIp;// cout<<"Max D = "<<maxD<<endl;
    double maxGd = maxElement2D(Gd);
    double mindX = minElement1D(dX); double mindE = minElement1D(dE); 

    vector<double> cfl;
    cfl.push_back(C1*mindX/maxVd); 
    //cfl.push_back(C2*pow(mindX,2)/maxD);
    cfl.push_back(C3*mindE*mindX/(maxE*maxVd));
    cfl.push_back(C4*2*mindX/maxVd);
    //cfl.push_back(C5/maxGd);

    cout<<"CFL Values : "<<endl;
    cout<<"Advection : "<<C1*mindX/maxVd<<" s"<<endl;
    cout<<"Diffusion : "<<C2*pow(mindX,2)/maxD<<" s"<<endl;
    cout<<"Energy    : "<<C3*mindE*mindX/(maxE*maxVd)<<" s"<<endl;
    cout<<"Growth    : "<<C4*2*mindX/maxVd<<" s"<<endl;
    cout<<"Damping   : "<<C5/maxGd<<" s"<<endl;
    double dt = minElement1D(cfl);
    cout<<"Time-step = "<<dt<<" s"<<endl;


    // SIMULATION
    double Tmax = setTmax();
    double time = 0.;
    int time_index = 0;
    vector<double> dat_output = getOutput();

    int out_Pcr_index = 0;
    int out_Ip_index = 0;

    vector<vector<double>> Pcr_new, Pcr_old, Ip_new, Ip_old, Pcr_background, Ip_background;
    vector<vector<double>> Pcr_temp;

    Pcr_new = Pcr; Ip_new  = Ip; Pcr_background = Pcr, Ip_background = Ip;

    double box_Pcr[5][5], box_Ip[5][5], box_VA[5][5], box_Gd[5][5], box_Db[5][5], box_X[5], box_E[5]; 
    int loc_xi, loc_ei;
    int lxi, lei;
    double P1, P2, Ip1, Ip2;
    double Pcr_new_temp, Ip_new_temp;
    double Pcr_background_temp, Ip_background_temp, B_temp, Qcrs_temp, dX_temp, dE_temp, E_temp;
    int ei_temp, xi_temp, t_NX = NX, t_NE = NE;
    int xi_box, ei_box;
    double Qwaves;

    vector<double> Finj_temp(NE); 
    vector<double> Pcr_ini_temp(NE); 
    vector<double> ttesc(NE), norm_pcr(NE);
    vector<vector<double>> t_Pcr;
    vector<double> vec_theta(NX);
    double temp_theta, r_snr;


    for (int j=0; j<NE; j++)
    {
        Pcr_ini_temp[j] = Pcr_ini(E[j]);
        ttesc[j] = tesc(E[j]);
        //cout<<Pcr_ini_temp[j]<<endl;
    }



    int xi, ei; 
    int nb = nproc;
    int g;

    while (time < Tmax)
    {   
        start = std::clock();

        Pcr_old = Pcr_new;
        //cout<<"Hello"<<endl;
        Ip_old  = Ip_new;

        for (g=0; g<NE; g++)
        {
            Finj_temp[g] = Finj(time, dt, E[g], ttesc[g]);
        }
        for (g=0; g<NX; g++)
        {
            vec_theta[g] = theta(X[g], time, r_snr);
        }

        r_snr = RSNR(time);

        
        //----------------------------------------------------------------------//
        // This solver do nothing, just lose your time                          //
        //----------------------------------------------------------------------//
        //NotMove(Ip_old, Ip_new);


        //----------------------------------------------------------------------//
        // Spatially variable diffusion solver, implicit scheme for Pcr         //
        //----------------------------------------------------------------------//
        //thetaDiffusionSolver(Pcr_old, Pcr_new, dt, X, NE, Ip_new, Db, Pcr_background); Pcr_old = Pcr_new;


        //----------------------------------------------------------------------//
        // Explicit Advection solver for Pcr by Alfvén velocity                 //
        //----------------------------------------------------------------------//
        //advectionSolverX(Pcr_old, Pcr_new, dt, X, NE, VA); Pcr_old = Pcr_new;


        //----------------------------------------------------------------------//
        // Explicit Advection solver for Pcr by the energy derivative of        //
        // Alfvén velocity. Which seems to have no effects on the diffusion     //
        // Note : This term needs more studies ...                              //
        //----------------------------------------------------------------------//
        //advectionSolverX(Pcr_old, Pcr_new, dt, X, NE, dVAdlog10E); Pcr_old = Pcr_new;

        //----------------------------------------------------------------------//
        // Explicit Advection solver for Pcr in energy cdVAdX
        // This value needs to be studied more in details 
        //----------------------------------------------------------------------//
        //advectionSolverE(Pcr_old, Pcr_new, dt, log10E, NX, cdVAdX, Pcr_background); Pcr_old = Pcr_new;

        //----------------------------------------------------------------------//
        // Source term effect due to the dependance of the Alfvén velocity to   //
        // the space                                                            //
        //----------------------------------------------------------------------//
        //sourceSolver(Pcr_old, Pcr_new, dt, c2dVAdX, 1.); Pcr_old = Pcr_new;

        //----------------------------------------------------------------------//
        // CRs injection term from SNRs                                         // 
        //----------------------------------------------------------------------//
        //theta(X[xi], time, r_snr)
        // temp_theta*Finj_temp[ei]*Pcr_ini_temp[ei];
        CRsInjectionSourceSolver(Pcr_old, Pcr_new, dt, Pcr_ini_temp, Finj_temp, vec_theta); Pcr_old = Pcr_new; 




        //cout<<"size New = "<<Pcr_new[0].size()<<", size Old = "<<Pcr_old[0].size()<<endl;

        //NotMove(Pcr_old, Pcr_new);
        
        
        //cout<<"0 - "<<Pcr_new.size()<<endl;
        //cout<<"1 - "<<Pcr_new[0].size()<<endl;

        //implicitDiffusion(Pcr_old, Pcr_new, dt, X, Ip_new, Db);





        //------------------------------------------------------------------------------------------------------------//
        /*for (xi = 0; xi<NX; xi++)
        {

            temp_theta = theta(X[xi], time, r_snr);
            //temp_theta = vec_theta[xi];

            
            //temp_theta = Pcr_old[xi][ei]/maxElement1D(Pcr_old);
            for (ei = 0; ei<NE; ei++)
            {

                //We load all the values we need 
                dX_temp = dX[xi];
                dE_temp = dE[ei];
                E_temp = E[ei];
                B_temp = B[xi];
                Pcr_background_temp = Pcr_background[xi][ei];
                Ip_background_temp = Ip_background[xi][ei];
                for (lxi = 0; lxi < 5; lxi++)
                {
                    for (lei = 0; lei < 5; lei++)
                    {   

                        if (xi-2+lxi >= 0 and xi+2+lxi < NX){xi_box = xi-2+lxi;}
                        if (xi-2+lxi < 0)                   {xi_box = 0;}          //Absorbing left layer 
                        if (xi+2+lxi >= NX)                 {xi_box = NX-1;}       //Absorbing right layer 
                        if (ei-2+lei >= 0 and ei+2+lei < NE){ei_box = ei-2+lei;}
                        if (ei-2+lei < 0)                   {ei_box = 0;}          //Absorbing low energy layer 
                        if (ei+2+lei >= NE)                 {ei_box = NE-1;}       //Absorbing high energy layer 
                                box_Pcr[lxi][lei] = Pcr_old[xi_box][ei_box];
                                box_Ip[lxi][lei]  = Ip_old[xi_box][ei_box]; 
                                box_VA[lxi][lei]  = VA[xi_box][ei_box]; 
                                box_Gd[lxi][lei]  = Gd[xi_box][ei_box]; 
                                box_Db[lxi][lei]  = Db[xi_box][ei_box];
                        box_E[lei] = E[ei_box];
                    }
                    box_X[lxi] = X[xi_box];
                }
                    // EQ. Solving 
                    Qwaves = box_Gd[2][2]*box_Ip[2][2];
                    Qcrs_temp = temp_theta*Finj_temp[ei]*Pcr_ini_temp[ei];

                    //if (time_index == 0){Qcrs_temp = temp_theta*Finj_temp[ei]*Pcr_ini_temp[ei];}
                    


                    Pcr_new_temp = pressureSolver(dt, dX_temp, dE_temp, box_Pcr, box_Ip, box_VA, box_Gd, box_Db, E_temp, Qcrs_temp);
                    Ip_new_temp  = wavesSolver(dt, dX_temp, dE_temp, box_Pcr, box_Ip, box_VA, box_Gd, box_Db, B_temp, Qwaves);

                    if (Pcr_new_temp < Pcr_background_temp) {Pcr_new_temp = Pcr_background_temp;}
                    if (Ip_new_temp < Ip_background_temp) {Ip_new_temp = Ip_background_temp;}

                    if (xi == 0){Pcr_new_temp = Pcr_old[xi+1][ei]; Ip_new_temp = Ip_old[xi+1][ei];}
                    if (xi == NX-1){Pcr_new_temp = Pcr_new[xi-1][ei]; Ip_new_temp = Ip_new[xi-1][ei];}

                    //if (time_index > 0){Qcrs_temp = temp_theta*Finj_temp[ei]*Pcr_ini_temp[ei];}

                Pcr_new[xi][ei] = Pcr_new_temp;
                Ip_new[xi][ei]  = Ip_new_temp;
            }
            
        }*/

        if (time > dat_output[out_Pcr_index] && out_Pcr_index < dat_output.size()) 
        {
            out_Ip_index  = writeXE("Ip", out_Ip_index, Ip_new, NX, NE);
            out_Pcr_index = writeXE("Pcr", out_Pcr_index, Pcr_new, NX, NE);
        }

        
        duration = ( std::clock() - start ) / (double) CLOCKS_PER_SEC;
        duration = duration / nb;
        showLog_0(time, Tmax, getLogOutput(), time_index, duration);
        time += dt;
        time_index += 1;

    }
}
