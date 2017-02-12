#!/usr/bin/env python3
from source.modules._generic_module import *

class Module(GenericModule):
    def __init__(self):
        self.authors = [
            Author(name='Vitezslav Grygar', email='vitezslav.grygar@gmail.com', web='https://badsulog.blogspot.com'),
        ]
        
        self.name = 'locasploit.update.cve'
        self.short_description = 'Updates CVE database with annual feeds.'
        self.references = [
            '',
        ]
        
        self.date = '2016-10-25'
        self.license = 'GNU GPLv2'
        self.version = '1.0'
        self.tags = [
            'locasploit',
            'update',
            'CVE',
            'CPE',
        ]
        self.description = """
This module downloads all CVE entries from the https://nvd.nist.gov/download.cfm for desired years and populates the database.
This should be run for all years (2002-now) when locasploit is installed. After that, locasploit.update.cve module should be preferred.
"""
        
        self.dependencies = {
        }
        self.changelog = """
"""

        self.reset_parameters()

    def reset_parameters(self):
        self.parameters = {
            'SILENT': Parameter(value='no', mandatory=True, description='Suppress the output'),
            'BACKGROUND' : Parameter(value='yes', mandatory=True, description='yes = run in background, no = wait for it...'),
            'YEARS' : Parameter(value='', mandatory=False, description='Years (separate by spaces), empty = all'),
            'CLEAR' : Parameter(value='no', mandatory=True, description='Discard present entries?'),
            #'TIMEOUT' : Parameter(value='5', mandatory=True, description='Number of seconds to wait'),

        }

    def check(self, silent=None):
        if silent is None:
            silent = positive(self.parameters['SILENT'].value)
        years = self.parameters['YEARS'].value
        result = CHECK_PROBABLY
        # check parameters
        silent = positive(self.parameters['SILENT'].value)
        if not positive(self.parameters['BACKGROUND'].value) and not negative(self.parameters['BACKGROUND'].value):
            if not silent:
                log.err('Bad %s value: %s.', 'BACKGROUND', self.parameters['BACKGROUND'].value)
            result = CHECK_FAILURE
        #if not self.parameters['TIMEOUT'].value.isdigit() or int(self.parameters['TIMEOUT'].value) < 0:
        #    if not silent:
        #        log.err('Bad timeout value: %d', int(self.parameters['TIMEOUT'].value))
        #    result = CHECK_FAILURE
        if not (years=='' or all([x.isdigit() for x in years.split(' ')])):
            if not silent:
                log.err('Invalid YEARS parameter.')
            result = CHECK_FAILURE

        # can import urlib, datetime, gzip, xml.etree.ElementTree and hashlib?
        try:
            from urllib.request import urlretrieve
        except:
            if not silent:
                log.err('Cannot import urllib.request library (urllib5).')
            # TODO other ways?
            result = CHECK_FAILURE
        try:
            import gzip
        except:
            if not silent:
                log.err('Cannot import gzip.')
            # TODO zip alternative?
            result = CHECK_FAILURE
        try:
            from datetime import datetime
        except:
            if not silent:
                log.err('Cannot import datetime.')
            result = CHECK_FAILURE
        try:
            import xml.etree.ElementTree as etree
        except:
            if not silent:
                log.err('Cannot import xml.etree.ElementTree.')
            result = CHECK_FAILURE
        
        try:
            import hashlib
        except:
            if not silent:
                log.err('Cannot import hashlib.')
            result = CHECK_FAILURE
        
        
        return result
    
    def run(self):
        silent = positive(self.parameters['SILENT'].value) 
        clear = positive(self.parameters['CLEAR'].value)
        # # # # # # # #
        #t = Thread(silent, int(self.parameters['TIMEOUT'].value))
        pyears = self.parameters['YEARS'].value
        from datetime import datetime
        years = pyears.split(' ') if pyears != '' else range(2002, datetime.now().year+1)
        t = Thread(silent, years, clear)
        if positive(self.parameters['BACKGROUND'].value):
            return t
        t.start()
        t.join()
        # # # # # # # #
        return None
    
        
class Thread(threading.Thread):
    def __init__(self, silent, years, clear): #,timeout):
        threading.Thread.__init__(self)
        self.silent = silent
        self.years = years
        self.clear = clear
        #self.timeout = timeout
        self.terminate = False
    
    def download_years(self, years):
        from urllib.request import urlretrieve
        from urllib.error import HTTPError
        import gzip
        import hashlib
        
        years_to_update = {} # year: sha1
        for year in years:
            if self.terminate:
                break
            # get cves
            localfile = './vulnerabilities/nvdcve-%s.xml' % (year)
            try:
                urlretrieve('https://nvd.nist.gov/download/nvdcve-%s.xml.gz' % (year), localfile+'.gz')
            except HTTPError:
                log.warn('Cannot get data for %s.' % (year))

            try:
                with gzip.open(localfile+'.gz', 'rb') as fg:
                    io.write_file('/', localfile, fg.read())
                io.delete('/', localfile+'.gz')
                if year == 'Modified':
                    years_to_update[year] = ''
                    continue

                # get hash
                content = io.read_file('/', localfile, forcebinary=True)
                #if isinstance(content, str):
                   #    content = content.encode('utf-8')
                sha1 = hashlib.sha1(content).hexdigest()
                if sha1 != lib.db['vuln'] .get_property('%s_sha1' % (year)):
                    years_to_update[year] = sha1
                    #lib.db['vuln'].add_property('%s_sha1' % (year), sha1)
            except FileNotFoundError:
                log.warn('GZ extraction failed for year %s' % (year))
                pass
        return years_to_update


    def run(self):
        from datetime import datetime
        import xml.etree.ElementTree as etree

        # clear db
        if self.clear:
            lib.db['vuln'].delete_cves_apps()
        
        p = '{http://nvd.nist.gov/feeds/cve/1.2}'
        if not self.silent:
            log.info('Downloading CVE files...')

        io.mkdir('/', './vulnerabilities')
        years_to_update = self.download_years(self.years)
        modified_years_to_update = set()
        
        #for year in [2003]:
        #for year in self.years:
        for year in sorted(years_to_update.keys()):
            if self.terminate:
                break
            if not self.silent:
                log.info('Parsing %s data...' % (year))
            # parse the files
            xmlfile = './vulnerabilities/nvdcve-%s.xml' % (year)
            try:
                tree = etree.parse(xmlfile)
            except FileNotFoundError:
                log.err('Cannot open %s' % (xmlfile))
                continue
            root = tree.getroot()

            #print(root)
            actuples = []
            cvetuples = []
            cves = [x for x in root if 'type' in x.attrib.keys() and x.attrib['type']=='CVE' and not ('reject' in x.attrib.keys() and x.attrib['reject']=='1')]
            #cves = cves[:10]
            for cve in cves:
                # should not stop?
                if self.terminate:
                    break
                # insert into db
                cveid = cve.attrib['name']
                if year == 'Modified':
                    cveyear = cve.attrib['seq'][:4]
                    modified_years_to_update.add(cveyear if cveyear>'2002' else '2002')

                #print(cveid)
                description = cve.find('%sdesc' % p).find('%sdescript' % p).text
                cvetuples.append((cve.attrib, description))
                #lib.db['vuln'].add_cve(cve.attrib, description)
    
                vs = cve.find('%svuln_soft' % p)
                
                if vs is None:
                    products = []
                else:
                    products = vs.findall('%sprod' % p)
                for product in products:
                    #print('   ', product.attrib['vendor'], product.attrib['name'])
                    for version in product.findall('%svers' % p):
                        # prepare for insertion
                        if 'prev' not in version.attrib:
                            version.attrib['prev'] = 0
                        actuples.append((cveid, product.attrib['name'], product.attrib['vendor'], version.attrib['num'], version.attrib['prev']))
            # push into db
            #print('-------- pushing into DB (%d cves, %d acs)' % (len(cvetuples), len(actuples)))
            lib.db['vuln'].add_cves(cvetuples)
            lib.db['vuln'].add_apps_for_cves(actuples)
        
        # from 'Modified' year? Update checksums for altered years
        if self.terminate:
            return
        if 'Modified' in self.years:
            log.info('Updating checksums for modified years...')
            updated_years = self.download_years(modified_years_to_update)
        else:
            updated_years = years_to_update
        for year, sha1 in updated_years.items():
            lib.db['vuln'].add_property('%s_sha1' % (year), sha1)
        
        lib.db['vuln'].add_property('last_update', datetime.now().strftime('%Y-%m-%d'))
        log.ok('CVEs updated.')
        
    # terminates the thread
    def stop(self):
        self.terminate = True
    

lib.module_objects.append(Module())
