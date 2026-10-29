"""Docker smoke test; set ADDON_TEST_IMAGE to an already-built add-on image.

Uses disposable named volumes and no network or published ports. Exercises the
real entrypoint, SQLite, HTTP server, and go2rtc, including container recreation.
"""

import json
import os
import subprocess
import time
import unittest
import uuid


IMAGE = os.environ.get("ADDON_TEST_IMAGE", "lightnvr-addon:issue688")


def docker(*args, check=True):
    result = subprocess.run(
        ["docker", *args], text=True, capture_output=True, timeout=90
    )
    if check and result.returncode:
        raise AssertionError(f"docker {args[0]} failed:\n{result.stdout}\n{result.stderr}")
    return result.stdout.strip()


class ContainerTest(unittest.TestCase):
    def setUp(self):
        self.name = "lightnvr-test-" + uuid.uuid4().hex[:12]
        self.volumes = [self.name + "-data", self.name + "-media"]
        for volume in self.volumes:
            docker("volume", "create", volume)
        self.mounts = ["-v", self.volumes[0] + ":/data",
                       "-v", self.volumes[1] + ":/media"]

    def tearDown(self):
        docker("rm", "-f", "-v", self.name, check=False)
        for volume in self.volumes:
            docker("volume", "rm", volume, check=False)

    def prepare(self, script):
        return docker("run", "--rm", "--network", "none", *self.mounts,
                      "--entrypoint", "/bin/sh", IMAGE, "-ec", script)

    def run_shell(self, script, user="10001:10001"):
        return docker("exec", "--user", user, self.name, "/bin/sh", "-ec", script)

    def start(self, port):
        docker("run", "-d", "--name", self.name, "--network", "none",
               *self.mounts, IMAGE)
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            result = subprocess.run(
                ["docker", "exec", "--user", "10001:10001", self.name,
                 "curl", "-fsS", f"http://127.0.0.1:{port}/"],
                capture_output=True, timeout=5,
            )
            if result.returncode == 0:
                break
            if docker("inspect", "-f", "{{.State.Running}}", self.name) != "true":
                self.fail(docker("logs", self.name))
            time.sleep(1)
        else:
            self.fail("HTTP startup timed out:\n" + docker("logs", self.name))
        self.run_shell("/ha-health.sh")
        self.assertEqual(self.run_shell("cat /run/lightnvr/web_port"), str(port))
        # Read the real processes, not docker exec's selected UID.
        status = self.run_shell("""
            for name in lightnvr go2rtc; do
                found=false
                for comm in /proc/[0-9]*/comm; do
                    [ "$(cat "$comm" 2>/dev/null)" = "$name" ] || continue
                    found=true
                    awk '/^Uid:|^Gid:/{print $2, $3, $4, $5}' "${comm%comm}status"
                done
                "$found"
            done
        """)
        self.assertEqual(status.splitlines(), ["10001 10001 10001 10001"] * 4)
        self.assertEqual(len(json.loads(docker("inspect", self.name))[0]["Mounts"]), 2)

    def stop(self):
        docker("stop", "-t", "15", self.name)
        docker("rm", "-v", self.name)

    def test_fresh_install_upgrade_and_recreation(self):
        config = json.loads(docker("image", "inspect", IMAGE))[0]["Config"]
        self.assertFalse(config.get("Volumes"), "upstream volumes must not be inherited")
        # Supervisor's private data directory can be root-owned and mode 0700.
        self.prepare("chmod 700 /data")
        self.start(7800)
        self.run_shell("""
            test -s /data/config/lightnvr.ini
            test -s /data/lib/database/lightnvr.db
            for dir in /etc/lightnvr/go2rtc /var/lib/lightnvr/data/database \
                       /var/lib/lightnvr/data/models /var/lib/lightnvr/data/recordings/mp4; do
                touch "$dir/probe"
                rm "$dir/probe"
            done
        """)
        self.stop()

        # Represent an existing installation from before the non-root change.
        self.prepare("""
            printf '%s' '{"web_port":7801,"go2rtc_config_persist":false}' > /data/options.json
            sed -i 's@/var/run/lightnvr/lightnvr.pid@/var/run/lightnvr.pid@' /data/config/lightnvr.ini
            printf '\n# upgrade sentinel\n' >> /data/config/lightnvr.ini
            printf '# private override\nlog:\n  level: info\n' > /data/config/go2rtc/override.yaml
            printf 'model sentinel' > /data/lib/models/sentinel
            sqlite3 /data/lib/database/lightnvr.db \
                "CREATE TABLE addon_upgrade_probe (value TEXT); INSERT INTO addon_upgrade_probe VALUES ('preserved');
                 INSERT OR REPLACE INTO system_settings (key, value)
                 VALUES ('go2rtc_config_override', CAST(readfile('/data/config/go2rtc/override.yaml') AS TEXT));"
            mkdir -p /media/lightnvr/recordings/mp4/test-camera /media/other-addon
            printf 'old segment' > /media/lightnvr/recordings/mp4/test-camera/old.mp4
            printf 'unrelated' > /media/other-addon/keep
            chown -R 0:0 /data /media
            chmod 600 /data/config/lightnvr.ini /data/config/go2rtc/override.yaml \
                /data/lib/models/sentinel /media/other-addon/keep
        """)
        self.start(7801)
        self.assertIn("go2rtc_persist=false", docker("logs", self.name))
        self.assertEqual(self.run_shell("""
            sqlite3 /data/lib/database/lightnvr.db 'SELECT value FROM addon_upgrade_probe'
        """), "preserved")
        self.run_shell("""
            grep -q '# upgrade sentinel' /data/config/lightnvr.ini
            grep -q '^pid_file = /var/run/lightnvr/lightnvr.pid$' /data/config/lightnvr.ini
            grep -q 'private override' /data/config/go2rtc/override.yaml
            test "$(cat /data/lib/models/sentinel)" = 'model sentinel'
            for file in /data/config/lightnvr.ini /data/config/go2rtc/override.yaml /data/lib/models/sentinel; do
                test "$(stat -c '%u:%g:%a' "$file")" = '10001:10001:600'
            done
            test "$(stat -c '%u:%g' /media/lightnvr/recordings/mp4/test-camera/old.mp4)" = '0:0'
            test "$(cat /media/lightnvr/recordings/mp4/test-camera/old.mp4)" = 'old segment'
            # Same permission needed for retention of old root-owned segments.
            rm /media/lightnvr/recordings/mp4/test-camera/old.mp4
            touch /media/lightnvr/recordings/mp4/test-camera/new.mp4
        """)
        self.assertEqual(self.run_shell(
            "stat -c '%u:%g:%a' /media/other-addon/keep", user="0:0"), "0:0:600")
        self.stop()
        self.start(7801)
        self.run_shell("test -f /media/lightnvr/recordings/mp4/test-camera/new.mp4")
        self.assertEqual(self.run_shell("""
            sqlite3 /data/lib/database/lightnvr.db 'SELECT value FROM addon_upgrade_probe'
        """), "preserved")


if __name__ == "__main__":
    unittest.main(verbosity=2)
