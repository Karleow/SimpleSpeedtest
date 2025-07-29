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
