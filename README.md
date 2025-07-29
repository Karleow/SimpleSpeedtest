# Browser-Based Network Speed Test

A simple, iperf-like network throughput tester that runs from a single Python script and uses any web browser as the client.

## What is this for?

This tool measures the network throughput (speed) between two devices on the same network. One device runs a lightweight Python server, and the other device (the client) only needs a web browser to run the test.

It is designed to be a quick and easy replacement for command-line tools like `iperf`, especially in situations where installing software is inconvenient or impossible.

## Why Use This Over `iperf`?

`iperf` is a powerful tool, but its command-line nature and installation requirements can be a major hurdle. This browser-based tester shines in environments where simplicity and accessibility are key.

#### The Convenience of the Web Browser

The web browser is the most universal application available today. This tool leverages it as the "client," meaning you don't need to install any special apps on the device you're testing from.

#### No More Installation Headaches

This tool is perfect for testing network speeds in tricky situations:
* **Mobile Devices:** Easily test the Wi-Fi speed of your iPhone, iPad, or Android device without searching for a specific network testing app.
* **Restricted Environments:** Run a speed test from a corporate laptop or a library computer where you don't have administrator rights to install software.
* **Embedded Systems & IoT:** Test the network connection of a Raspberry Pi, a smart TV, or any other device that has a web browser but a complex or non-existent app ecosystem.
* **Non-Technical Users:** It's much easier to ask someone to "open a web address" than to guide them through installing and running a command-line tool.

In short, if a device has a web browser, you can test its network speed with this tool.

## Features

* **Clientless Installation:** The only client you need is a web browser.
* **Single-File Server:** The entire application is contained in a single Python script.
* **Cross-Platform:** Works between any two devices that can run Python 3 and a modern web browser (e.g., Windows, macOS, Linux, iOS, Android).
* **Upload & Download Testing:** Measures throughput in both directions.
* **Minimal Performance Overhead:** Uses a high-speed pseudo-random generator on the client-side to ensure the test is measuring network speed, not the device's processing power.
* **Simple Dependencies:** Only requires Python and the Flask library.

## How It Works

1.  **Server:** A Python server using the Flask framework is started on `Machine A`. At startup, it pre-generates 128 MB of random data in memory to ensure download tests are not bottlenecked by on-the-fly data generation.
2.  **Client:** A user on `Machine B` navigates to the server's IP address in a web browser.
3.  **Download Test:** The browser requests data from the `/download` endpoint. The server continuously streams its pre-generated 128 MB data block to the browser. The browser calculates the speed based on how much data is received over time.
4.  **Upload Test:** The browser generates its own pseudo-random data (very quickly, without using slow cryptographic functions) and sends it to the server's `/upload` endpoint in 256KB chunks. The server immediately receives and discards the data. The browser calculates the speed based on how fast it can send the data.

## Requirements

* Python 3
* Flask

## How to Use

Follow these steps to test the network speed between a server machine (where you run the script) and a client machine (where you use the browser).

#### 1. Install Flask

On the server machine, open your terminal or command prompt and install Flask:
```bash
pip install Flask
```

#### 2. Save the Script

Save the Python code as a file named `speedtest.py` on the server machine.

#### 3. Find the Server's IP Address

You will need the local IP address of the server machine so the client can connect to it.

* **On Windows:** Open Command Prompt and type `ipconfig`. Look for the "IPv4 Address".
* **On macOS or Linux:** Open a terminal and type `ip addr` or `ifconfig`. Look for the "inet" address.

It will typically look like `192.168.1.15` or `10.0.0.32`.

#### 4. Run the Server

In the same directory where you saved `speedtest.py`, run the script:
```bash
python speedtest.py
```
You will see output indicating that the server is preparing data and is now running.

```
Server: Preparing 128MB of random data for downloads...
Server: Data preparation complete. Took 1.23 seconds.
Server: Prepared data size: 128MB

🚀 Server starting...
Access the speed test at [http://127.0.0.1:8080](http://127.0.0.1:8080) or http://<your-ip>:8080
* Serving Flask app 'speedtest'
* Running on [http://0.0.0.0:8080](http://0.0.0.0:8080)
```

#### 5. Run the Test on the Client

1.  On your client device (e.g., your phone, laptop, etc.), open a web browser.
2.  In the address bar, type `http://<server_ip>:8080`, replacing `<server_ip>` with the IP address you found in step 3.
    * Example: `http://192.168.1.15:8080`
## Troubleshooting

### Connection Issues

If you are unable to connect to the server from your client device (e.g., the web page times out or shows a "This site can’t be reached" error), the most common cause is a firewall on the server machine.

The server listens on TCP port **8080**. Most operating systems have a built-in firewall that will block incoming connections on this port by default for security reasons.

#### Solutions:

1.  **Create a Firewall Rule (Recommended):** The best solution is to add a new "inbound rule" to your server's firewall settings to specifically allow incoming TCP traffic on port 8080. This is the most secure method.

2.  **Temporarily Disable the Firewall (Easy, but use with caution):** For a quick test, you can temporarily disable the firewall on the server machine. **IMPORTANT:** Remember to re-enable your firewall immediately after you have finished testing to keep your system secure.

A good way to confirm the problem is firewall-related: If you can successfully load the page using `http://127.0.0.1:8080` on the server machine itself, but not from another device using its IP address (`http://<server_ip>:8080`), the firewall is almost always the culprit.
3.  The speed test page will load. Click the **Download** or **Upload** buttons to begin testing. The results will be displayed on the page.
