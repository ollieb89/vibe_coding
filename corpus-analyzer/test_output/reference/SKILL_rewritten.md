---
title: Pentest Commands
source: skills/pentest-commands/SKILL.md
---

# Pentesting Commands Reference

This document provides a comprehensive guide to various pentesting commands and tools, categorized into different sections for easy navigation. Each section includes examples of how to use the respective tool or command.

## 1. Nmap

Nmap is a versatile network scanning tool used for discovering hosts and services on a computer network.

### Basic Scan
```bash
nmap 192.168.1.1
```

### Fast Scan with Version Information
```bash
nmap -sV 192.168.1.1
```

[source: skills/pentest-commands/SKILL.md#nmap]

---

## 2. Metasploit

Metasploit is a penetration testing framework that provides numerous tools for exploiting, analyzing, and reporting vulnerabilities.

### Exploit Execution
```bash
msfconsole
use exploit/windows/smb/ms17_010_eternalblue
set RHOST 192.168.1.1
exploit
```

[source: skills/pentest-commands/SKILL.md#metasploit]

---

## 3. Nikto

Nikto is a web server scanner for identifying vulnerabilities on web servers.

### Basic Scan
```bash
nikto -h http://192.168.1.1
```

### Comprehensive Scan
```bash
nikto -h http://192.168.1.1 -C all
```

[source: skills/pentest-commands/SKILL.md#nikto]

---

## 4. SQLMap

SQLMap is a powerful tool used for detecting and exploiting SQL injection vulnerabilities in web applications.

### Basic Injection Test
```bash
sqlmap -u "http://192.168.1.1/page?id=1"
```

### Enumerate Databases
```bash
sqlmap -u "http://192.168.1.1/page?id=1" --dbs
```

[source: skills/pentest-commands/SKILL.md#sqlmap]

---

## 5. Hydra

Hydra is a password cracking tool that supports various protocols and authentication methods.

### SSH Brute Force
```bash
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://192.168.1.1
```

[source: skills/pentest-commands/SKILL.md#hydra]

---

## 6. John the Ripper

John the Ripper is a password cracking tool that supports various encryption formats and wordlists.

### Crack Password File
```bash
john hash.txt
```

### SSH Key Passphrase
```bash
ssh2john id_rsa > ssh_hash.txt
john ssh_hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

[source: skills/pentest-commands/SKILL.md#john-the-ripper]

---

## 7. Aircrack-ng

Aircrack-ng is a suite of tools for wireless network analysis, cracking WEP and WPA keys, and monitoring WiFi traffic.

### Capture Packets
```bash
airmon-ng start wlan0
airodump-ng wlan0mon
```

[source: skills/pentest-commands/SKILL.md#aircrack-ng]

---

## 8. Wireshark/Tshark

Wireshark is a graphical network protocol analyzer, while Tshark is the command-line version of the same tool.

### Capture Traffic
```bash
tshark -i eth0 -w capture.pcap
```

[source: skills/pentest-commands/SKILL.md#wireshark]