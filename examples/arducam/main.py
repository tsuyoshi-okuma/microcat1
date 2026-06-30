from utime import sleep_ms
import utime
from machine import Pin, SPI
from camera import Camera
import microcat1
import uos
import urequests
import ntptime
import gc

# SPI Configuration
SPI_ID = 0
SPI_SCK_PIN = 18
SPI_MISO_PIN = 16
SPI_MOSI_PIN = 19
SPI_BAUDRATE = 8000000
SPI_CS_PIN = 17  # Chip select pin

# Pin Assignments
LED_PIN_NUM = 25  # Built-in LED pin

# JPEG Markers
JPEG_SOI = b"\xff\xd8"  # Start of Image marker
JPEG_EOI = b"\xff\xd9"  # End of Image marker

# Read Settings
# Safety margin added to the reported FIFO length to ensure full capture
READ_MARGIN = 40000

# Interval between captures (seconds)
INTERVAL_SEC = 15

# SORACOM Configuration
APN = "soracom.io"
USER = "sora"
PASSWORD = "sora"
HARVEST_FILES_URL = "http://harvest-files.soracom.io/photos"
TEMP_FILENAME = "temp.jpg"
JST_OFFSET = 9 * 3600

# Initialization
sleep_ms(1000)
spi = SPI(
    SPI_ID,
    sck=Pin(SPI_SCK_PIN),
    miso=Pin(SPI_MISO_PIN),
    mosi=Pin(SPI_MOSI_PIN),
    baudrate=SPI_BAUDRATE,
)
cs = Pin(SPI_CS_PIN, Pin.OUT)
led = Pin(LED_PIN_NUM, Pin.OUT)
cam = Camera(spi, cs)
modem = microcat1.modem()


def capture_and_get_data(cam):
    """Performs high-speed burst read and extracts clean JPEG data."""
    print("\n[Camera] Starting capture...")

    # Start stabilization delay
    led.on()
    print("Stabilizing White Balance (AWB)...")
    sleep_ms(3000)
    led.off()

    # Flush the buffer with Dummy Captures
    # Sometimes one is not enough to clear the old "green" frames
    for i in range(2):
        print(f"Dummy capture {(i + 1)}/2 to clear sensor cache...")
        cam.capture_jpg()
        sleep_ms(500)
        # We don't need to read the data, just move to the next capture

    # Visual cue for actual capture
    for _ in range(2):
        led.on()
        sleep_ms(200)
        led.off()
        sleep_ms(200)

    # Final Capture
    print("Capturing final image...")
    led.on()
    cam.capture_jpg()
    # Wait for FIFO to stabilize
    sleep_ms(100)
    led.off()

    # Allocate a buffer slightly larger than the actual data volume
    read_size = cam.received_length + READ_MARGIN
    raw_buffer = bytearray(read_size)

    # Initiating SPI communication and starting burst read operations
    cam.cs.off()
    cam.spi_bus.write(bytes([cam.BURST_FIFO_READ]))

    # Read all data
    cam.spi_bus.readinto(raw_buffer)

    # Terminate SPI communication
    cam.cs.on()

    start_idx = raw_buffer.find(JPEG_SOI)  # Search for the JPEG start marker
    end_idx = raw_buffer.find(JPEG_EOI)  # Search for the JPEG end marker

    if start_idx != -1 and end_idx != -1:
        # Slice includeing the 2-byte EOI (FF D9)
        return raw_buffer[start_idx : end_idx + 2]
    return None


def make_timestamp_filename():
    # NTPはUTC取得のため、JSTに変換する
    t = utime.localtime(utime.time() + JST_OFFSET)
    return "pic_{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}.jpg".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )


def upload_photo(file_path, remote_filename):
    try:
        url = HARVEST_FILES_URL + "/" + remote_filename
        headers = {"Content-Type": "image/jpeg"}

        print("Uploading to SORACOM Harvest Files...")
        with open(file_path, "rb") as f:
            image_binary = f.read()
        response = urequests.put(url, data=image_binary, headers=headers)
        response.close()

    except Exception as e:
        print("System Error: ", e)

    finally:
        gc.collect()


# Main Execution Loop
def main():

    if cam.camera_idx == "NOT DETECTED":
        print("Camera not found.")
        return

    while True:
        try:
            # 1. Capture and Process
            image_data = capture_and_get_data(cam)

            if image_data:
                # 2. Save to Local Storage
                with open(TEMP_FILENAME, "wb") as f:
                    f.write(image_data)
                print(f"Saved: {TEMP_FILENAME} ({len(image_data)}bytes)")

                # 3. Connect to LTE and upload
                print("Connecting to LTE...")
                modem.active(True)

                modem.connect(
                    apn=APN,
                    user=USER,
                    key=PASSWORD,
                    security=microcat1.SEC_CHAP,
                )

                sleep_ms(3000)

                if modem.isconnected() and modem.ifconfig()[0] != '0.0.0.0':
                    ntptime.settime()
                    remote_filename = make_timestamp_filename()
                    upload_photo(TEMP_FILENAME, remote_filename)
                else:
                    print("Failed to connect to LTE.")

        except Exception as e:
            print(f"Error in main loop: {e}")

        finally:
            # Delete all jpg files from MicroCat.1
            for f in uos.listdir():
                if f.endswith(".jpg"):
                    uos.remove(f)
                    print(f"Deleted {f}")
            # Always close the connection in the order: disconnect() -> active(False)!
            print("Restarting modem for next cycle...")
            modem.disconnect()
            modem.active(False)

        print(f"Waiting for next cycle ({INTERVAL_SEC}s)...")
        sleep_ms(INTERVAL_SEC * 1000)


if __name__ == "__main__":
    main()
