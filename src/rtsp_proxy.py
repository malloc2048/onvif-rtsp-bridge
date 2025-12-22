"""RTSP Proxy for forwarding streams from HikVision to ONVIF clients."""

import asyncio
import logging
import subprocess
import os
from typing import Optional

from src.config import Config

logger = logging.getLogger(__name__)


class RtspProxy:
    """RTSP Proxy using mediamtx + FFmpeg for stream forwarding."""

    def __init__(self, config: Config):
        self.config = config
        self.mediamtx_process: Optional[subprocess.Popen] = None
        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.running = False
        self.monitor_task = None

    async def start(self):
        """Start the RTSP proxy server."""
        self.running = True

        # Start mediamtx RTSP server
        await self._start_mediamtx()

        # Wait for mediamtx to be ready
        await asyncio.sleep(2)

        # Start FFmpeg to push stream to mediamtx
        await self._start_ffmpeg()

        # Start monitoring task
        self.monitor_task = asyncio.create_task(self._monitor())

        logger.info(f"RTSP Proxy started - proxying {self.config.rtsp_url_masked}")
        logger.info(f"Stream available at: {self.config.proxy_rtsp_url}")

    async def stop(self):
        """Stop the RTSP proxy server."""
        self.running = False

        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        # Stop FFmpeg first
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()
            self.ffmpeg_process = None

        # Then stop mediamtx
        if self.mediamtx_process:
            self.mediamtx_process.terminate()
            try:
                self.mediamtx_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.mediamtx_process.kill()
            self.mediamtx_process = None

        logger.info("RTSP Proxy stopped")

    async def _start_mediamtx(self):
        """Start mediamtx RTSP server."""
        # Create minimal mediamtx config
        config_content = f"""
logLevel: warn
logDestinations: [stdout]

rtsp: yes
rtspAddress: :{self.config.rtsp_proxy_port}
protocols: [tcp]

paths:
  stream:
    source: publisher
"""
        config_path = "/tmp/mediamtx.yml"
        with open(config_path, 'w') as f:
            f.write(config_content)

        cmd = ['mediamtx', config_path]

        logger.info(f"Starting mediamtx RTSP server on port {self.config.rtsp_proxy_port}")

        try:
            self.mediamtx_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setpgrp if hasattr(os, 'setpgrp') else None
            )

            await asyncio.sleep(1)

            if self.mediamtx_process.poll() is not None:
                stderr = self.mediamtx_process.stderr.read().decode('utf-8', errors='ignore')
                logger.error(f"mediamtx failed to start: {stderr[:500]}")
                raise RuntimeError("mediamtx failed to start")

            logger.info("mediamtx RTSP server started")

        except FileNotFoundError:
            logger.error("mediamtx not found - install it or use Docker")
            raise

    async def _start_ffmpeg(self):
        """Start FFmpeg to push stream to mediamtx."""
        cmd = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'warning',

            # Input options
            '-rtsp_transport', 'tcp',
            '-i', self.config.rtsp_url,

            # Re-encoding options (passthrough for lowest latency)
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-an',  # Disable audio for simplicity

            # Output to mediamtx
            '-f', 'rtsp',
            '-rtsp_transport', 'tcp',
            f'rtsp://127.0.0.1:{self.config.rtsp_proxy_port}/stream'
        ]

        logger.info(f"Starting FFmpeg: {' '.join(cmd[:8])}...")

        try:
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setpgrp if hasattr(os, 'setpgrp') else None
            )

            await asyncio.sleep(2)

            if self.ffmpeg_process.poll() is not None:
                stderr = self.ffmpeg_process.stderr.read().decode('utf-8', errors='ignore')
                logger.error(f"FFmpeg failed: {stderr[:500]}")
            else:
                logger.info("FFmpeg stream relay started")

        except FileNotFoundError:
            logger.error("FFmpeg not found")
            raise
        except Exception as e:
            logger.error(f"Error starting FFmpeg: {e}")
            raise

    async def _monitor(self):
        """Monitor FFmpeg process and restart if needed."""
        restart_delay = 5

        while self.running:
            await asyncio.sleep(10)

            # Check mediamtx
            if self.mediamtx_process and self.mediamtx_process.poll() is not None:
                logger.error("mediamtx died, restarting...")
                await self._start_mediamtx()
                await asyncio.sleep(2)

            # Check FFmpeg
            if self.ffmpeg_process and self.ffmpeg_process.poll() is not None:
                logger.warning(f"FFmpeg process died (code: {self.ffmpeg_process.returncode}), restarting...")

                if self.ffmpeg_process.stderr:
                    stderr = self.ffmpeg_process.stderr.read()
                    if stderr:
                        logger.error(f"FFmpeg stderr: {stderr.decode('utf-8', errors='ignore')[:500]}")

                await asyncio.sleep(restart_delay)

                if self.running:
                    await self._start_ffmpeg()
                    restart_delay = min(restart_delay * 2, 60)
            else:
                restart_delay = 5
