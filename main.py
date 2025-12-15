import network
import socket
import machine
import neopixel

# WS2812B setup
MATRIX_PIN = 5  # GPIO pin connected to DIN of the matrix
NUM_LEDS = 64   # 8x8 matrix
BRIGHTNESS = 0.05  # 5% brightness
np = neopixel.NeoPixel(machine.Pin(MATRIX_PIN), NUM_LEDS)


STATUS_COLORS = {
    "Available": (0, 255, 0),   # Green
    "Busy": (255, 0, 0),        # Red
    "Away": (255, 255, 0),      # Yellow
}

# Connect to Wi-Fi
ssid = ''
password = ''
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
while not wlan.isconnected():
    pass
print('Connected, IP:', wlan.ifconfig()[0])


def set_led(status):
    if status == "Busy":
        # Red background with white horizontal line in the middle
        red = tuple(int(c * BRIGHTNESS) for c in (255, 0, 0))
        white = tuple(int(c * BRIGHTNESS) for c in (255, 255, 255))
        for y in range(8):
            for x in range(8):
                idx = y * 8 + x
                # Draw white line at rows 3 and 4 (center two rows)
                if y == 3 or y == 4:
                    np[idx] = white
                else:
                    np[idx] = red
        np.write()
        return
    base_color = STATUS_COLORS.get(status, (0, 0, 0))  # Default off
    color = tuple(int(c * BRIGHTNESS) for c in base_color)
    for i in range(NUM_LEDS):
        np[i] = color
    np.write()

# Simple HTTP server
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print('Listening on', addr)

while True:
    cl, addr = s.accept()
    request = cl.recv(1024)
    request = str(request)
    # Parse status from request (e.g., /?status=Available)
    if '/?status=' in request:
        status = request.split('/?status=')[1].split(' ')[0]
        status = status.split('&')[0]
        status = status.split('\\r')[0]
        set_led(status)
        print(f'Setting {status} status')
    cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\nOK')
    cl.close()