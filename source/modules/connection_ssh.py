#!/usr/bin/env python3
"""
This module creates an SSH connection.
"""
from source.modules._generic_module import *

class Module(GenericModule):
    def __init__(self):
        super().__init__()
        self.authors = [
            Author(name='Vitezslav Grygar', email='vitezslav.grygar@gmail.com', web='https://badsulog.blogspot.com'),
        ]
        
        self.name = 'connection.ssh'
        self.short_description = 'Creates a SSH connection.'
        self.references = [
        ]
        self.date = '2017-01-14'
        self.license = 'GNU GPLv2'
        self.version = '1.0'
        self.tags = [
            'SSH',
            'RSA',
            'public',
            'private',
            'key',
            'password',
            'agent', 'ssh-agent',
        ]
        
        
        self.description = """This module creates SSH connection. Paramiko must be installed.
In version 1.0 the following authentication methods are supported:
    agent    - ssh-agent is used 
    password - user is asked for password
    pubkey   - private key is used, user must provide password if necessary

Login with empty password is not possible.
"""
        
        self.dependencies = {

        }
        self.changelog = """
"""

        self.reset_parameters()

    def reset_parameters(self):
        self.parameters = {
            'SILENT': Parameter(value='no', mandatory=True, description='Suppress the output'),
            'HOST': Parameter(mandatory=True, description='IP/hostname of the target system'),
            'PORT': Parameter(value='22', mandatory=True, description='SSH remote port'),
            'USER': Parameter(mandatory=True, description='Username'),
            'METHOD': Parameter(mandatory=True, description='Auth method - agent, password or pubkey'),
            'PRIVATEKEY': Parameter(mandatory=False, description='Absolute path of private key'),
        }

    def check(self, silent=None):
        
        if silent is None:
            silent = positive(self.parameters['SILENT'].value)
        method = self.parameters['METHOD'].value
        privkey = self.parameters['PRIVATEKEY'].value
        port = self.parameters['PORT'].value
        result = CHECK_PROBABLY
        
        # can import paramiko and getpass?
        try:
            import paramiko
        except:
            log.err('Paramiko module is not present.')
            result = CHECK_FAILURE
        try:
            import getpass
        except:
            log.err('Getpass module is not present.')
            result = CHECK_UNLIKELY # may not be needed
        # correct method
        if method not in ['agent', 'password', 'pubkey']:
            log.err('Wrong METHOD parameter.')
            result = CHECK_FAILURE
        # correct port
        if not (port.isdigit() and int(port)>0 and int(port)<65536):
            if not silent:
                log.err('Invalid port value.')
            result = CHECK_FAILURE
        # existing privatekey if pubkey
        if method == 'pubkey' and not io.can_read('/', privkey):
            if not silent:
                log.err('Private key file cannot be read.')
            result = CHECK_FAILURE
        
        return result

    def run(self):
        silent = positive(self.parameters['SILENT'].value)
        host = self.parameters['HOST'].value
        port = int(self.parameters['PORT'].value)
        user = self.parameters['USER'].value
        method = self.parameters['METHOD'].value
        privatekey = self.parameters['PRIVATEKEY'].value
        
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if method == 'agent':
            try:
                client.connect(host, port=port, username=user)
            except paramiko.ssh_exception.NoValidConnectionsError:
                log.err('Cannot connect to the host \'%s\'.' % (host))
                client = None
            except Exception as e:
                log.err('Connection with ssh-agent failed: %s.' % (str(e)))
                client = None
                
        if method == 'password':
            import getpass
            password = getpass.getpass('Password for user %s: ' % (user))
            try:
                client.connect(host, port=port,  username=user, password=password)
            except paramiko.ssh_exception.NoValidConnectionsError:
                log.err('Cannot connect to the host \'%s\'.' % (host))
                client = None
            except Exception as e:
                log.err('Connection with password failed: %s.' % (str(e)))
                client = None
        
        if method == 'pubkey':
            pkey = None
            try:
                pkey = paramiko.RSAKey.from_private_key_file(privatekey)
            except: # encrypted?
                try:
                    import getpass
                    password = getpass.getpass('Password for private key: ')
                    pkey = paramiko.RSAKey.from_private_key_file(privatekey, password=password)
                except:
                    log.err('Cannot process private key file.')
                    client = None

            if pkey is not None:
                try:
                    client.connect(host, port=port, username=user, pkey=pkey)
                except paramiko.ssh_exception.NoValidConnectionsError:
                    log.err('Cannot connect to the host \'%s\'.' % (host))
                    client = None
                except Exception as e:
                    log.err('Connection with pubkey failed: %s.' % (str(e)))
                    client = None
        
        if client is not None:
            c = Connection('ssh://%s@%s:%s/' % (user, host, port), client, 'SSH')
            lib.connections.append(c)
            if not silent:
                log.ok('Connection created: %s' % (c.description))
            # test sftp
            try:
                sftp = client.open_sftp()
                sftp.close()
            except:
                log.err('SFTP connection cannot be established.')
            
            # client.close() is called on connection kill request or program termination
           
            # EXAMPLES
            # =======================
            # normal read
            #data = io.read_file(c.description, '/etc/resolv.conf')
            #print(data)

            # chunk read
            #f = io.get_fd(c.description, '/etc/resolv.conf', 'r')
            #data = io.read_file(c.description, '/etc/resolv.conf', f=f, chunk=10)
            #while len(data)>0:
            #    print(data)
            #    data = io.read_file(c.description, '/etc/resolv.conf', f=f, chunk=10)

        return None

lib.module_objects.append(Module())

