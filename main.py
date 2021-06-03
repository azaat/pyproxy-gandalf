import socket
import threading
import traceback
import urllib.parse


DEFAULT_HTTP_PORT = 80
DEFAULT_HTTPS_PORT = 443
CR_LF = '\r\n'
HOST = "0.0.0.0"
PORT = 6969
BLOCKED_URLS = [
    "se.math.spbu.ru",
    "tiktok.com",
    "hwproj.me"
]
CONNECTION_ESTABLISHED = b'HTTP/1.1 200 Connection established\r\n\r\n'

filtered_message = '''
<html>
<head>
</head>
<body>
    <h1>Filtered...</h1>
</body>
</html>
'''


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
        # also acts as request length limit! browsers do it too
        # https://stackoverflow.com/questions/2659952/maximum-length-of-http-get-request
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
        self.listening_socket.bind((HOST, PORT))
        self.listening_socket.listen(socket.SOMAXCONN)

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
        url = None
        try:
            self.handle(client_conn, client_addr)
        except:
            url_str = url.geturl() if url else None
            print(url_str)
            traceback.print_exc()

    def handle(self, client_conn, client_addr):
        request = client_conn.recv(self.buffer_length)

        if not request:
            return

        method, address = self.parse_method_and_address(request)
        print(f'{bcolors.OKBLUE}Request to {address}..')
        hostname, _ = address
        if hostname in BLOCKED_URLS:
            print(f'{bcolors.FAIL}------------------------')
            print(f'{bcolors.FAIL}Really? {hostname}?!')
            print(f'{bcolors.FAIL}YOU SHALL NOT PASS!!!!!')
            print(f'{bcolors.FAIL}------------------------')
            client_conn.close()
            return
        with socket.create_connection(address) as server_conn:
            if method == 'CONNECT':
                client_conn.sendall(CONNECTION_ESTABLISHED)
                threading.Thread(
                    target=self.try_forward,
                    args=(server_conn, client_conn)).start()

            else:
                threading.Thread(target=self.try_forward,
                                 args=(server_conn, client_conn
                                 )).start()
                server_conn.sendall(request)

            self.forward(client_conn, server_conn)

    def try_forward(self, source, target):
        try:
            self.forward(source, target)
        except:
            traceback.print_exc()

    def forward(self, source, target):
        while True:
            # Receive data from source
            response = source.recv(self.buffer_length)
            if not response:
                break
            # Forward to target
            target.sendall(response)

    @staticmethod
    def parse_method_and_address(request):
        method, url = ProxyServer.parse_method_and_url(request)

        port = url.port or ProxyServer.get_default_port(url.scheme)
        address = (url.hostname, port)

        return method, address

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


def main():
    proxy = ProxyServer()
    proxy.serve_forever()


if __name__ == '__main__':
    main()
