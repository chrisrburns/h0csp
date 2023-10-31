import numpy as np
from astropy.io import ascii
from astropy.table import join, vstack,unique, Table
import cosmolopy.distance as cd
import sys
from collections import Counter
cosmo = {'omega_M_0' : .3, 'omega_lambda_0' : .7, 'h' : 0.70}
cosmo1 = cd.set_omega_k_0(cosmo)


c1 = ascii.read('../../data/hosts/CSP1_SNIa_coord.csv')
c2 = ascii.read('../../data/hosts/CSP2_SN_host_coord.csv')
b = ascii.read('../../data/lc/Spreadsheet.csv')
a = ascii.read('../../data/working/B_all_update2.csv')


#table = Table()
#table['host']= b['Host']
#table.write('../../data/hosts/NedQuery.csv',format='ascii.csv', delimiter=',',overwrite=True)
#sys.exit()


c1.remove_column('zc')
c1.remove_column('gal')
c1.rename_column('ra','snra')
c1.rename_column('dec','sndec')
c = vstack([c1,c2])




tab = join(a,c,keys='sn',join_type='outer')

t = join(tab,a,keys='sn')

print (len(c), len(a), len(tab),len(t))


print (set(tab['sn']).difference(t['sn']))
#print (c)

sn = a['sn']
sn1 = c['sn']

for i in range(len(sn)):
    if sn[i] in sn1:
        print (sn[i])
    else:
        print (sn[i])


sys.exit()

#b.rename_column('Name','sn')
#tab1 = join(c,b,keys='sn')
#b.remove_column('sn')
#b.rename_column('Name(P19)','sn')
#tab2 = join(c,b,keys='sn')

#tab=vstack([tab1,tab2])

#tab = unique(tab,keys='sn')



#w = np.where((tab['Sub-type']!='Ia-02cx') & ((tab['Sub-type']!='Ia-SC')))
#tab=tab[w]
sra=tab['snra']
sdec=tab['sndec']
hra=tab['hra']
hdec=tab['hdec']
z =tab['zcmb']
caltype= tab['caltype']


impact = np.sqrt((((sra-hra)*3600)*np.cos(sdec*np.pi/180))**2 + ((sdec-hdec)*3600)**2)

proj=(cd.angular_diameter_distance(np.abs(z),**cosmo))*(impact/206.264806) # projected distance in kpc

print (len(proj))
table = Table()
table['sn']= tab['sn']
#table['proj'] = proj
table['snra']=sra
table['sndec']=sdec
table['zcmb']=z
table['caltype']=caltype
#print (table)

#table.write('../../data/hosts/proj_dist.csv',format='ascii.csv', delimiter=',',overwrite=True)

table.write('../../data/hosts/cspallcal_sncoords.csv',format='ascii.csv', delimiter=',',overwrite=True)
