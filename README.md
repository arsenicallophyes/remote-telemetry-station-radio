# Remote Telemetry System (RTS) – Radio Component

The **radio component** of RTS is a long-range, infrastructure-less telemetry system built around **LoRa** for environments where traditional **LoRaWAN** deployment is impractical, costly, or unavailable.

This part of the project focuses on the **networking and protocol layer**: peer discovery, transmission logic, benchmarking, recovery behaviour, and duty-cycle-aware communication. It is designed as a modular foundation for reliable long-range communication without requiring pre-existing infrastructure.

## Overview

RTS is split into two main parts:

- **Radio component** – handles node-to-node communication, protocol behaviour, peer management, benchmarking, transmission control, and recovery logic.
- **Webserver component** – intended to receive, process, and store telemetry data from the base station, while also exposing selected node/network configuration features.

This repository currently focuses on the **radio side**.

<img width="1280" height="720" alt="Slide3" src="https://github.com/user-attachments/assets/4696bb36-90a3-483a-ad06-ae72f409213d" />

## Goals

The radio component is designed to:

- support long-range telemetry without relying on gateways or internet access
- remain compliant with regional duty-cycle regulations
- provide a modular protocol foundation for future mesh-like behaviour
- support benchmarking and routing decisions using measured link quality
- remain adaptable to constrained and lower-cost embedded hardware

## Current Features

The radio component currently supports:

- automatic network join and peer verification
- ETX benchmarking
- RSSI averaging
- data transmission and reception
- ACK and NACK handling
- data recovery mode
- modular packet validation and parsing
- typed, low-coupling architecture

## High-Level Behaviour

### Startup and Join

On startup, a node attempts to discover nearby peers by broadcasting a `NETWORK_JOIN` command.

Nearby nodes validate the request and respond with `NETWORK_ACCEPT`.

The joining node acknowledges the response, allowing both nodes to register each other as known peers.

If no peers are found, the node can enter a low-activity state and retry later.

### Link Benchmarking

After joining, the node benchmarks peer link quality using:

- **ETX (Expected Transmission Count)** for link reliability
- **RSSI averaging** for signal strength estimation

These metrics are intended to be forwarded to the base station to support future routing decisions.

### Runtime

Once startup is complete, the node enters its normal runtime loop:

- listens by default
- transmits only when scheduled or required
- supports control and data flow with recovery-oriented behaviour

The base station behaves differently by listening continuously and only transmitting when issuing commands or sending acknowledgements.

<img width="1280" height="720" alt="Slide5" src="https://github.com/user-attachments/assets/385c9192-3b95-4c55-b48d-9c52ef848b75" />


## Duty-Cycle Compliance

One of the main design goals of RTS is to remain compliant with **duty-cycle regulations**.

This heavily influenced the transmission design. Instead of relying on excessive retransmission behaviour, the protocol separates traffic into two planes:

- **Control traffic**
- **Data traffic**

Control packets use a dedicated channel/band, while data packets are transmitted on the remaining allowed bands.

Before transmission, the system performs airtime and legal wait-time checks in order to select an appropriate band for transmission while preserving future availability.

## Architecture

A major strength of the project is the architecture of the radio codebase.

The system is intentionally modular, with clear separation of responsibilities across areas such as:

- radio handling
- control flow
- data flow
- ETX behaviour
- protocol parsing
- transport logic
- MAC-layer logic

The codebase was designed to remain extensible and compatible with constrained embedded environments, while still maintaining readability and structure.

## Hardware and Software Notes

The prototype was developed using **Challenger RP2040 LoRa 868 MHz** boards.

A compromise had to be made between affordability and software support. The provided library only supported basic send/receive behaviour and required patching to better suit the project’s networking and compliance requirements.

The project also had to work within **CircuitPython** limitations on embedded hardware, which influenced several architecture decisions.

<img width="1280" height="720" alt="Slide4" src="https://github.com/user-attachments/assets/43c3818c-f666-41c4-80ed-87817ef1dcea" />


## Project Status

The radio component is functional, but not yet complete.

### Main Missing Features

- clock synchronization
- SD card integration
- secure transmission
- routing table and path update command
- full webserver-side integration

Of these, **routing table and path update** are the most important missing radio-side features, as they complete the intended routing behaviour of the system.

<img width="1919" height="1035" alt="Untitled" src="https://github.com/user-attachments/assets/9e73faaf-e917-4252-8482-9a0351d519b7" />


## Intended Applications

RTS is not tied to a single domain.

Potential applications include:

- agricultural monitoring
- industrial telemetry
- environmental monitoring
- remote deployments where infrastructure access is limited or too costly

The main value of RTS is in scenarios where long-range communication is needed but the logistics, legality, or cost of traditional infrastructure create constraints.

## Tech Stack

- CircuitPython
- Python
- CubicSDR
- SDRAngel
- Arduino Serial Monitor
- Git
- MyPy (strict)

## Notes

This project focuses strongly on **protocol design**, **modularity**, and **regulation-aware communication** under constrained hardware conditions.

This repository is published for portfolio and review purposes only.
No permission is granted to copy, redistribute, train on, scrape, or reuse this code except where required by law.
