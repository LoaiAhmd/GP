from __future__ import annotations

"""
Live flow capture using CICFlowMeter's Flow class directly.

Instead of running the broken CICFlowMeter CLI subprocess and tailing
a CSV file, this module uses scapy's AsyncSniffer with CICFlowMeter's
Flow objects to extract real network-flow features in-process.

A background thread periodically garbage-collects expired flows and
pushes their feature dicts into a thread-safe queue for the main loop.
"""

import queue
import threading
import time
from decimal import Decimal

from scapy.all import AsyncSniffer

from cicflowmeter.features.context.packet_direction import PacketDirection
from cicflowmeter.features.context.packet_flow_key import get_packet_flow_key
from cicflowmeter.flow import Flow

from config import CAPTURE_INTERFACE, FLOW_EXPIRED_SECONDS, GC_INTERVAL, VERBOSE_GC


class LiveFlowCapture:
    """
    Captures packets on a network interface and extracts CICFlowMeter
    flow features in real-time.

    Completed flows are placed into self.flow_queue as dicts
    (column_name -> value), ready for feature parsing.
    """

    def __init__(
        self,
        interface: str = CAPTURE_INTERFACE,
        expired_seconds: float = FLOW_EXPIRED_SECONDS,
        gc_interval: float = GC_INTERVAL,
    ):
        self.interface = interface
        self.expired_seconds = expired_seconds
        self.gc_interval = gc_interval

        # Active flows being assembled from packets
        self._flows: dict = {}
        self._flows_lock = threading.Lock()

        # Completed flows ready for processing
        self.flow_queue: queue.Queue = queue.Queue()

        self._sniffer: AsyncSniffer | None = None
        self._gc_thread: threading.Thread | None = None
        self._running = False

        # Stats
        self.packets_seen = 0
        self.flows_extracted = 0

    # -- public API ------------------------------------------

    def start(self) -> None:
        """Start packet capture and the garbage-collector thread."""
        self._running = True

        print(
            f"[CAPTURE] Sniffing on interface '{self.interface}' "
            f"(flow timeout={self.expired_seconds}s, gc interval={self.gc_interval}s)",
            flush=True,
        )

        # Start scapy async sniffer
        self._sniffer = AsyncSniffer(
            iface=self.interface,
            filter="ip and (tcp or udp)",
            prn=self._on_packet,
            store=False,
        )
        self._sniffer.start()

        # Start garbage-collector thread
        self._gc_thread = threading.Thread(
            target=self._gc_loop, daemon=True, name="flow-gc"
        )
        self._gc_thread.start()

        print("[OK] Packet capture active", flush=True)

    def stop(self) -> None:
        """Stop capture and extract remaining flows."""
        self._running = False
        if self._sniffer is not None:
            self._sniffer.stop()
            self._sniffer = None

        # Final garbage collection to flush any remaining flows
        self._garbage_collect(force_all=True)

        print(
            f"[STOP] Capture stopped. "
            f"Packets={self.packets_seen}, Flows={self.flows_extracted}",
            flush=True,
        )

    # -- packet callback -------------------------------------

    def _on_packet(self, packet) -> None:
        """Called by scapy for each captured packet."""
        if "IP" not in packet:
            return
        if "TCP" not in packet and "UDP" not in packet:
            return

        # Convert packet.time to Decimal to avoid float/Decimal
        # incompatibility in CICFlowMeter's Flow.add_packet()
        packet.time = Decimal(str(packet.time))

        self.packets_seen += 1

        direction = PacketDirection.FORWARD
        count = 0

        try:
            packet_flow_key = get_packet_flow_key(packet, direction)
        except Exception:
            return

        with self._flows_lock:
            flow = self._flows.get((packet_flow_key, count))

            if flow is None:
                # Check reverse direction
                direction = PacketDirection.REVERSE
                try:
                    packet_flow_key = get_packet_flow_key(packet, direction)
                except Exception:
                    return
                flow = self._flows.get((packet_flow_key, count))

                if flow is None:
                    # Brand new flow
                    direction = PacketDirection.FORWARD
                    packet_flow_key = get_packet_flow_key(packet, direction)
                    flow = Flow(packet, direction)
                    self._flows[(packet_flow_key, count)] = flow

            # Add packet to the flow
            try:
                flow.add_packet(packet, direction)
            except Exception:
                pass

    # -- garbage collection ----------------------------------

    def _gc_loop(self) -> None:
        """Background thread that periodically collects expired flows."""
        while self._running:
            time.sleep(self.gc_interval)
            self._garbage_collect(force_all=False)

    def _garbage_collect(self, force_all: bool = False) -> None:
        """
        Extract feature data from flows that have expired.

        A flow is considered expired when no packet has been seen for
        it in the last `expired_seconds` seconds.

        If force_all is True, extract ALL flows (used at shutdown).
        """
        now = Decimal(str(time.time()))
        extracted = 0

        with self._flows_lock:
            keys = list(self._flows.keys())
            for k in keys:
                flow = self._flows.get(k)
                if flow is None:
                    continue

                is_expired = (now - flow.latest_timestamp) > self.expired_seconds
                is_long = flow.duration > 90

                if force_all or is_expired or is_long:
                    try:
                        data = flow.get_data()
                        self.flow_queue.put(data)
                        extracted += 1
                        self.flows_extracted += 1
                    except Exception as e:
                        print(f"[WARN] Failed to extract flow: {e}", flush=True)
                    del self._flows[k]

        if VERBOSE_GC and extracted > 0:
            print(
                f"[GC] Extracted {extracted} flow(s), "
                f"{len(self._flows)} active, "
                f"{self.flow_queue.qsize()} queued",
                flush=True,
            )
