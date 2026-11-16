"""Client for the emulator's control interface (see src/control.rs).

One JSON object per line over TCP. Requests carry an id; the matching response
arrives once the command has finished. Lines without an id are events.
"""

import json
import socket
import time


class ControlError(Exception):
    """The emulator answered a command with ok=false."""


class ControlGone(Exception):
    """The connection to the emulator was lost or timed out."""


class Control:
    def __init__(self, port, host="127.0.0.1", connect_timeout=30.0):
        self.host, self.port = host, port
        self.sock = None
        self.buf = b""
        self.next_id = 1
        self.events = []
        self.hello = None
        deadline = time.time() + connect_timeout
        last_error = None
        while time.time() < deadline:
            try:
                self.sock = socket.create_connection((host, port), timeout=2.0)
                break
            except OSError as e:
                last_error = e
                time.sleep(0.2)
        if self.sock is None:
            raise ControlGone(f"could not connect to {host}:{port}: {last_error}")
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def close(self):
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _read_line(self, timeout):
        deadline = time.time() + timeout
        while b"\n" not in self.buf:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise ControlGone(f"no reply from the emulator within {timeout:.0f}s")
            self.sock.settimeout(min(remaining, 1.0))
            try:
                chunk = self.sock.recv(65536)
            except socket.timeout:
                continue
            except OSError as e:
                raise ControlGone(f"connection lost: {e}")
            if not chunk:
                raise ControlGone("the emulator closed the connection")
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        return json.loads(line.decode("utf-8"))

    def command(self, cmd, timeout=30.0, **args):
        """Send a command and wait for its response. Returns the response dict."""
        request = {"id": self.next_id, "cmd": cmd}
        request.update({k: v for k, v in args.items() if v is not None})
        self.next_id += 1
        try:
            self.sock.sendall(json.dumps(request).encode("utf-8") + b"\n")
        except OSError as e:
            raise ControlGone(f"connection lost: {e}")
        while True:
            message = self._read_line(timeout)
            if "event" in message:
                if message["event"] == "hello":
                    self.hello = message
                else:
                    self.events.append(message)
                continue
            if message.get("id") != request["id"]:
                continue  # stale response from an earlier, abandoned command
            if not message.get("ok"):
                raise ControlError(message.get("error", "unknown error"))
            return message

    def drain_events(self):
        """Events received so far (they arrive alongside command responses)."""
        self.command("ping")
        events, self.events = self.events, []
        return events

    # Convenience wrappers -------------------------------------------------

    def ping(self):
        return self.command("ping", timeout=10.0)

    def tap(self, x, y, hold_frames=None, finger=None):
        return self.command("tap", x=x, y=y, hold_frames=hold_frames, finger=finger)

    def drag(self, x1, y1, x2, y2, frames=None, finger=None):
        return self.command(
            "drag", x1=x1, y1=y1, x2=x2, y2=y2, frames=frames, finger=finger, timeout=120.0
        )

    def touch(self, phase, x, y, finger=None):
        return self.command("touch", phase=phase, x=x, y=y, finger=finger)

    def stroke(self, points, step=14.0, frames_per_step=1, finger=None):
        """Draw a path through `points` with one finger: down at the first
        point, moves about `step` points apart, up at the last."""
        x, y = points[0]
        self.touch("down", x, y, finger)
        self.wait_frames(2)
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
            steps = max(1, round(length / step))
            for i in range(1, steps + 1):
                t = i / steps
                self.touch("move", x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, finger)
                self.wait_frames(frames_per_step)
        self.wait_frames(2)
        self.touch("up", *points[-1], finger)
        return self.wait_frames(2)

    def wait_frames(self, frames):
        return self.command("wait", frames=frames, timeout=30.0 + frames * 0.2)

    def wait_ms(self, ms):
        return self.command("wait", ms=ms, timeout=30.0 + ms / 1000.0)

    def tilt(self, x, y):
        return self.command("tilt", x=x, y=y)

    def tilt_clear(self):
        return self.command("tilt", clear=True)

    def accel(self, x, y, z):
        return self.command("accel", x=x, y=y, z=z)

    def accel_clear(self):
        return self.command("accel", clear=True)

    def screenshot(self, path, timeout_ms=3000):
        return self.command(
            "screenshot", path=str(path), timeout_ms=timeout_ms, timeout=timeout_ms / 1000.0 + 10.0
        )

    def nodes(self, ptr=None, depth=None, max_nodes=None):
        return self.command("nodes", ptr=ptr, depth=depth, max_nodes=max_nodes)["root"]

    def views(self, depth=None):
        return self.command("views", depth=depth)["windows"]

    def find(self, class_name, subclasses=True, limit=None):
        return self.command("find", **{"class": class_name}, subclasses=subclasses, limit=limit)

    def describe(self, ptr):
        return self.command("describe", ptr=ptr)

    def read(self, ptr, ivar, type_):
        return self.command("read", ptr=ptr, ivar=ivar, type=type_)["value"]

    def read_addr(self, addr, type_):
        return self.command("read", addr=addr, type=type_)["value"]

    def call(self, selector, ptr=None, class_name=None, returns="id"):
        args = {"selector": selector, "returns": returns, "ptr": ptr}
        if class_name is not None:
            args["class"] = class_name
        return self.command("call", **args)["value"]

    def watch(self, *selectors):
        return self.command("watch", selectors=list(selectors))

    def unwatch(self, *selectors):
        return self.command("unwatch", selectors=list(selectors) or None)

    def profile(self, ms=3000, top=40):
        """Profile the emulator for `ms` milliseconds; see harness/profile.py."""
        self.command("profile", action="start")
        self.wait_ms(ms)
        return self.command("profile", action="stop", top=top)

    def quit(self):
        try:
            return self.command("quit", timeout=5.0)
        except ControlGone:
            return None
