import json
import random
import socket
import struct

from client_status import AcceptanceChoice, ClientStatus

import _thread


class Client:
    def __init__(self, status, username):
        self.sock = None
        self.status = status
        self.wait_acceptance = {}
        self.username = username
        self.message = ""
        self.chat_identifier = ""
        self.chat_name = ""
        self.multicast_group = ("224.3.29.71", 0)

    def __del__(self):
        self.close_socket()

    def generate_identifier(self):
        return self.sock.getsockname()[-1]

    def multicast(self, message):
        self.sock.sendto(json.dumps(message).encode("utf-8"), self.multicast_group)

    def set_acceptance_ticket(self, message, address):
        self.wait_acceptance = {
            "status": True,
            "message": message,
            "address": address,
        }

    def get_validation_ticket(self, message):
        validation_ticket = {
            "from": self.username,
            "to": message["sender"],
            "port": self.multicast_group[-1],
            "chat_name": self.chat_name,
            "state": False,
        }

        return validation_ticket

    def receive(self):
        while True:
            data, address = self.sock.recvfrom(1024)
            message = json.loads(data.decode("utf-8"))

            if self.status == ClientStatus.GROUP_CREATOR:
                print("<", message["sender"], ">", ": ", message["message"], sep="")

                if message.get("state", "") != "wait":
                    self.multicast(message)
                else:
                    print("".join(["Accept user: ", message["sender"], "? [Y/N] "]))
                    self.set_acceptance_ticket(message, address)
            else:
                if self.username != message["sender"]:
                    print("<", message["sender"], ">", ": ", message["message"], sep="")

    def send(self):
        while True:
            try:
                self.message = input()
                ticket = {"message": self.message, "sender": self.username}
                if self.status == ClientStatus.GROUP_CREATOR:
                    if self.wait_acceptance:
                        message, address = (
                            self.wait_acceptance["message"],
                            self.wait_acceptance["address"],
                        )
                        validation_ticket = self.get_validation_ticket(message)

                        if self.message == AcceptanceChoice.NO:
                            self.sock.sendto(
                                json.dumps(validation_ticket).encode("utf-8"), address
                            )
                        else:
                            print(f"User {message['sender']} join chat!")
                            validation_ticket["state"] = True
                            self.sock.sendto(
                                json.dumps(validation_ticket).encode("utf-8"), address
                            )

                        self.wait_acceptance.clear()
                    else:
                        self.multicast(ticket)
                else:
                    self.sock.sendto(
                        json.dumps(ticket).encode("utf-8"), ("", self.chat_identifier)
                    )
            except Exception:
                continue

    def processing(self):
        try:
            self.configure_socket()
            _thread.start_new_thread(self.receive, ())
            self.send()
        except KeyboardInterrupt:
            self.close_socket()
            print("\nGoodbye")

    def configure_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if self.status == ClientStatus.GROUP_CREATOR:
            self.chat_creator_socket_configurations()
            print("Identifier: ", self.generate_identifier())
        else:
            while True:
                accept_ticket = self.accept_chat()

                if accept_ticket.get("state", None):
                    print(f"You join {accept_ticket['chat_name']} chat")
                    self.chat_joiner_socket_configurations(accept_ticket)
                    break
                else:
                    print(f"Access denied for {accept_ticket['chat_name']} chat")

    def chat_creator_socket_configurations(self):
        ttl = struct.pack("b", 1)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        self.update_multicast_group(random.randint(10000, 20000))

        self.chat_name = input("Enter your chat name: ")
        self.sock.sendto("".encode("utf-8"), self.multicast_group)

    def chat_joiner_socket_configurations(self, accept_ticket):
        self.sock.close()
        self.update_multicast_group(accept_ticket["port"])

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.multicast_group)

        mreq = struct.pack(
            "4sL", socket.inet_aton(self.multicast_group[0]), socket.INADDR_ANY
        )
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def update_multicast_group(self, port):
        self.multicast_group = (self.multicast_group[0], port)

    def accept_chat(self):
        ticket = {
            "sender": self.username,
            "state": "wait",
            "message": "Can i accept?",
        }

        self.chat_identifier = int(input("Enter identifier: "))
        self.sock.sendto(json.dumps(ticket).encode("utf-8"), ("", self.chat_identifier))
        data, address = self.sock.recvfrom(1024)

        return json.loads(data.decode("utf-8"))

    def close_socket(self):
        self.sock.close()
