import sys
import numpy as np
from numpy import matrix
import emcee
import astropy.io.fits as pyfits
import matplotlib.pylab as pl
import triangle
import random,os
from astropy.cosmology import FlatLambdaCDM
from scipy import optimize
from multiprocessing import Pool
from multiprocessing import cpu_count
import time
from astropy.io import ascii
from astropy.table import Table
c = 300000. # km/sec
q=-0.59 # decelertion parameter


# Eqn 9 of Bruns 2018
def distmod(h,z1,z2):
    t1 = (1+z1)/(1+z2)
    t2 = (c*z2)/h
    t3 = 1 + ((1-q)*z1/2)
    return (5*np.log10(t1*t2*t3)) +25

# Getting results
pl.figure(figsize=(20,10))
#filter = ['u','B','g','V','r','i','Y','J','H']

filter=['B','H']
for i in range(len(filter)):
    
    result = ascii.read('../../results/'+filter[i]+'_trgb_result.txt')
    p0=result['p0'][0]
    ep0 = (result['p0'][1]+result['p0'][2])/2
    p1=result['p1'][0]
    ep1 = (result['p1'][1]+result['p1'][2])/2
    p2=result['p2'][0]
    ep2 = (result['p2'][1]+result['p2'][2])/2
    alpha=result['alpha'][0]
    ealpha = (result['alpha'][1]+result['alpha'][2])/2

    beta=result['beta'][0]
    ebeta = (result['beta'][1]+result['beta'][2])/2
    sig=result['sig_int'][0]
    vel=result['vel'][0]
    h0=result['H0'][0]
    eh0 = (result['H0'][1]+result['H0'][2])/2

    #p2=.38
    
    
    tab = ascii.read('../../data/working/'+filter[i]+'_trgb.csv')
    #w= np.where((tab['subtype']!='Ia-91T') & (tab['subtype']!='Ia-91bg') & (tab['caltype']=='none')& (tab['sample']!='bla'))
   
    w = np.where((tab['sn']!='CSP14abk') &  (tab['sn']!='PTF13dyt') &  (tab['sn']!='PTF13dym') &  (tab['sn']!='PS1-13eao'))

    st = tab['st'][w]
    est = tab['est'][w]
    zhel = tab['zhel'][w]
    zcmb = tab['zcmb'][w]
    mmax = tab['Mmax'][w]
    emmax = tab['eMmax'][w]
    bv = tab['BV'][w]
    ebv = tab['eBV'][w]
    m_csp = tab['m'][w]
    ml = tab['ml'][w]
    mu = tab['mu'][w]
    eml = (tab['m'][w]-tab['ml'][w])
    emu = (tab['mu'][w]-tab['m'][w])
    em = (eml+emu)/2.
    dist = tab['dist'][w]
    edist = tab['edist'][w]
    c_ms = tab['covMs'][w]
    c_mbv = tab['covBV_M'][w]
    sn = tab['sn'][w]
    sample = tab['sample'][w]
    cal = tab['caltype'][w]
   
    subtype = tab['subtype'][w] 
    Ho_dist = tab['dist'][w]<0

    st1 = p1*(st - 1)
    st2 = p2*(st - 1)**2
    red = beta*(bv)
    
    mu_obs = mmax - p0 - st1 - st2 - red - alpha*(m_csp-np.median(m_csp)) 
    absmag = p0 + st1 + st2 #+ red #+ alpha*(m_csp-np.median(m_csp)) 

    mu_model = np.where(Ho_dist,distmod(72.0,zhel,zcmb), dist)

    yval = mmax - red - p0- alpha*(m_csp-np.median(m_csp))-mu_model
    pval = st1 + st2
    
    fac= (p1+(2*p2*st))

    err1 = ((fac*est)**2) +(emmax**2) +((beta*ebv)**2)+(2*beta*c_ms)+(2*fac*c_mbv)+(sig**2)+(((2.17*vel)/(zcmb*c))**2)+(alpha*(em/np.log(10)*m_csp))**2 

    err2 = ((fac*est)**2) +(emmax**2) +((beta*ebv)**2)+(2*fac*c_ms)+(beta*c_mbv)+(edist**2)

    #err1 = (emmax**2)+ (ep0**2)+ ((1+(st**2))*(ep1**2)) + ((1+(4*st**2)+(st**4))*(ep2**2))                                                                
    #err2 = (emmax**2)+ (ep0**2)+ ((1+(st**2))*(ep1**2))+ ((1+(4*st**2)+(st**4))*(ep2**2))  

    err = np.where(Ho_dist,err1,err2)
    err = np.sqrt(err)
    dmu=mu_obs-mu_model
    #w1 = np.where(np.abs(dmu)>1.)

    rms=np.sqrt(np.sum(np.power(dmu,2))/len(dmu))
    #err_int=(np.std(dmu)) - (np.mean(err))
    #wt= np.sqrt(1/((ey**2)+(err_int**2))) # weights
    #wt= 1/((err**2)+(err_int**2)) # weights

    #mean= np.sum(dmu*wt)/np.sum(wt)
    #error= np.sqrt((1/np.sum(wt)))
    
    #print (filter[i], '%0.3f'%mean,'%0.3f'%error, '%0.3f'%np.std(dmu), '%0.3f'%(np.std(dmu)/np.sqrt(len(dmu))))
    #print (filter[i],'Full','%0.3f'%rms)
    #sys.exit()
    data=Table()
    data['sn']=sn
    data['res']=dmu
    data['eres']=err
    data['zcmb']=zcmb
    data['st']=st
    data['B-V']=bv
    data['m'] =m_csp
    data['ml'] =ml
    data['mu'] =mu
    data['sample']=sample
    data['cal']=cal
    
    #ascii.write(data,'../../results/Ceph_res_'+filter[i]+'.csv',format='csv', delimiter=',',overwrite=True)
    
    pl.subplot(1,2,i+1)
   
    pl.grid()
    w1 = np.where(dist>0)
   
    pl.plot(st,yval,'ko',label='$'+filter[i]+'$',alpha=.5,ms=10)
    pl.plot(st[w1],yval[w1],'bo',ms=12,label='$TRGB \ cals$')

    pl.plot(st,pval,'ks',lw=2,label='$p1*(s_{BV}-1)+p2*(s_{BV}-1)^2$')
    #pl.gca().invert_yaxis()

    w2 = np.where(m_csp<9.0)
    pl.plot(st[w2],yval[w2],'ro',ms=14,label='$logM<9.0\ SNe \ Ia$')

    #pl.ylim(-1.5,1.5),pl.xlim(0.0,0.15)
    pl.legend(numpoints =1,fontsize=18,loc='lower left')
    #pl.ylabel(r'$p0+p1*(s_{BV}-1)+p2*(s_{BV}-1)^2$' ,fontsize=12)
    pl.ylabel(r'$m-\beta(B-V)-\alpha M-p0-\mu$',fontsize=18)
    pl.xlabel(r'$s_{BV}$' ,fontsize=18)
    #pl.axhline(sig[i],color='g')
    #pl.axhline(-sig[i],color='g')
    #pl.savefig('plots/hd_burns.pdf')
pl.tight_layout()
pl.savefig('../../plots/st_absmag_trgb.pdf')
#pl.show()






