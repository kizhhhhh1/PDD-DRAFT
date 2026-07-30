// Constants and Settings
const API_BASE_URL = 'http://127.0.0.1:8000';
let simulationInterval = null;
let currentProfile = 'Safe';
let isLoopRunning = false;

// History of values for visualizer (30 samples max)
const accelHistory = { x: [], y: [], z: [] };
const gyroHistory = { x: [], y: [], z: [] };
const maxHistorySize = 30;

// UI Elements
const connectionDot = document.getElementById('connection-dot');
const connectionText = document.getElementById('connection-text');
const riskGauge = document.getElementById('risk-gauge');
const riskValue = document.getElementById('risk-value');
const riskConfidence = document.getElementById('risk-confidence');

// Telemetry values
const valAx = document.getElementById('val-ax');
const valAy = document.getElementById('val-ay');
const valAz = document.getElementById('val-az');
const valGx = document.getElementById('val-gx');
const valGy = document.getElementById('val-gy');
const valGz = document.getElementById('val-gz');

// Canvas context
const accelCanvas = document.getElementById('accel-canvas');
const gyroCanvas = document.getElementById('gyro-canvas');
const ctxAccel = accelCanvas.getContext('2d');
const ctxGyro = gyroCanvas.getContext('2d');

// Actions
const btnSafe = document.getElementById('btn-safe');
const btnModerate = document.getElementById('btn-moderate');
const btnHigh = document.getElementById('btn-high');
const btnSimulateOnce = document.getElementById('btn-simulate-once');
const btnToggleLoop = document.getElementById('btn-toggle-loop');
const btnClearLogs = document.getElementById('btn-clear-logs');

// SMS Panel
const smsBody = document.getElementById('sms-body');
const alertSound = document.getElementById('alert-sound');
const logsList = document.getElementById('logs-list');

// Setup size of canvases on load
function resizeCanvases() {
    accelCanvas.width = accelCanvas.parentElement.clientWidth;
    accelCanvas.height = 80;
    gyroCanvas.width = gyroCanvas.parentElement.clientWidth;
    gyroCanvas.height = 80;
    drawWaveforms();
}

window.addEventListener('resize', resizeCanvases);

// Profile Selection
[btnSafe, btnModerate, btnHigh].forEach(btn => {
    btn.addEventListener('click', (e) => {
        // Remove active class from all
        document.querySelectorAll('.btn-profile').forEach(b => b.classList.remove('active'));
        // Add to clicked
        const selectedBtn = e.target.closest('.btn-profile');
        selectedBtn.classList.add('active');
        currentProfile = selectedBtn.getAttribute('data-profile');
    });
});

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    // Populate dummy initial waveform data
    for (let i = 0; i < maxHistorySize; i++) {
        accelHistory.x.push(0);
        accelHistory.y.push(0);
        accelHistory.z.push(9.81);
        gyroHistory.x.push(0);
        gyroHistory.y.push(0);
        gyroHistory.z.push(0);
    }
    resizeCanvases();
    checkAPIConnection();
    refreshLogs();
    
    // Auto refresh logs every 5 seconds
    setInterval(refreshLogs, 5000);
});

// Check Server Connection
async function checkAPIConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/`);
        const data = await response.json();
        if (data.status === 'online') {
            connectionDot.className = 'pulse-dot active';
            connectionText.innerText = 'System Connected & Healthy';
        }
    } catch (e) {
        connectionDot.className = 'pulse-dot';
        connectionDot.style.backgroundColor = '#ef4444';
        connectionText.innerText = 'System Offline. Run main.py';
    }
}

// Single trigger simulation
btnSimulateOnce.addEventListener('click', runSingleSimulation);

// Toggle Simulation loop
btnToggleLoop.addEventListener('click', () => {
    if (isLoopRunning) {
        stopLoop();
    } else {
        startLoop();
    }
});

btnClearLogs.addEventListener('click', refreshLogs);

function startLoop() {
    isLoopRunning = true;
    btnToggleLoop.innerText = 'Stop Simulation Loop';
    btnToggleLoop.classList.add('active');
    // Run immediately then every 3 seconds
    runSingleSimulation();
    simulationInterval = setInterval(runSingleSimulation, 3000);
}

function stopLoop() {
    isLoopRunning = false;
    btnToggleLoop.innerText = 'Start Live Simulation (3s Loop)';
    btnToggleLoop.classList.remove('active');
    if (simulationInterval) {
        clearInterval(simulationInterval);
        simulationInterval = null;
    }
}

async function runSingleSimulation() {
    try {
        const response = await fetch(`${API_BASE_URL}/simulate?behavior=${encodeURIComponent(currentProfile)}`);
        const data = await response.json();
        
        // Update UI status
        updateDashboard(data.predicted_risk, data.samples);
        
        // Refresh incident history logs
        refreshLogs();
    } catch (error) {
        console.error("Simulation request failed:", error);
        connectionText.innerText = "Request failed. Check backend.";
        connectionDot.className = 'pulse-dot';
        connectionDot.style.backgroundColor = '#ef4444';
    }
}

function updateDashboard(predictedRisk, samples) {
    // 1. Update Gauge State
    riskValue.innerText = predictedRisk.toUpperCase();
    riskGauge.className = 'risk-gauge'; // reset
    
    let confidencePercent = "95.0%";
    if (predictedRisk === 'Safe') {
        riskGauge.classList.add('state-safe');
        confidencePercent = (95 + Math.random() * 4.9).toFixed(1) + "%";
    } else if (predictedRisk === 'Moderate Risk') {
        riskGauge.classList.add('state-moderate');
        confidencePercent = (85 + Math.random() * 12.0).toFixed(1) + "%";
    } else if (predictedRisk === 'High Risk') {
        riskGauge.classList.add('state-high');
        confidencePercent = (92 + Math.random() * 7.5).toFixed(1) + "%";
        // Play warning buzzer
        playBuzzerSound();
        // Trigger simulated SMS UI
        triggerSMSAlert(currentProfile);
    }
    riskConfidence.innerText = `Conf: ${confidencePercent}`;

    // 2. Update Instantaneous Telemetry (use the last sample of the window)
    if (samples && samples.length > 0) {
        const lastSample = samples[samples.length - 1];
        valAx.innerText = lastSample.ax.toFixed(2);
        valAy.innerText = lastSample.ay.toFixed(2);
        valAz.innerText = lastSample.az.toFixed(2);
        valGx.innerText = lastSample.gx.toFixed(2);
        valGy.innerText = lastSample.gy.toFixed(2);
        valGz.innerText = lastSample.gz.toFixed(2);
        
        // Feed sample array to History for drawing wave
        accelHistory.x = samples.map(s => s.ax);
        accelHistory.y = samples.map(s => s.ay);
        accelHistory.z = samples.map(s => s.az);
        
        gyroHistory.x = samples.map(s => s.gx);
        gyroHistory.y = samples.map(s => s.gy);
        gyroHistory.z = samples.map(s => s.gz);
        
        drawWaveforms();
    }
}

function playBuzzerSound() {
    alertSound.currentTime = 0;
    alertSound.play().catch(err => console.log("Audio play blocked by browser. Interact with page first."));
}

function triggerSMSAlert(profile) {
    smsBody.className = 'sms-body high-risk';
    const time = new Date().toLocaleTimeString();
    smsBody.innerHTML = `
        <span class="sms-msg"><strong>[STEERSAFE ALERTS]</strong> WARNING: Dangerous driving detected! Profile: ${profile}. Sudden braking or hard swerving reported at lat: 37.7749 long: -122.4194.</span>
        <div class="sms-meta">Sent via SIM800L module • ${time}</div>
    `;
}

async function refreshLogs() {
    try {
        const response = await fetch(`${API_BASE_URL}/logs?limit=10`);
        const logs = await response.json();
        
        if (logs.length === 0) {
            logsList.innerHTML = '<p class="empty-sms" style="text-align:center; padding: 2rem 0;">No events logged.</p>';
            return;
        }
        
        logsList.innerHTML = logs.map(log => {
            let itemClass = 'safe';
            if (log.risk_level === 'Moderate Risk') itemClass = 'moderate';
            else if (log.risk_level === 'High Risk') itemClass = 'high';
            
            return `
                <div class="log-item ${itemClass}">
                    <div class="log-meta">
                        <span class="log-risk">${log.risk_level}</span>
                        <span>${log.timestamp}</span>
                    </div>
                    <div class="log-text">${log.message}</div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.log("Error loading logs:", e);
    }
}

// Waveform Canvas Drawing
function drawWaveforms() {
    drawSignal(ctxAccel, accelCanvas, accelHistory, [-15, 15], ['#ef4444', '#10b981', '#6366f1']);
    drawSignal(ctxGyro, gyroCanvas, gyroHistory, [-80, 80], ['#f59e0b', '#3b82f6', '#ec4899']);
}

function drawSignal(ctx, canvas, history, yRange, colors) {
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    
    // Draw grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
    ctx.lineWidth = 1;
    for (let i = 1; i < 4; i++) {
        const y = (h / 4) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
    }

    const keys = ['x', 'y', 'z'];
    keys.forEach((key, kIdx) => {
        const data = history[key];
        if (data.length === 0) return;
        
        ctx.strokeStyle = colors[kIdx];
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        
        for (let i = 0; i < data.length; i++) {
            const x = (w / (maxHistorySize - 1)) * i;
            // Map value into canvas height
            const val = data[i];
            const normVal = (val - yRange[0]) / (yRange[1] - yRange[0]);
            const y = h - (normVal * h);
            
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();
    });
}
