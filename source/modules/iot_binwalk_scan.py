#!/usr/bin/env python3
"""
This module uses binwalk to analyze structure of a binary file.
"""
from source.modules._generic_module import *

class Module(GenericModule):
    def __init__(self):
        self.authors = [
            Author(name='Vitezslav Grygar', email='vitezslav.grygar@gmail.com', web='https://badsulog.blogspot.com'),
        ]
        
        self.name = 'iot.binwalk.scan'
        self.short_description = 'Performs a binwalk on a file.'
        self.references = [
            '',
        ]
        
        self.date = '2016-07-22'
        self.license = 'GNU GPLv2'
        self.version = '1.0'
        self.tags = [
            'IoT',
            'Internet of Things',
            'binwalk',
            'firmware'
        ]
        self.description = """
Performs a binwalk on a file.
"""
        self.dependencies = {
        }
        self.changelog = """
"""

        self.reset_parameters()

    def reset_parameters(self):
        self.parameters = {
            'ACTIVEROOT': Parameter(mandatory=True, description='System to work with'),
            'SILENT': Parameter(value='no', mandatory=True, description='Suppress the output'),
            'BINFILE': Parameter(mandatory=True, description='File to analyze'),
        }

    def check(self, silent=None):
        if silent is None:
            silent = positive(self.parameters['SILENT'].value)
        result = CHECK_SUCCESS
        # binwalk available?
        try:
            import binwalk
        except:
            if not silent:
                log.err('Binwalk is not available.')
            result = CHECK_FAILURE
        return result
    
    def run(self):
        silent = positive(self.parameters['SILENT'].value)
        import binwalk
        try:
            # Perform a signature scan against the files specified on the command line and suppress the usual binwalk output.
            path = io.get_fullpath(self.parameters['ACTIVEROOT'].value, self.parameters['BINFILE'].value)
            for module in binwalk.scan(path, signature=True, quiet=True):
                if not silent:
                    for result in module.results:
                        log.writeline('0x%.8X    %s [%s]' % (result.offset, result.description, str(result.valid)))
        except binwalk.ModuleException as e:
            log.err(str(e))
        
        return None
    
"""        
class Thread(threading.Thread):
    def __init__(self, silent, timeout):
        threading.Thread.__init__(self)
        self.silent = silent
        self.timeout = timeout
        self.terminate = False
            
    # starts the thread
    def run(self):
        if not self.silent:
            log.info('You have %d seconds.' % (self.timeout))
        while self.timeout > 0:
            self.timeout -= 1
            time.sleep(1)
        if not self.silent:
            log.ok('Time\'s up!')

    # terminates the thread
    def stop(self):
        self.terminate = True
"""    

lib.module_objects.append(Module())
