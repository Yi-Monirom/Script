#!/usr/bin/python3
"""Ansible module: usg_ping - test reachability of a Huawei USG6000V2
via the expect wrapper Scripts/usg.exp (interactive AAA auth)."""
import os
import subprocess
from ansible.module_utils.basic import AnsibleModule

# usg.exp is resolved from the invoking working directory (Ansible zips the
# module, so __file__ points into a temp payload dir that is useless here).
_CANDIDATES = (
    "Script/usg.exp",
    os.path.join(os.getcwd(), "Script", "usg.exp"),
    os.path.join(os.getcwd(), "..", "usg.exp"),
    "/home/monirom/Documents/Thesis_project/Infrastructure/Script/usg.exp",
)
DEFAULTS = {
    "usg_host": "192.168.71.100",
    "usg_user": "admin",
    "usg_password": "M@n!r0m@123",
    "timeout": 30,
}


def _find_exp():
    for c in _CANDIDATES:
        if os.path.isfile(c):
            return c
    return None


def main():
    module = AnsibleModule(
        argument_spec={
            "usg_host": {"type": "str", "default": DEFAULTS["usg_host"]},
            "usg_user": {"type": "str", "default": DEFAULTS["usg_user"]},
            "usg_password": {"type": "str", "default": DEFAULTS["usg_password"], "no_log": True},
            "timeout": {"type": "int", "default": DEFAULTS["timeout"]},
        },
        supports_check_mode=True,
    )
    host = module.params["usg_host"]

    env = os.environ.copy()
    env["USG_HOST"] = host
    env["USG_USER"] = module.params["usg_user"]
    env["USG_PASS"] = module.params["usg_password"]
    env["USG_TIMEOUT"] = str(module.params["timeout"])

    exp = _find_exp()
    if exp is None:
        module.fail_json(msg="usg.exp not found (looked in %s)" % ", ".join(_CANDIDATES))

    try:
        proc = subprocess.run(
            ["expect", exp, "display version"],
            env=env, capture_output=True, text=True, timeout=module.params["timeout"] + 10,
        )
    except subprocess.TimeoutExpired:
        module.fail_json(msg="connection to %s timed out" % host)

    if proc.returncode == 0:
        module.exit_json(changed=False, ping="pong", stdout=proc.stdout.strip())
    else:
        module.fail_json(msg="cannot reach %s (returncode %s)" % (host, proc.returncode),
                         stderr=proc.stderr.strip())

if __name__ == "__main__":
    main()