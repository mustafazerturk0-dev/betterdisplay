import dxcam
import subprocess
import socket
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BTDS-Engine")

class BTDSEngine:
    def __init__(self):
        self.camera = dxcam.create(output_color="BGR")
        self.target_fps = 60
        self.is_streaming = False
        self.ffmpeg_process = None
        self.server_socket = None
        self.client_socket = None
        self.mode = "usb"
        
        # Telemetry
        self.latency_ms = 0
        self.bandwidth_mbps = 0
        self.gpu_usage = 0

    def set_fps(self, fps):
        self.target_fps = fps
        if self.is_streaming:
            self.stop_stream()
            self.start_stream()

    def set_mode(self, mode):
        if self.mode == mode:
            return
        self.mode = mode
        if mode == "usb":
            self.setup_adb_tunnel()
        else:
            self.teardown_adb_tunnel()

    def setup_adb_tunnel(self):
        try:
            subprocess.run(["adb", "reverse", "tcp:5000", "tcp:5000"], 
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("ADB tunnel established on port 5000.")
        except Exception as e:
            logger.error(f"Failed to setup ADB tunnel. Is ADB installed and device connected? {e}")

    def teardown_adb_tunnel(self):
        try:
            subprocess.run(["adb", "reverse", "--remove", "tcp:5000"], 
                           check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("ADB tunnel removed.")
        except Exception as e:
            logger.error(f"Failed to remove ADB tunnel: {e}")

    def start_server(self):
        if self.mode == "usb":
            self.setup_adb_tunnel()
            
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", 5000))
        self.server_socket.listen(1)
        logger.info("Server listening on 0.0.0.0:5000")

        def accept_clients():
            while True:
                try:
                    conn, addr = self.server_socket.accept()
                    logger.info(f"Client connected from {addr}")
                    if self.client_socket:
                        self.client_socket.close()
                    self.client_socket = conn
                    if not self.is_streaming:
                        self.start_stream()
                except Exception as e:
                    logger.error(f"Server accept error: {e}")
                    break

        threading.Thread(target=accept_clients, daemon=True).start()

    def start_stream(self):
        if self.is_streaming or not self.client_socket:
            return
        
        self.is_streaming = True
        
        width, height = self.camera.width, self.camera.height
        logger.info(f"Starting stream at {width}x{height} @ {self.target_fps}fps")
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{width}x{height}",
            "-r", str(self.target_fps),
            "-i", "-",
            "-c:v", "h264_nvenc",
            "-preset", "p1", # Fastest preset for lowest latency
            "-tune", "ull",  # Ultra low latency
            "-profile:v", "main",
            "-rc", "cbr",
            "-b:v", "15M",
            "-maxrate", "15M",
            "-bufsize", "15M",
            "-zerolatency", "1",
            "-delay", "0",
            "-f", "mpegts",
            "-"
        ]
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            logger.error(f"Failed to start ffmpeg. Is ffmpeg in PATH? {e}")
            self.is_streaming = False
            return
            
        def capture_loop():
            self.camera.start(target_fps=self.target_fps)
            try:
                while self.is_streaming:
                    frame = self.camera.get_latest_frame()
                    if frame is not None and self.ffmpeg_process and self.ffmpeg_process.stdin:
                        try:
                            self.ffmpeg_process.stdin.write(frame.tobytes())
                        except (BrokenPipeError, IOError):
                            break
            finally:
                self.camera.stop()
                if self.ffmpeg_process and self.ffmpeg_process.stdin:
                    try:
                        self.ffmpeg_process.stdin.close()
                    except:
                        pass
                    
        def stream_loop():
            try:
                while self.is_streaming and self.ffmpeg_process and self.ffmpeg_process.stdout:
                    data = self.ffmpeg_process.stdout.read(8192)
                    if not data:
                        break
                    if self.client_socket:
                        try:
                            self.client_socket.sendall(data)
                            # Update telemetry (rough estimate)
                            self.bandwidth_mbps = (len(data) * 8 * self.target_fps) / 1_000_000 
                        except (BrokenPipeError, ConnectionResetError):
                            logger.info("Client disconnected.")
                            break
            except Exception as e:
                logger.error(f"Streaming error: {e}")
            finally:
                self.stop_stream()
                
        threading.Thread(target=capture_loop, daemon=True).start()
        threading.Thread(target=stream_loop, daemon=True).start()
        
    def stop_stream(self):
        self.is_streaming = False
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.terminate()
            except:
                pass
            self.ffmpeg_process = None
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
            
    def shutdown(self):
        self.stop_stream()
        if self.server_socket:
            self.server_socket.close()
        self.teardown_adb_tunnel()
