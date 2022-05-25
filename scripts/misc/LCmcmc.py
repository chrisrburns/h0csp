import sys
import numpy as np
from numpy import matrix
import emcee
import astropy.io.fits as pyfits
import matplotlib.pylab as pl
import corner
import random,os
from astropy.cosmology import FlatLambdaCDM
import pandas as pd
from scipy import optimize
from multiprocessing import Pool
from multiprocessing import cpu_count
import time
from astropy.io import ascii

ncpu = cpu_count()
print("{0} CPUs".format(ncpu))

os.environ["OMP_NUM_THREADS"] = "1"

# Speed of light
c = 300000.
#Decelration parameter
q=-0.53


#tab = ascii.read('../data/working/B_ceph.csv')
#tab = ascii.read('data/CSPI_Burns2018.dat')
file = sys.argv[1]
tab = ascii.read('../../data/working/'+file)

#w = np.where((tab['subtype']!='Ia-91T') & (tab['subtype']!='Ia-91bg')) # sample selection

w = tab['caltype']!='none'


f1 =open('../../results/'+file[:-4]+'_result_allcal.txt','w')


Ho_dists = tab['dist'][w] < 0
st = tab['st'][w]
est = tab['est'][w]
zhel = tab['zhel'][w]
zcmb = tab['zcmb'][w]
mmax = tab['Mmax'][w]
emmax = tab['eMmax'][w]
bv = tab['BV'][w]
ebv = tab['eBV'][w]
m_csp = tab['m'][w]
dist = tab['dist'][w]
edist = tab['edist'][w]
c_ms = tab['covMs'][w]
c_mbv = tab['covBV_M'][w]

print (len(st))

#initial guess
plim=-18.9, -18.8
p1lim =-1.2,-1.1
p2lim=-.055,-0.05
rvlim =2.7,2.71
alphalim=-0.11,-0.1
siglim=0.1,.12
vellim =300.,310
h0lim= 71.0,71.1

# Eqn 9 of Bruns 2018
def distmod(h,z1,z2): # z1=zhel, z2=zcmb
    t1 = (1+z1)/(1+z2)
    t2 = (c*z2)/h
    t3 = 1 + (((1-q)/2)*z2)
    return 5*np.log10(t1*t2*t3) +25

# Liklihood function
def like(par):
    p1,p2,rv,sig,vel = par
    if  -10.0<p1<10.0 and -10.0<p2<10.0 and 0.<rv<10.0 and 0.<sig<1. and 0.<vel<1000.:

        mu_obs = mmax -19.0- p1*(st - 1.) -  p2*(st - 1.)**2 - rv*bv 
        #mu_obs = mmax - p - p1*(st - 1.) -  p2*(st - 1.)**2 - rv*bv - (alpha*m_csp) # slope 


        mu_model = np.where(Ho_dists, distmod(72.0,zhel,zcmb), dist)
        fac= (p1+(2*p2*st))
        velterm = (2.17*vel)**2/(c*zcmb)**2
        err = (fac*est)**2 +emmax**2 +(rv*ebv)**2+2*fac*c_ms+rv*c_mbv+sig**2+(0.00000723*vel/zcmb)**2
        err1 = ((fac*est)**2) +(emmax**2) +((rv*ebv)**2)+(2*fac*c_ms)+(rv*c_mbv)+(edist**2)
        
        mu_stat = np.where(Ho_dists,err,err1)
        
      
        mu_stat=np.sqrt(mu_stat)
        dmu=mu_obs-mu_model
        
        chi =np.sum((dmu)**2/mu_stat**2)
        return -0.5*chi - (0.5*np.sum(np.log(2*np.pi*(mu_stat)**2))) 
    else:
        return -np.inf
          
# EMCEE  
ndim, nwalkers =5, 50
ssize=1000
burnin =200   


p00 = np.random.rand(nwalkers) * (plim[1] - plim[0]) + plim[0]
p10 = np.random.rand(nwalkers) * (p1lim[1] - p1lim[0]) + p1lim[0]
p20 = np.random.rand(nwalkers) * (p2lim[1] - p2lim[0]) + p2lim[0]
rv0 = np.random.rand(nwalkers) * (rvlim[1] - rvlim[0]) + rvlim[0]
alpha0 = np.random.rand(nwalkers) * (alphalim[1] - alphalim[0]) + alphalim[0]
sig0 = np.random.rand(nwalkers) * (siglim[1] - siglim[0]) + siglim[0]
vel0 = np.random.rand(nwalkers) * (vellim[1] - vellim[0]) + vellim[0]
h00 = np.random.rand(nwalkers) * (h0lim[1] - h0lim[0]) + h0lim[0]

#p0 = zip(*[p00,p10,p20,rv0,alpha0,sig0,vel0])
p0 = np.array([p10,p20,rv0,sig0,vel0]).T


sampler = emcee.EnsembleSampler(nwalkers, ndim, like)
print ("running mcmc..")
start = time.time()
sampler.run_mcmc(p0,ssize,progress=True)
samples = sampler.chain[:, burnin:, :].reshape((-1, ndim))
end = time.time()
serial_time = end - start


# Chains
fig, axes = pl.subplots(5, figsize=(10, 7), sharex=True)
samples = sampler.get_chain()
labels = ["$P1$", "$P2$", r"$\beta$", r"$\sigma_{int}$","$V_{pec}$"]
for j in range(ndim):
    ax = axes[j]
    ax.plot(samples[:, :, j], "k", alpha=0.3)
    ax.set_xlim(0, len(samples))
    ax.set_ylabel(labels[j])
    ax.yaxis.set_label_coords(-0.1, 0.5)

axes[-1].set_xlabel("step number")

fig.savefig("../../plots/steps_allcal.pdf")

samples = sampler.chain[:, burnin:, :].reshape((-1, ndim))


 # Printing results
p1_mcmc,p2_mcmc,rv_mcmc,sig_mcmc,vel_mcmc = map(lambda v: (v[1], v[2]-v[1], v[1]-v[0]),
                             zip(*np.percentile(samples, [16, 50, 84],
                                                axis=0)))


print("""MCMC result:
    P1 = {0[0]} +{0[1]} -{0[2]} 
    P2 = {1[0]} +{1[1]} -{1[2]} 
    Beta = {2[0]} +{2[1]} -{2[2]}
    Sigma = {3[0]} +{3[1]} -{3[2]}
    Vpec = {4[0]} +{4[1]} -{4[2]}

   
""".format(p1_mcmc, p2_mcmc,rv_mcmc,sig_mcmc,vel_mcmc))





#f1.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\n'%('p1','p2','beta','sig_int','vel'))

#f1.write('%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\n'%(p0_mcmc[0],p1_mcmc[0],p2_mcmc[0],rv_mcmc[0],alpha_mcmc[0],sig_mcmc[0],vel_mcmc[0]))

#f1.write('%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\n'%(p0_mcmc[1],p1_mcmc[1],p2_mcmc[1],rv_mcmc[1],alpha_mcmc[1],sig_mcmc[1],vel_mcmc[1]))
#f1.write('%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\n'%(p0_mcmc[2],p1_mcmc[2],p2_mcmc[2],rv_mcmc[2],alpha_mcmc[2],sig_mcmc[2],vel_mcmc[2]))

f1.close()


# Triangle plot
figure = corner.corner(samples,labels=["$P1$", "$P2$", "$R_V$", r"$\sigma_{int}$","$V_{pec}$"],quantiles=[0.16, 0.5, 0.84],truths=[p1_mcmc[0],p2_mcmc[0],rv_mcmc[0],sig_mcmc[0],vel_mcmc[0]],show_titles=True)

figure.savefig("../../plots/mcmcH0_allcal.pdf")



#pl.hist(samples[:, 4], 500, color="k", histtype="step")
#pl.savefig("H0.pdf")


print ("Mean acceptance fraction:", np.mean(sampler.acceptance_fraction))
print("Serial took {0:.1f} minutes".format(serial_time/60.))


    












