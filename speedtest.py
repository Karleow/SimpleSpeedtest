import os
import time
from flask import Flask, Response, request, render_template_string
from multiprocessing import Pool, cpu_count

# --- 1. Server-side Data Preparation ---
PREPARE_BYTES_SERVER = 128 * 1024 * 1024
PREPARED_DOWNLOAD_DATA = None

def generate_random_chunk(size):
    """Generates a chunk of random data (used by multiprocessing workers)."""
    return os.urandom(size)

def prepare_server_data():
    """
    Pre-generates 128MB of random data in parallel at server startup for download tests.
    """
    global PREPARED_DOWNLOAD_DATA
    print(f"Server: Preparing {PREPARE_BYTES_SERVER / (1024*1024):.0f}MB of random data for downloads...")
    start_time = time.time()
    
    # Use all available CPU cores for parallel generation
    num_workers = cpu_count()
    chunk_size = PREPARE_BYTES_SERVER // num_workers
    sizes = [chunk_size] * num_workers
    sizes[-1] += PREPARE_BYTES_SERVER % num_workers

    with Pool(processes=num_workers) as pool:
        chunks = pool.map(generate_random_chunk, sizes)

    PREPARED_DOWNLOAD_DATA = b"".join(chunks)
    end_time = time.time()
    print(f"Server: Data preparation complete. Took {end_time - start_time:.2f} seconds.")
    print(f"Server: Prepared data size: {len(PREPARED_DOWNLOAD_DATA) / (1024*1024):.0f}MB")

# Initialize the Flask application
app = Flask(__name__)

# --- 2. HTML & JavaScript Frontend ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Browser Speed Test</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 600px; margin: auto; background-color: #f4f4f9; color: #333; }
        h1, h2 { color: #000; }
        .test-row { display: flex; gap: 10px; margin-bottom: 10px; align-items: center; }
        .test-row-label { font-weight: bold; min-width: 80px; }
        .test-btn { background-color: #007bff; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; transition: background-color 0.2s; flex-grow: 1; }
        .test-btn:hover { background-color: #0056b3; }
        .test-btn:disabled { background-color: #cccccc; cursor: not-allowed; }
        .upload-btn { background-color: #28a745; }
        .upload-btn:hover { background-color: #218838; }
        #results { margin-top: 20px; background-color: #fff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        #status { font-weight: bold; color: #555; height: 1.5em; }
        #progress-container { margin-top: 15px; background: #eee; padding: 10px; border-radius: 5px; }
        #progressBar { font-family: "Courier New", Courier, monospace; font-size: 1.2em; color: #007bff; white-space: pre; margin: 5px 0 0 0; }
        #instantSpeed { font-family: monospace; font-size: 1.2em; font-weight: bold; text-align: center; margin-bottom: 5px;}
        span { font-weight: bold; color: #007bff; }
    </style>
</head>
<body>
    <h1>🌐 Browser Speed Test</h1>
    <p>Select a test to begin.</p>
    
    <div id="test-controls">
        <div class="test-row">
            <div class="test-row-label">Download:</div>
            <button class="test-btn" data-type="download" data-duration="10">10s</button>
            <button class="test-btn" data-type="download" data-duration="30">30s</button>
            <button class="test-btn" data-type="download" data-duration="300">5min</button>
        </div>
        <div class="test-row">
            <div class="test-row-label">Upload:</div>
            <button class="test-btn upload-btn" data-type="upload" data-duration="10">10s</button>
            <button class="test-btn upload-btn" data-type="upload" data-duration="30">30s</button>
            <button class="test-btn upload-btn" data-type="upload" data-duration="300">5min</button>
        </div>
    </div>
    
    <div id="results">
        <div id="status">Preparing data for upload test...</div>
        <div id="progress-container">
            <div id="instantSpeed">0.00 Mbps</div>
            <pre id="progressBar">[....................]</pre>
        </div>
        <h2>Results</h2>
        <p>Download Speed: <span id="dlResult">0.00</span> Mbps</p>
        <p>Upload Speed: <span id="ulResult">0.00</span> Mbps</p>
    </div>

<script>
    const statusDiv = document.getElementById('status');
    const dlResultSpan = document.getElementById('dlResult');
    const ulResultSpan = document.getElementById('ulResult');
    const testButtons = document.querySelectorAll('.test-btn');
    const progressBar = document.getElementById('progressBar');
    const instantSpeedDiv = document.getElementById('instantSpeed');

    const UPLOAD_REQUEST_SIZE_BYTES = 256 * 1024;
    const PREPARE_TOTAL_BYTES = 128 * 1024 * 1024;
    let preparedUploadData = null;
    let uploadOffset = 0;

    const workerScriptContent = `
        function createPrng(seed) {
            let currentSeed = seed;
            const a = 1664525;
            const c = 1013904223;
            const m = 2**32;
            return function() {
                currentSeed = (a * currentSeed + c) % m;
                return currentSeed;
            }
        }

        self.onmessage = (e) => {
            const { size, offset, seed } = e.data;
            const prng = createPrng(seed);
            
            const buffer = new ArrayBuffer(size);
            const view32 = new Uint32Array(buffer);

            for (let i = 0; i < view32.length; i++) {
                view32[i] = prng();
            }

            self.postMessage({ buffer: buffer, offset: offset }, [buffer]);
        };
    `;

    async function prepareClientData() {
        console.log('Browser: Preparing ' + (PREPARE_TOTAL_BYTES / (1024 * 1024)) + 'MB of pseudo-random data for uploads.');
        const startTime = performance.now();
        setButtonsDisabled(true);

        const numWorkers = navigator.hardwareConcurrency || 4;
        const mainBuffer = new ArrayBuffer(PREPARE_TOTAL_BYTES);
        const mainBufferView = new Uint8Array(mainBuffer);
        const workerBlob = new Blob([workerScriptContent], { type: 'application/javascript' });
        const workerUrl = URL.createObjectURL(workerBlob);
        const workers = Array.from({ length: numWorkers }, () => new Worker(workerUrl));
        
        const chunkSizePerWorker = Math.ceil(PREPARE_TOTAL_BYTES / numWorkers);
        let promises = [];
        let bytesLoaded = 0;

        for (let i = 0; i < numWorkers; i++) {
            const offset = i * chunkSizePerWorker;
            const size = Math.min(chunkSizePerWorker, PREPARE_TOTAL_BYTES - offset);
            if (size <= 0) continue;
            
            const promise = new Promise((resolve) => {
                workers[i].onmessage = (e) => {
                    const { buffer, offset: workerOffset } = e.data;
                    mainBufferView.set(new Uint8Array(buffer), workerOffset);
                    bytesLoaded += buffer.byteLength;
                    updateProgressBar(bytesLoaded, PREPARE_TOTAL_BYTES);
                    workers[i].terminate();
                    resolve();
                };
            });
            
            const seed = performance.now() + i;
            workers[i].postMessage({ size, offset, seed });
            promises.push(promise);
        }

        await Promise.all(promises);
        preparedUploadData = mainBufferView;
        URL.revokeObjectURL(workerUrl);

        const endTime = performance.now();
        console.log('Browser: Data preparation complete. Took ' + ((endTime - startTime) / 1000).toFixed(2) + ' seconds.');
        statusDiv.textContent = 'Ready for testing.';
        updateProgressBar(0, 1);
        setButtonsDisabled(false);
    }
    
    testButtons.forEach(button => {
        button.addEventListener('click', () => {
            if (!preparedUploadData && button.getAttribute('data-type') === 'upload') {
                statusDiv.textContent = "Data is still being prepared, please wait.";
                return;
            }
            const durationSec = parseInt(button.getAttribute('data-duration'), 10);
            const testType = button.getAttribute('data-type');
            startTest(testType, durationSec);
        });
    });

    function setButtonsDisabled(disabled) {
        testButtons.forEach(b => b.disabled = disabled);
    }

    async function startTest(testType, durationSec) {
        setButtonsDisabled(true);
        instantSpeedDiv.textContent = '0.00 Mbps';
        updateProgressBar(0, 1);

        const result = await runTestPhase(testType, durationSec);
        
        if (result >= 0) {
            if (testType === 'download') {
                dlResultSpan.textContent = result.toFixed(2);
            } else {
                ulResultSpan.textContent = result.toFixed(2);
            }
            statusDiv.textContent = 'Test complete! Ready for next test.';
            instantSpeedDiv.textContent = 'Test Finished';
        }
        
        setButtonsDisabled(false);
    }
    
    function updateProgressBar(elapsed, total) {
        const totalWidth = 20;
        const percent = total > 0 ? Math.min(elapsed / total, 1) : 0;
        const filledWidth = Math.round(totalWidth * percent);
        const emptyWidth = totalWidth - filledWidth;
        const filledStr = '█'.repeat(filledWidth);
        const emptyStr = '░'.repeat(emptyWidth);
        progressBar.textContent = '[' + filledStr + emptyStr + '] ' + Math.round(percent * 100) + '%';
    }

    async function runTestPhase(type, durationSec) {
        const typeName = type.charAt(0).toUpperCase() + type.slice(1);
        statusDiv.textContent = 'Testing ' + typeName + ' speed...';
        const controller = new AbortController();
        const signal = controller.signal;
        const durationMs = durationSec * 1000;

        const testTimeout = setTimeout(() => controller.abort(), durationMs);

        let totalBytes = 0;
        let lastBytes = 0;
        let lastTime = performance.now();
        const startTime = lastTime;

        const progressInterval = setInterval(() => {
            const currentTime = performance.now();
            const elapsedMs = currentTime - startTime;
            
            const bytesSinceLast = totalBytes - lastBytes;
            const timeSinceLast = currentTime - lastTime;
            const speedBps = timeSinceLast > 0 ? (bytesSinceLast * 8) / (timeSinceLast / 1000) : 0;
            instantSpeedDiv.textContent = (speedBps / 1_000_000).toFixed(2) + ' Mbps';
            
            lastBytes = totalBytes;
            lastTime = currentTime;

            updateProgressBar(elapsedMs, durationMs);
        }, 500);

        try {
            if (type === 'download') {
                const response = await fetch('/download', { signal });
                const reader = response.body.getReader();
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    totalBytes += value.length;
                }
            } else { // upload
                while (!signal.aborted) {
                    const end = uploadOffset + UPLOAD_REQUEST_SIZE_BYTES;
                    const chunk = preparedUploadData.subarray(uploadOffset, end);
                    await fetch('/upload', { method: 'POST', body: chunk, signal });
                    totalBytes += chunk.length;
                    uploadOffset = (end >= preparedUploadData.length) ? 0 : end;
                }
            }
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error(typeName + ' test error:', error);
                statusDiv.textContent = typeName + ' test failed. See console for details.';
                clearTimeout(testTimeout);
                clearInterval(progressInterval);
                return -1;
            }
        } finally {
            clearTimeout(testTimeout);
            clearInterval(progressInterval);
            updateProgressBar(durationMs, durationMs);
        }
        
        const endTime = performance.now();
        const actualDurationSec = (endTime - startTime) / 1000;
        if (actualDurationSec < 0.1) return 0;

        const avgSpeedBps = (totalBytes * 8) / actualDurationSec;
        return avgSpeedBps / 1_000_000;
    }
    
    window.onload = prepareClientData;
</script>
</body>
</html>
"""

# --- 3. Flask Routes ---
@app.route('/')
def home():
    """Serves the main HTML page."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/download')
def download_stream():
    """Streams endless data from a pre-generated buffer."""
    def generate_from_preped_data():
        if not PREPARED_DOWNLOAD_DATA:
            print("Warning: Pre-prepared data is not available. Serving on-the-fly data.")
            while True: yield os.urandom(128 * 1024)
        
        buffer = PREPARED_DOWNLOAD_DATA
        buffer_len = len(buffer)
        chunk_size = 128 * 1024
        offset = 0
        while True:
            end = offset + chunk_size
            if end <= buffer_len:
                yield buffer[offset:end]
                offset = end
            else:
                part1 = buffer[offset:]
                part2_len = chunk_size - len(part1)
                part2 = buffer[:part2_len]
                yield part1 + part2
                offset = part2_len
            if offset >= buffer_len:
                offset = 0
    return Response(generate_from_preped_data(), mimetype='application/octet-stream')

@app.route('/upload', methods=['POST'])
def upload_stream():
    """Receives and discards data from the client."""
    _ = request.get_data(as_text=False)
    return "OK", 200

# --- 4. Main Execution ---
if __name__ == '__main__':
    # Prepare server-side data before starting the web server
    prepare_server_data()
    
    print("\n🚀 Server starting...")
    print("Access the speed test at http://127.0.0.1:8080 or http://<your-ip>:8080")
    # Use Flask's built-in server for simple deployment without extra dependencies.
    # Note: Flask's dev server is not recommended for production.
    app.run(host='0.0.0.0', port=8080)
