import struct
import sys
import time
from random import random, randint
from select import select
from scapy.arch import get_if_addr
from socket import *
from threading import Thread

TIMEOUT = 10
BUFFER_SIZE = 1024
TYPE = 0x2
COOKIE = 0xabcddcba
TCP_serverPORT = 2073
UDP_ADDRESS = ('<broadcast>', 13117)
connectedPlayers = []


def acceptClients(serverSocket):
    global connectedPlayers
    while len(connectedPlayers) < 2:
        clientSocket, addr = serverSocket.accept()  # blocking
        connectedPlayers.append((clientSocket, addr))


def sendBroadcastToClients():
    UDP_serverSocker = socket(AF_INET, SOCK_DGRAM)
    UDP_serverSocker.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    UDP_serverSocker.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    while len(connectedPlayers) < 2:
        cast = struct.pack('IBH', COOKIE, TYPE, TCP_serverPORT)
        UDP_serverSocker.sendto(cast, UDP_ADDRESS)
        time.sleep(1)


def openTCPSocket():
    # serverAddress = get_if_addr('eth1')
    serverAddress = "192.168.56.1"
    serverSocket = socket(AF_INET, SOCK_STREAM)
    # serverSocket.bind((serverAddress, TCP_serverPORT))
    serverSocket.bind(('', TCP_serverPORT))
    serverSocket.listen(2)
    print("Server started, listening on IP {0}".format(serverAddress))
    return serverSocket


def generateQuestion():
    n1 = randint(20, 100)
    n2 = randint(n1 - 9, n1)
    return "{0}-{1}".format(n1, n2), (n1 - n2)


def generateStartMsg(team1_name, team2_name):
    question, ans = generateQuestion()
    return "Welcome to Quick Math.\n" \
           "Player 1: {0}Player 2: {1}==\n" \
           "Please answer the following question as fast as you can:\n" \
           "How much is {2}?\n".format(
        team1_name, team2_name, question), str(ans)


def generateEndMsg(team1_name, team1_ans, team2_name, team2_ans, ans):
    winner = "No one answered correctly\n"
    if (team1_ans[0] and team1_ans[1] == ans) or (team2_ans[0] and team2_ans[1] != ans):
        winner = "Congratulations to the winner: {0}\n".format(team1_name)
    elif (team2_ans[0] and team2_ans[1] == ans) or (team1_ans[0] and team1_ans[1] != ans):
        winner = "Congratulations to the winner: {0}\n".format(team2_name)
    msg = "Game Over!\n" \
          "The correct answer was {0}!\n".format(ans) + winner
    return msg


def initGame():
    global connectedPlayers
    team1_socket = connectedPlayers[0][0]
    team2_socket = connectedPlayers[1][0]
    try:
        team1_name = team1_socket.recv(BUFFER_SIZE).decode()
        team2_name = team2_socket.recv(BUFFER_SIZE).decode()
        question, ans = generateStartMsg(team1_name, team2_name)
        time.sleep(10)  # wait 10 seconds after the 2 teams joined the game
        # start the game - send the questions
        team1_socket.send(question.encode())
        team2_socket.send(question.encode())
        # wait for response
        team1_ans = (False, "")
        team2_ans = (False, "")
        reads, _, _ = select([team1_socket, team2_socket], [], [], TIMEOUT)
        if len(reads) > 0:
            if reads[0] == team1_socket:
                team1_ans = (True, team1_socket.recv(BUFFER_SIZE).decode())
            elif reads[0] == team2_socket:
                team2_ans = (True, team2_socket.recv(BUFFER_SIZE).decode())
        end_msg = generateEndMsg(team1_name, team1_ans, team2_name, team2_ans, ans)
        # send back results
        team1_socket.send(end_msg.encode())
        team2_socket.send(end_msg.encode())
        team1_socket.close()
        team2_socket.close()
        connectedPlayers = []  # clean list and ready for next session
    except:
        team1_socket.close()
        team2_socket.close()
        print("Something went wrong during the game")


def run():
    serverSocket = openTCPSocket()
    while True:
        sendBroadcast_thread = Thread(target=sendBroadcastToClients)
        acceptClients_thread = Thread(target=acceptClients, args=(serverSocket,))
        sendBroadcast_thread.start()
        acceptClients_thread.start()
        sendBroadcast_thread.join()
        acceptClients_thread.join()
        initGame()
        print("Game over, sending out offer requests...")


if __name__ == "__main__":
    run()
