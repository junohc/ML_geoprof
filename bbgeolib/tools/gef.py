import sys  
import numpy as np
import pandas as pd
import math
from shapely.geometry import Point, Polygon
sys.path.append("D:\\Projects\\Python\\libraries\\") 
from bbgeolib.objects.gef import get_from_file

UNIT_WEIGHT_WATER = 9.81

EMPERICAL_QC = [['[S] Zand', 3],
                ['[C] Klei', 1],
                ['[P] Veen', 0]]

NEN5140 = [['[P] Veen',8.1],
           ['[P] Veen kleihoudend',5],
           ['[C] Klei veenhoudend',4],
           ['[C] Klei slap',3.3],
           ['[C] Klei matig',2.9],
           ['[C] Klei stevig',2.5],
           ['[C] Klei silthoudend',2.2],
           ['[C] Klei zandhoudend',1.8],
           ['[S] Zand kleihoudend',1.4],
           ['[S] Zand silthoudend',1.1],
           ['[S] Zand fijn',0.8],
           ['[S] Zand matig',0.6],
           ['[S] Zand grof',0.0]]

ROBERTSON_SOILS = {
    '[C] RBS_Grond':Polygon([(0.00,0.00),(0.00,1.01),(0.22,0.98),(0.48,0.90),(0.83,0.69),(0.98,0.49),(1.23,0.05),(1.22,0.00)]),
    '[P] RBS_Veen':Polygon([(1.22,0.00),(1.23,0.05),(1.61,0.27),(1.79,0.48),(1.91,0.70),(2.00,0.88),(2.00,0.00)]),
    '[C] RBS_Klei_zs':Polygon([(1.23,0.05),(1.12,0.27),(0.98,0.48),(0.83,0.69),(1.01,0.75),(1.28,0.95),(1.51,1.23),(1.79,1.79),(2.00,1.75),(2.00,0.88),(1.91,0.70),(1.79,0.48),(1.61,0.27)]),
    '[C] RBS_Klei_s':Polygon([(0.83,0.69),(0.64,0.81),(0.86,0.86),(1.04,1.00),(1.16,1.20),(1.29,1.60),(1.40,2.36),(1.59,1.99),(1.79,1.79),(1.51,1.23),(1.28,0.95),(1.01,0.75)]),
    '[S] RBS_Zand_s':Polygon([(0.64,0.81),(0.48,0.90),(0.22,0.98),(0.00,1.01),(0.00,1.44),(0.46,1.49),(0.83,1.67),(1.09,1.90),(1.40,2.36),(1.29,1.60),(1.16,1.20),(1.04,1.00),(0.86,0.86)]),
    '[S] RBS_Zand_zs':Polygon([(0.00,1.44),(0.00,2.18),(0.31,2.26),(0.63,2.44),(0.82,2.64),(1.07,3.26),(1.25,2.71),(1.40,2.36),(1.09,1.90),(0.83,1.65),(0.46,1.49)]),
    '[S] RBS_Zand_g':Polygon([(0.00,2.18),(0.00,4.00),(1.07,4.00),(1.07,3.26),(0.82,2.64),(0.63,2.44),(0.31,2.26)]),
    '[S] RBS_Zand_v':Polygon([(1.07,4.00),(1.71,4.00),(1.71,2.99),(1.67,2.40),(1.59,1.99),(1.40,2.36),(1.25,2.71),(1.07,3.26)]),
    '[S] RBS_Grond_zs':Polygon([(1.71,4.00),(2.00,4.00),(2.00,1.75),(1.79,1.79),(1.59,1.99),(1.67,2.40),(1.71,2.99)])
}

ROBERTSON_SOILS_SPECIALS = {
    '[P] RBS_Veen_ocr':Polygon([(1.64,2.18),(1.72,2.32),(1.80,2.35),(1.93,2.29),(1.96,2.16),(1.94,2.06),(1.85,1.98),(1.76,1.99),(1.67,2.04)])
}

COLOR_HACK = {
    '[S] Zand':'#f9f900',
    '[C] Klei':'#1c8234',
    '[P] Veen':'#824b1b',
    '[P] Veen kleihoudend':'#e0883c',
    '[C] Klei veenhoudend':'#b2e084',
    '[C] Klei slap':'#98ce63',
    '[C] Klei matig':'#68a82a',
    '[C] Klei stevig':'#1c8234',
    '[C] Klei silthoudend':'#326303',
    '[C] Klei zandhoudend':'#e2df83',
    '[S] Zand kleihoudend':'#e8e358',
    '[S] Zand silthoudend':'#c9c442',
    '[S] Zand fijn':'#efe93e',
    '[S] Zand matig':'#f9f213',
    '[S] Zand grof':'#f9f900',
    '[C] RBS_Grond':'#c6c6b4',
    '[P] RBS_Veen':'#824b1b',
    '[C] RBS_Klei_zs':'#98ce63',
    '[C] RBS_Klei_s':'#1c8234',
    '[S] RBS_Zand_s':'#e8e358',
    '[S] RBS_Zand_zs':'#c9c442',
    '[S] RBS_Zand_g':'#f9f900',
    '[S] RBS_Zand_v':'#6d6d28',
    '[S] RBS_Grond_zs':'#84846f',
    '[P] RBS_Veen_ocr':'#5e3f02',
    'Unknown':'#ffffff'    
}

def robertson(nrf, nqc):
    """This function returns the soiltype according to the given (normalized)
    frictionnumber [0.1 - 10] and (normalized) cone resistance [1 - 1000]
    input:
    nrf = normalized friction number
    nqc = normalized cone resistance
    output:
    name of the soiltype or Unknown if input is out of bounds
    notes:
    nrf = (100 x fs) / (qt - sv0)
    nqc = (qt - sv0) / s'v0
    sv0 = vertical soilstress
    sv'0 = effective vertical soilstress
    !! USE THIS RULE BEFORE ROBERTSON !!:
    qc < 1.5 and Rf > 5.0 returns [P] RBS_Veen
    """
    if nrf < 0.1:
        #print("Warning, found nrf<0.1 in robertson correlation")
        nrf = 0.1
    if nqc < 1.: 
        #print("Warning, found nqc<1 in robertson correlation")
        nqc = 1.

    x = math.log10(nrf) + 1.
    y = math.log10(nqc)
    if y>=4.: y=3.999
    if x<=0.: x=0.001

    # first check the minor polygons (small elipses that cross multiple polygons)
    for key, value in ROBERTSON_SOILS_SPECIALS.items():
        if value.contains(Point(x,y)) or (x,y) in list(value.exterior.coords):
            return key

    # now check the major polygons
    for key, value in ROBERTSON_SOILS.items():
        if value.contains(Point(x,y)) or (x,y) in list(value.exterior.coords):
            return key

    #print("[W] no soil found for combination nrf=%f and nqc=%f (x=%.2f, y=%.2f)" % (nrf, nqc, x, y))
    return "Unknown"

def emperical_qc_only(qc):
    for soilname, _qc in EMPERICAL_QC:
        if qc >= _qc:
            return soilname
    return EMPERICAL_QC[-1][0]

def nen5140(wg):
    for soilname, _wg in NEN5140:
        if wg >= _wg:
            return soilname
    return NEN5140[-1][0]

def unit_weight_from_cpt(qt, rf):
    if qt<1.5 and rf>=5.: return 10.
    if rf <= 0.: rf = 1e-3
    if qt <= 0.: qt = 1e-3
    yw = (0.27 * math.log10(rf) + 0.36 * math.log10(qt / 0.101325) + 1.236) * UNIT_WEIGHT_WATER
    if yw < 10.: 
        return 10.
    else:
        return yw
        
def get_unit_weight_from_cpt(gef):
    df = gef.as_dataframe()
    df['unitweight'] = df.apply(lambda x: unit_weight_from_cpt(x['qc'], x['wg']), axis=1)
    return df

def get_soilstress_from_cpt(gef):
    df = get_unit_weight_from_cpt(gef)
    svs = []
    for _, row in df.iterrows():
        if len(svs)==0:
            svs.append(0)            
        else:
            svs.append(svs[len(svs)-1] + (yprev - row['depth']) * row['unitweight'])
        yprev = row['depth']
    df['sv'] = svs
    return df

def gef_to_soils_robertson(gef, interval=0.1):
    if not gef._has_pw:
        print("Deze CPT heeft geen wrijvingsgetal en kan niet door Robertson geinterepreteerd worden")
        return None
    
    df = gef.as_dataframe()
    num = int((gef.z_start - gef.z_min) / interval)
    zs = np.linspace(gef.z_start, gef.z_min, num)
    sls = []
    sv0top = 0.
    for i in range(1,len(zs)):
        ztop, zbottom = zs[i-1], zs[i]
        qcgem = df[(df['depth']<=ztop) & (df['depth']>=zbottom)]['qc'].agg('mean')
        fsgem = df[(df['depth']<=ztop) & (df['depth']>=zbottom)]['fs'].agg('mean') 
        wggem = df[(df['depth']<=ztop) & (df['depth']>=zbottom)]['wg'].agg('mean')
        uw = unit_weight_from_cpt(qcgem, wggem)
        sv0bot = sv0top + (ztop - zbottom) * uw
        sv0 = (sv0bot + sv0top) / 2.
        nqc = (qcgem * 1000. - sv0) / sv0
        nrf = (100 * fsgem * 1000.) / (qcgem * 1000. - sv0)
        
        if qcgem < 1.5 and wggem > 5.:
            sls.append([ztop, zbottom, '[P] RBS_Veen'])
        else:
            sls.append([ztop, zbottom, robertson(nrf, nqc)])        

    result = [sls[0]]
    for i in range(1, len(sls)):
        if sls[i][-1] != result[-1][-1]:
            result.append(sls[i])
        else:
            result[-1][1] = sls[i][1]

    return pd.DataFrame(data=result, columns=['ztop','zbottom','soilname'])       

def gef_to_soils(gef, interval=0.1):
    df = gef.as_dataframe()
    num = int((gef.z_start - gef.z_min) / interval)
    zs = np.linspace(gef.z_start, gef.z_min, num)
    sls = []
    for i in range(1,len(zs)):
        ztop, zbottom = zs[i-1], zs[i]
        if gef._has_pw:
            sls.append([ztop, zbottom, nen5140(df[(df['depth']<=ztop) & (df['depth']>=zbottom)]['wg'].agg('mean'))]) 
        else:
            sls.append([ztop, zbottom, emperical_qc_only(df[(df['depth']<=ztop) & (df['depth']>=zbottom)]['qc'].agg('mean'))]) 

    result = [sls[0]]
    for i in range(1, len(sls)):
        if sls[i][-1] != result[-1][-1]:
            result.append(sls[i])
        else:
            result[-1][1] = sls[i][1]

    return pd.DataFrame(data=result, columns=['ztop','zbottom','soilname'])    

def get_top_sand_layer(gef, interval=0.1, max_voorboor=0.5):    
    if gef.z - gef.z_start > max_voorboor:
        print("sondering %s heeft een voorboring van meer dan %.2fm." % (gef.filename, max_voorboor))
        return(-1, 0., 0.)

    zstart, zend = gef.z, gef.z    
    soils = gef_to_soils(gef, interval) 
    for index, row in soils.iterrows():
        if row['soilname'].find('[S]')<0:
            zend = row['ztop']
            if zstart - zend >= interval:
                return (zstart-zend, zstart, zend)
    return(0., 0., 0.)

if __name__=="__main__":
    g = get_from_file('D:\\Data\\bodemarchief_gef\\Sonderingen\\VAK_A01\\A01-1.gef')
    #   print(gef_to_soils_robertson(g, interval=0.5))
    print(get_gef_complete(g))