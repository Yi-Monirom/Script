# Network Infrastructure Automation Suite

Enterprise Ansible automation, Expect CLI drivers, and diagnostic tools for Cisco Core/Edge switches, Huawei USG6000V2 Next-Generation Firewall HA Cluster, and DMZ Suricata IDS.

---

## 1. Project Directory Layout

```text
Script/
├── .gitignore                       # Protects vault credentials and transient outputs
├── README.md                        # Master documentation and operations runbook
├── notes.md                         # Reference architecture notes (IPsec, ACLs)
├── moniom.cfg                       # [PROTECTED] Golden baseline configuration (542 lines)
├── firewall_security_policies.conf  # Human-readable reference of USG security policies
├── usg.exp                          # Interactive Expect wrapper for Huawei USG CLI
├── sftp_get.exp                     # Expect-driven SFTP configuration retrieval engine
│
├── Inventory/                       # Ansible Inventory & Variable Definitions
│   ├── Connection.ini               # Host definitions, management IPs & group hierarchy
│   ├── group_vars/                  # Group-level variables and credential overrides
│   │   ├── credentials.example      # Safe credential template
│   │   ├── switches.yml             # Cisco switch credentials (git-ignored)
│   │   ├── usg.yml                  # Huawei USG credentials (git-ignored)
│   │   └── dmz.yml                  # DMZ Suricata server configuration
│   └── host_vars/                   # Per-device VLAN, trunk, IP, and LACP configuration
│       ├── cs1.yml / cs2.yml        # Cisco Core Switch 1 & 2 variables
│       ├── sw1.yml / sw2.yml        # Cisco Edge Switch 1 & 2 variables
│       └── usg6000v2.yml / usg6000v2-2.yml # Primary & Standby USG variables
│
├── playbooks/                       # Ansible Orchestration Playbooks
│   ├── usg_firewall_playbook.yml    # USG HA, sub-interfaces, static routes, NAT, security policies
│   ├── l2_switches_playbook.yml     # Cisco Core & Edge switches (VLANs, Trunks, EtherChannels)
│   ├── edge_switches_playbook.yml   # Cisco Edge switches only (SW1 & SW2)
│   ├── ids_suricata_playbook.yml    # DMZ Suricata IDS rules deployment & engine validation
│   └── test_connection.yml          # Network reachability and AAA authentication tests
│
├── library/                         # Custom Ansible Modules
│   └── usg_ping.py                  # AAA-compatible ping verification module for Huawei USG
│
├── files/                           # Static Configuration Assets
│   └── thesis.rules                 # Custom Suricata IDS signature detection rules
│
├── backups/                         # Automated Device Configuration Dumps
│   ├── switches/                    # Cisco running configuration archives
│   └── usg/                         # Huawei USG XML/CFG configuration archives
│
└── tools/                           # Diagnostic & Operational Utilities
    ├── scan_ips.sh                  # Multi-threaded parallel subnet scanner (192.168.71.0/24)
    ├── lab_vpn_setup.sh             # FortiClient routing & socat UDP relay configuration
    ├── recover_relay.sh             # DMZ relay VM recovery helper
    └── recover_server.sh            # DMZ WireGuard VPN server recovery helper
```

---

## 2. Requirements & Prerequisites

### System Packages
```bash
sudo apt update
sudo apt install -y ansible expect openssh-client python3-netaddr
```

### Ansible Galaxy Collections
```bash
ansible-galaxy collection install cisco.ios
```

---

## 3. Credentials & Inventory Setup

1. Copy the credentials template:
   ```bash
   cp Inventory/group_vars/credentials.example Inventory/group_vars/switches.yml
   cp Inventory/group_vars/credentials.example Inventory/group_vars/usg.yml
   ```
2. Configure credentials in `Inventory/group_vars/switches.yml` and `Inventory/group_vars/usg.yml`. These files are protected by `.gitignore` to prevent credential exposure.

3. Verify inventory host mapping:
   ```bash
   ansible-inventory -i Inventory/Connection.ini --graph
   ```

---

## 4. Playbooks & Execution Guide

### Syntax Check All Playbooks
```bash
ansible-playbook -i Inventory/Connection.ini --syntax-check playbooks/edge_switches_playbook.yml
ansible-playbook -i Inventory/Connection.ini --syntax-check playbooks/l2_switches_playbook.yml
ansible-playbook -i Inventory/Connection.ini --syntax-check playbooks/ids_suricata_playbook.yml
ansible-playbook -i Inventory/Connection.ini --syntax-check playbooks/test_connection.yml
ansible-playbook -i Inventory/Connection.ini --syntax-check playbooks/usg_firewall_playbook.yml
```

### Playbook Descriptions

| Playbook | Target Hosts | Description | Command |
| :--- | :--- | :--- | :--- |
| **`usg_firewall_playbook.yml`** | `localhost` $\rightarrow$ USG Cluster | Configures Huawei USG Active/Standby HA, WAN sub-interfaces (GE1/0/1.10, GE1/0/1.20), Trust/DMZ interfaces, static routing, NAT Server (`10.1.1.2:51820`), and all security policies. | `ansible-playbook -i Inventory/Connection.ini playbooks/usg_firewall_playbook.yml` |
| **`l2_switches_playbook.yml`** | `switches` (`cs1, cs2, sw1, sw2`) | Configures VLANs 10, 20, 30, 40, 71, 100, 200, 300, 802.1Q trunks, LACP Port-Channels (Po1, Po2, Po12, Po34), SVI management, and saves startup configs. | `ansible-playbook -i Inventory/Connection.ini playbooks/l2_switches_playbook.yml` |
| **`edge_switches_playbook.yml`** | `edge_switches` (`sw1, sw2`) | Targets only WAN Edge switches for fast convergence testing. | `ansible-playbook -i Inventory/Connection.ini playbooks/edge_switches_playbook.yml` |
| **`ids_suricata_playbook.yml`** | `dmz` (Suricata VM) | Idempotently pushes `files/thesis.rules` (MD5 verification) to `/etc/suricata/rules/thesis.rules` and reloads the engine. | `ansible-playbook -i Inventory/Connection.ini playbooks/ids_suricata_playbook.yml` |
| **`test_connection.yml`** | `all` | Verifies end-to-end SSH and AAA connectivity. | `ansible-playbook -i Inventory/Connection.ini playbooks/test_connection.yml` |

---

## 5. Expect CLI Drivers (`usg.exp` & `sftp_get.exp`)

The Huawei USG6000V2 utilizes an interactive AAA authentication prompt. The Expect scripts provide seamless automation:

```bash
# Execute a single view command
USG_HOST=192.168.71.100 USG_USER=admin USG_PASS='password' ./usg.exp 'display hrp state'

# Pull running configuration backup via SFTP
./sftp_get.exp
```

---

## 6. Operational & Diagnostic Tools (`tools/`)

| Script | Purpose | Usage Example |
| :--- | :--- | :--- |
| **`tools/scan_ips.sh`** | Parallel multi-threaded IP scanner for `192.168.71.0/24`. Detects active hosts and identifies consecutive free blocks. | `./tools/scan_ips.sh` *(or `./tools/scan_ips.sh 100 110`)* |
| **`tools/lab_vpn_setup.sh`** | Configures local routes and `socat` UDP relay when connecting through FortiClient VPN. | `sudo ./tools/lab_vpn_setup.sh` |
| **`tools/recover_relay.sh`** | Re-establishes DMZ UDP relay routing on the test VM. | `./tools/recover_relay.sh` |
| **`tools/recover_server.sh`** | Restores WireGuard server configuration on the DMZ node. | `./tools/recover_server.sh` |

---

## 7. Configuration Safety Guidelines

- **Golden Baseline:** `moniom.cfg` is the verified golden reference configuration. Do not modify or overwrite this file.
- **Automated Backups:** Playbooks automatically export timestamped backups into `backups/switches/` and `backups/usg/` before applying any state changes.