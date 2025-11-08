# Prototype script

graph = {
    "Base": {"A": 4.5, "B": 4, "C": 3.6},
    "A": {"Base": 4.5, "B": 2.5, "E": 1.9},
    "B": {"A": 2.5, "Base": 4, "C": 1, "E": 1.7, "D": 2.8, "G": 5},
    "C": {"B": 1, "Base": 3.6, "E": 3.8, "J": 2.5, "G": 3.9},
    "D": {"E": 2.1, "B": 2.8, "C": 3.7, "G": 4.5},
    "E": {"A": 1.9, "B": 1.7, "C": 3.8, "D": 2.1},
    "F": {"J": 2, "G": 4.1},
    "G": {"D": 4.5, "B": 5, "C": 3.9, "J": 1.8, "F": 4.1},
    "J": {"C": 2.5, "F": 2, "G": 1.8}
}


RSSI_LOW = -80
RSSI_HIGH = -110
packets = int(input("Number of Packets: "))
transmitted_forward_packets = int(input("Number of transmitted packets while forwarding: "))
if transmitted_forward_packets < packets:
    print(f"Error, impossible to send {packets} packets in {transmitted_forward_packets} transmissions")
    exit()

transmitted_reverse_packets = int(input("Number of transmitted packets while receiving: "))


if transmitted_reverse_packets < packets:
    print(f"Error, impossible to send {packets} packets in {transmitted_reverse_packets} transmissions")
    exit()


df = packets/transmitted_forward_packets

dr = packets/transmitted_reverse_packets

ETX = 1/(dr*df)

RSSI = int(input("RSSI: "))

if RSSI >= RSSI_LOW:
    cost = 0
elif RSSI <= RSSI_HIGH:
    print("Abort Link")
    exit()
else:
    x = (RSSI - RSSI_LOW)/(RSSI_HIGH-RSSI_LOW)
    cost = (x**2 * (3-2*x)) * 0.2


print(f"{ETX=}, {cost=}, Total Cost={ETX * 0.75 + cost + 0.05}")

