import struct
import sys
from select import select
from socket import *

# Magic numbers
TIMEOUT = 10
UDP_serverPort = 13117
BUFFER_SIZE = 1024
EXPECTED_COOKIE = 0xabcddcba
EXPECTED_OFFER_TYPE = 0x2
TEAM_NAME = 'HAFALAFEL HA-YA-ROCK!\n'
INVALID_OFFER_FORMAT = "Invalid expected offer format"


def run():
    # Open UDP socket to listen for broadcast from servers
    print("Client started, listening for offer requests...")
    UDP_clientSocket = socket(AF_INET, SOCK_DGRAM)
    UDP_clientSocket.setsockopt(SOL_SOCKET,SO_REUSEADDR, 1)
    UDP_clientSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    # SOL_SOCKET - search in the socket level itself
    # SO_BROADCAST - This option controls whether datagrams may be broadcast from the socket. The value has type int; a nonzero value means “yes”.
    UDP_clientSocket.bind(('', UDP_serverPort))  # (IP,PORT) - listen to specific port
    while True:
        offer, serverAddress = UDP_clientSocket.recvfrom(BUFFER_SIZE)  # blocking
        print("Received offer from {0}, attempting to connect...".format(serverAddress[0]))
        try:
            # check that the offer is valid as instructed
            # I - unsigned int(4 bytes) B- unsigned char(1 byte) H -"unsigned short(2 bytes)
            cookie, msg_type, TCP_server_port = struct.unpack('IBH', offer)
            if cookie == EXPECTED_COOKIE and msg_type == EXPECTED_OFFER_TYPE:
                server_IP_PORT = (serverAddress[0], TCP_server_port)
                TCP_clientSocket = socket(AF_INET, SOCK_STREAM)
                TCP_clientSocket.connect(server_IP_PORT)  # if it fails it will continue the loop for other offers
                # send the server out team name
                TCP_clientSocket.send(TEAM_NAME.encode())
                # get the welcome message + question from the server
                msg = TCP_clientSocket.recv(BUFFER_SIZE).decode()
                print(msg)
                # open timer for 10 seconds so that we can answer
                answerQuestion(TCP_clientSocket)
                print("Server disconnected, listening for offer requests...")
                TCP_clientSocket.close()
            else:
                print(INVALID_OFFER_FORMAT)
        except:
            continue


def answerQuestion(TCP_clientSocket):
    try:
        reads, _, _ = select([sys.stdin, TCP_clientSocket], [], [], TIMEOUT)
        if len(reads) > 0:
            if reads[0] == sys.stdin:
                ans = sys.stdin.readline().encode()
                TCP_clientSocket.send(ans)
            elif reads[0] == TCP_clientSocket:
                ans = TCP_clientSocket.recv(BUFFER_SIZE).decode()
                print(ans)
    except:
        print("Something went wrong in the answerQuestion method")



if __name__ == "__main__":
    run()
