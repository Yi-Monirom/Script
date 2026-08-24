# Network Infrastructure Automation

Ansible automation for the Cisco switches and Huawei USG6000V2 firewall HA pair used in this project.

## Project Layout

```text
Inventory/
  Connection.ini              Ansible inventory and device addresses
  group_vars/                 Local credentials (ignored by Git)
  host_vars/                  Per-device configuration
library/                      Custom Ansible modules
playbooks/
  edge_switches_playbook.yml  Configure edge switches only
  l2_switches_playbook.yml    Configure edge and core switches
  usg_firewall_playbook.yml   Configure the USG active/standby pair
usg.exp                      Expect wrapper for Huawei USG SSH sessions
```

## Requirements

- Linux or macOS
- Python 3
- Ansible
- Ansible collection `cisco.ios`
- OpenSSH client
- `expect` for USG automation
- Network reachability to the management addresses in `Inventory/Connection.ini`

Install the Ansible collection:

```bash
ansible-galaxy collection install cisco.ios
```

On Debian or Ubuntu, install the system tools with:

```bash
sudo apt update
sudo apt install ansible expect openssh-client
```

## Credentials

The following files are intentionally ignored by Git:

```text
Inventory/group_vars/switches.yml
Inventory/group_vars/usg.yml
```

Create or edit them locally. A safe template is available at `Inventory/group_vars/credentials.example`.

`Inventory/group_vars/switches.yml` must define:

```yaml
switch_password: "your-switch-password"
switch_become_password: "your-switch-enable-password"
```

`Inventory/group_vars/usg.yml` must define:

```yaml
usg_password: "your-usg-password"
```

Do not commit real passwords. Rotate any credentials that have previously been stored in Git or shared outside the protected environment.

## Check the Inventory

From this repository directory:

```bash
ansible-inventory -i Inventory/Connection.ini --graph
ansible-inventory -i Inventory/Connection.ini --list
```

The inventory contains these groups:

- `edge_switches`: `sw1` and `sw2`
- `core_switches`: `cs1` and `cs2`
- `switches`: all Cisco switches
- `usg`: both Huawei firewalls

## Validate Before Applying

Syntax-check a playbook before connecting to devices:

```bash
ansible-playbook -i Inventory/Connection.ini --syntax-check playbooks/edge_switches_playbook.yml
ansible-playbook -i Inventory/Connection.ini --syntax-check playbooks/l2_switches_playbook.yml
ansible-playbook -i Inventory/Connection.ini --syntax-check playbooks/usg_firewall_playbook.yml
```

Preview Cisco changes where supported:

```bash
ansible-playbook -i Inventory/Connection.ini --check playbooks/l2_switches_playbook.yml
```

## Run the Cisco Switch Playbooks

Configure only the edge switches:

```bash
ansible-playbook -i Inventory/Connection.ini playbooks/edge_switches_playbook.yml
```

Configure all Cisco switches, including the core switches:

```bash
ansible-playbook -i Inventory/Connection.ini playbooks/l2_switches_playbook.yml
```

The switch playbooks configure VLANs, trunk interfaces, access ports, EtherChannel, and save modified running configurations to startup configuration.

## Run the USG HA Playbook

The USG playbook uses `usg.exp` and runs from the control machine. Confirm SSH access first:

```bash
USG_HOST=192.168.71.100 USG_USER=admin USG_PASS='your-usg-password' \
  ./usg.exp 'display version'
```

Make the wrapper executable if necessary:

```bash
chmod +x usg.exp
```

The default playbook setting is `bootstrap_standby: false`. For the first HA deployment, edit that variable in `playbooks/usg_firewall_playbook.yml` to `true`, run the playbook once, and then set it back to `false`:

```bash
ansible-playbook -i Inventory/Connection.ini playbooks/usg_firewall_playbook.yml
```

The intended order is:

1. Apply the full configuration to the active firewall.
2. Bootstrap the standby heartbeat and HRP configuration on the first deployment.
3. Enable HRP on the active firewall.
4. Verify HRP state on both firewalls.

The management SSH configuration is expected to already exist and is not changed by this playbook.

## Troubleshooting

- `Host key` or SSH failures: verify management IPs, credentials, SSH algorithms, and network reachability.
- `cisco.ios` module not found: run `ansible-galaxy collection install cisco.ios`.
- `expect: command not found`: install the `expect` package.
- USG login timeout: test `./usg.exp 'display version'` directly and verify `USG_HOST`, `USG_USER`, and `USG_PASS`.
- Do not run the USG playbook with `bootstrap_standby: true` after the standby has already entered HRP standby mode unless the device state has been intentionally reset.

## Safety

These playbooks change live network devices. Review the inventory and host variables, verify the topology, and test against a lab device before applying changes to production equipment.

Script/playbooks/l2_switches_playbook.yml