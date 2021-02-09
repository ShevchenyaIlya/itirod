import os

from client import Client
from client_status import ClientStatus


class UI:
    def __init__(self):
        self.choice = -1
        self.choice_actions = {
            "1": self.create_group,
            "2": self.join_group,
            "3": self.exit,
        }

    def communicate(self):
        os.system("clear")
        username = input("Enter your username: ")

        print(
            f"\nWelcome {username} to best group chat!\n"
            "1. Create group\n"
            "2. Join group\n"
            "3. Exit"
        )
        choice = self.choice_actions.get(input("Choice: "), None)

        if choice is not None:
            choice(username)
        else:
            print("Incorrect user input!")

    def create_group(self, username):
        Client(ClientStatus.GROUP_CREATOR, username).processing()

    def join_group(self, username):
        Client(ClientStatus.GROUP_JOINER, username).processing()

    @staticmethod
    def exit(username):
        print(f"Thanks for visiting {username}")


if __name__ == "__main__":
    interface = UI()
    interface.communicate()
