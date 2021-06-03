import socket
import threading
import traceback
import urllib.parse
import os
import errno
from http_parser.parser import HttpParser
from src.config import CONNECTION_ESTABLISHED, CR_LF,\
    DEFAULT_HTTPS_PORT, DEFAULT_HTTP_PORT,\
    PORT, HOST, BLOCKED_URLS


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ProxyServer:
    def __init__(self):
        self.buffer_length = 8192

        # Create a TCP socket
        self.listening_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM)

        # Re-use the socket
        self.listening_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            True)
        self.listening_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_KEEPALIVE,
            True)

        self.listening_socket.bind((HOST, PORT))
        self.listening_socket.listen(socket.SOMAXCONN)

        # Trying to accept a connection
        try:
            self.listening_socket.settimeout(1)
            self.listening_socket.accept()
        except:
            print(f'{bcolors.FAIL}Cannot accept connections, is port open?')
            self.listening_socket.close()
            exit()
        self.listening_socket.settimeout(None)
        self.__clients = set()

    def __del__(self):
        del self.listening_socket

    def serve_forever(self):
        print(f'{bcolors.OKGREEN}Welcome to GANDALF TUNNEL v.0.0.0 alpha, \
            happily serving on {HOST} {PORT}..')

        while True:
            client_conn, client_addr = self.listening_socket.accept()
            self.__clients.add(client_addr[0])
            threading.Thread(
                target=self.try_handle,
                args=(client_conn, client_addr)).start()

    def try_handle(self, client_conn, client_addr):
        self.handle(client_conn, client_addr)

    def handle(self, client_conn, client_addr):
        request = client_conn.recv(self.buffer_length)

        if not request:
            return

        method, address, scheme = self.parse_method_and_address(request)
        print(f'{bcolors.OKBLUE}Request to {address}..')
        hostname, _ = address
        if hostname in BLOCKED_URLS:
            print(f'{bcolors.FAIL}------------------------')
            print(f'{bcolors.FAIL}Really? {hostname}?!')
            print(f'{bcolors.FAIL}YOU SHALL NOT PASS!!!!!')
            print(f'{bcolors.FAIL}------------------------')
            client_conn.close()
            return
        # if scheme == 'http':
        #     client_conn.sendall(filtered_message.encode())
        #     return
        with socket.create_connection(address) as server_conn:
            if method == 'CONNECT':
                client_conn.sendall(CONNECTION_ESTABLISHED)
                temp = threading.Thread(
                    target=self.try_forward,
                    args=(server_conn, client_conn))
                temp.start()
                self.forward(client_conn, server_conn)
            else:
                temp = threading.Thread(target=self.try_forward,
                                        args=(server_conn, client_conn, True))
                temp.start()
                server_conn.sendall(request)
                self.forward(client_conn, server_conn)
            temp.join()
            client_conn.close()

    def try_forward(self, source, target, http_forwarding=False):
        try:
            if http_forwarding:
                self.forward_http(source, target)
            else:
                self.forward(source, target)
        except socket.error as e:
            if e.errno == errno.EPIPE:
                print(os.strerror(e.errno))
                print('Detected remote disconnect')
            else:
                print(os.strerror(e.errno))

    def forward(self, source, target):
        while True:
            # Receive data from source
            response = source.recv(self.buffer_length)
            if not response:
                break
            # Forward to target
            target.sendall(response)

    def forward_http(self, source, target):
        p = HttpParser()
        body = []
        while True:
            # Receive data from source
            response = source.recv(self.buffer_length)
            if not response:
                break
            # Forward to target
            target.sendall(response)
            # Use http parser lib to check message completeness
            recved = len(response)
            nparsed = p.execute(response, recved)
            assert nparsed == recved
            if p.is_partial_body():
                body.append(p.recv_body())
            if p.is_message_complete():
                break

    @staticmethod
    def parse_method_and_address(request):
        method, url = ProxyServer.parse_method_and_url(request)

        port = url.port or ProxyServer.get_default_port(url.scheme)
        address = (url.hostname, port)

        return method, address, url.scheme

    @staticmethod
    def parse_method_and_url(request):
        request_str = request.decode()
        first_line = request_str[:request_str.index(CR_LF)]
        method, url_str = first_line.split(' ')[:2]
        if '://' not in url_str:
            url_str = '//' + url_str
        url = urllib.parse.urlparse(url_str)
        return method, url

    @staticmethod
    def get_default_port(scheme):
        if not scheme or scheme == 'http':
            return DEFAULT_HTTP_PORT

        if scheme == 'https':
            return DEFAULT_HTTPS_PORT
