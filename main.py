from src.ProxyServer import ProxyServer


def main():
    proxy = ProxyServer()
    proxy.serve_forever()


if __name__ == '__main__':
    main()
