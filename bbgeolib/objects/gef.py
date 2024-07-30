import datetime
import sys, os.path
import pandas as pd
import numpy as np

sys.path.append("D:\\Projects\\Python\\libraries\\") #TODO REMOVE AFTER TESTING

GEFCOL_Z = 1
GEFCOL_QC = 2
GEFCOL_PW = 3
GEFCOL_WG = 4

MEASUREMENTTEXT_DATUM_BORING = 16

def get_from_file(filename):
    g = GEF()
    g.read(filename)

    if g.valid: 
        if g._type == 'BORE':           
            g = GEFBore()
            g.read(filename)
            if g.valid:
                return g
            else:
                print("Kan boringen bestand %s niet lezen, hier is het logbestand" % filename)
                print(g.readlog)
        elif g._type == 'CPT':
            g = GEFCPT()
            g.read(filename)
            if g.valid:
                return g
            else:
                print("Kan het sonderingen bestand %s niet lezen, hier is het logbestand" % filename)
                print(g.readlog)
    else:
        print("Kan de header van het bestand %s niet lezen, hier is het logbestand" % filename)
        print(g.readlog)
    return None    

class GEF:
    def __init__(self):
        self.valid = True
        self._column_seperator = ' '
        self._record_seperator = ''
        self._filedate = ''
        self._startdate = ''
        self._projectid = ''
        self._companyid = ''
        self._columns = {}
        self.x = 0.
        self.y = 0.
        self.z = 0.        
        self._measurementtext = {}
        self._columnvoids = {}
        self._datalines = []
        self.readlog = []    
        self._type = "UNDEFINED"   
        self.filename = "" 
        self.name = ""
        
        self._knownkeywords = [
            "RECORDSEPARATOR",
            "COLUMNSEPARATOR",
            "FILEDATE",
            "STARTDATE",
            "COLUMNINFO",
            "REPORTCODE",
            "XYID",
            "ZID",
            "COLUMNVOID",
            "COLUMN",
            "PROCEDURECODE",
            "MEASUREMENTTEXT"
        ]       

    def getDate(self):
        """
        """
        if self._startdate != '':
            return self._startdate
        elif MEASUREMENTTEXT_DATUM_BORING in self._measurementtext:
            return self._measurementtext[MEASUREMENTTEXT_DATUM_BORING][0]        
        else:
            return self._filedate

    def add_to_readlog(self, msg):
        self.readlog.append(msg)

    def handleMEASUREMENTTEXT(self, args):
        self._measurementtext[int(args[0])] = args[1:]

    def handleCOLUMNSEPARATOR(self, args):
        self._column_seperator = args[0]

    def handleRECORDSEPARATOR(self, args):
        self._record_seperator = args[0]

    def handleFILEDATE(self, args):
        try:
            self._filedate = datetime.date(int(args[0].strip()), int(args[1].strip()), int(args[2].strip()))
        except:
            self._filedata = ''
    
    def handleSTARTDATE(self, args):
        try:
            self._startdate = datetime.date(int(args[0].strip()), int(args[1].strip()), int(args[2].strip()))
        except:
            self._startdate = ''

    def handleCOLUMNINFO(self, args):
        try:
            column = int(args[0])
            dtype = int(args[3].strip())
            if dtype==11: #override depth with corrected depth, TODO > check of 11 de juiste code is
                dtype = 1
            self._columns[dtype] = column - 1
        except:
            self.add_to_readlog("Fatale fout: invoer voor COLUMNINFO is foutief")
            self.valid = False
        return

    def handleREPORTCODE(self, args):
        if self._type == "UNDEFINED":
            if args[0].find('CPT') > -1:
                self._type = "CPT"
            elif args[0].find('BORE') > -1:
                self._type = "BORE"
        
    def handlePROCEDURECODE(self, args):
        self.handleREPORTCODE(args)

    def handleXYID(self, args):
        try:
            self.x = float(args[1].strip())
            self.y = float(args[2].strip())
            if self.x == 0. and self.y == 0.:
                self.add_to_readlog("Fatale fout > X en of Y coordinaat is nul (%.2f,%.2f)." % (self.x, self.y))
                self.valid = False
            elif self.x < 0 and self.y < 289000:
                self.x += 155000
                self.y += 463000
            elif self.x < -7000 or self.x > 300000 or self.y < 289000 or self.y > 629000:
                self.add_to_readlog("Fatale fout > De coordinaten (%.2f,%.2f) vallen buiten Nederland" % (self.x, self.y))
                self.valid = False            
        except:
            self.add_to_readlog("Fatale fout: x en y coordinaten zijn ongeldig")
            self.valid = False            

    def handleZID(self, args):
        try:
            self.z = float(args[1].strip())
            self.zstart = self.z # intially zstart is equal to z but we have to check this assumption at the first dataline
        except:
            self.add_to_readlog("Fatale fout: z coordinaat is ongeldig")
            self.valid = False        

    def handleCOLUMNVOID(self, args):
        try:
            col = int(args[0].strip())
            self._columnvoids[col-1] = float(args[1].strip())
        except Exception as e:
            self.add_to_readlog("[E] Fout in columnvoid lijn %s, melding: %s" % (line, str(e)))
            self.add_to_readlog("[I] De voorgaande fout wordt vaak veroorzaakt doordat de kolom van de columnvoid niet bestaat.")

    def handleCOLUMN(self, args):
        numcols = int(args[0].strip())
        self._columnvoids = [None] * numcols

    def read(self, filename):
        self.filename = filename
        self.name = os.path.splitext(os.path.basename(filename))[0]
        self._datalines = open(filename, 'r', encoding='utf-8', errors='ignore').readlines()
        self._datalines = [l for l in self._datalines if len(l.strip())>0]	
        for line in self._datalines:
            if line.find('#EOH')>=0:
                return
            else:
                self._parse_header_line(line)       

    def _parse_header_line(self, line):
        """
        """
        try:
            keyword, argline = line.split('=')
        except:
            self.add_to_readlog("Error splitting line %s" % line)
            self.valid = False
            return

        keyword = keyword.strip().replace('#', '')
        argline = argline.strip()
        args = argline.split(',')

        if keyword in self._knownkeywords:
            try:
                f = getattr(self, "handle%s" % keyword)
                f(args)
            except Exception as e:
                self.add_to_readlog("Fatale fout" + str(e))
                self.valid = False
        else:
            pass
            #print("No handler defined for keyword #%s, skipping this information" % keyword)

class GEFBore(GEF):
    def __init__(self): 
        super().__init__()

    def read(self, filename):
        super().read(filename)
        if not self._check_header():
            self.valid = False
            return

        #carry on reading the data

    def _parse_data(self, lines):
        return

    def _check_header(self):
        return True

    def _parse_cpt_data_line(self, line):
        pass

class GEFCPT(GEF):
    def __init__(self): 
        super().__init__()
        self._check_zstart = True
        self.z_start = 0. #start of the measurements (can be below z because of predigged soil)
        self.z_min = 0.
        self.dz = []
        self.qc = []
        self.pw = []
        self.wg = []
        self._has_pw = True
        self._has_wg = True

    def read(self, filename):
        super().read(filename)
        if not self._check_header():
            self.valid = False
            return

        isdata = False
        for line in self._datalines:
            if isdata and self.valid:
                if self._record_seperator != '':
                   line = line.replace(self._record_seperator, '')                   
                self._parse_cpt_data_line(line)
            if line.find('#EOH')>=0:
                isdata = True
        
    def _check_header(self):
        """
        """
        if not GEFCOL_Z in self._columns:
            self.add_to_readlog("Fatale fout > Dit GEF bestand mist een diepte kolom")
            return False

        if not GEFCOL_QC in self._columns:
            self.add_to_readlog("Fatale fout > Dit GEF bestand mist een qc (conusweerstand) kolom")
            return False

        self._has_pw = GEFCOL_PW in self._columns
        self._has_wg = GEFCOL_WG in self._columns        
        
        if self._type != 'CPT':
            self.add_to_readlog("Fatale fout > Dit GEF bestand is geen CPT, gevonden: ({})".format(self._type))
            return False
        
        return True

    def _parse_cpt_data_line(self, line):        
        try:
            args = line.strip().split(self._column_seperator)  
            for i in range(len(self._columnvoids)):
                if args[i] == self._columnvoids[i]:
                    return #skip this line, it has a void

            args = [float(arg.strip()) for arg in args if len(arg.strip())>0]
        
            dz = self.z - abs(args[self._columns[GEFCOL_Z]])
            self.z_min = dz
            if self._check_zstart: #first dataline, check if this measurement is at the same level as z or if it is predigged
                if dz != 0:
                    self.z_start = dz
                    self._check_zstart = False
        
            qc = args[self._columns[GEFCOL_QC]]
            if self._has_pw:
                #print(self._columns)
                pw = float(args[self._columns[GEFCOL_PW]])

            if self._has_wg:
                wg = float(args[self._columns[GEFCOL_WG]])

            self.dz.append(dz)
            if(qc <= 0): qc = 1e-3
            self.qc.append(qc)

            if self._has_pw:
                if(pw <= 0): pw = 1e-6
                self.pw.append(pw)
            else:
                self.pw.append(1e-6)

            if self._has_wg:
                if wg>10.: wg=10.
                if wg<0: wg=0.
            else:
                if self._has_pw:
                    wg = (pw / qc) * 100.
                    if wg>10.: wg=10.
                    if wg<0: wg=0.
                else:
                    wg = 0
            self.wg.append(wg)
        except Exception as e:            
            self.add_to_readlog("Fout bij het lezen van de data: %s" % str(e)) 
            self.valid = False  

    def as_numpy(self):
        """
        """
        return np.transpose(np.array([self.dz, self.qc, self.pw, self.wg]))

    def as_dataframe(self):
        """
        """
        a = self.as_numpy()
        return pd.DataFrame(data=a, columns=['depth','qc','fs','wg'])

if __name__=="__main__":    
    import glob
    geffiles = glob.glob('D:\\Projects\\Python\\libraries\\bbgeolib\\testdata\\gefs\\*.gef')
    for file in geffiles:        
        g = get_from_file(file)
        if g is not None:
            print(g.name)
            print("DATE",  g.getDate())