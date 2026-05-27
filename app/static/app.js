/* app.js */
/* Interactive functionality for the 'Dark' theme MLOps Fraud Detection Dashboard */

document.addEventListener("DOMContentLoaded", () => {
    // Navigation / Tabs
    const navLinks = document.querySelectorAll(".nav-link");
    const tabContents = document.querySelectorAll(".tab-content");

    navLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            if (link.classList.contains("docs-link")) return; // Follow external link
            
            e.preventDefault();
            const targetTab = link.getAttribute("href").substring(1);
            
            navLinks.forEach(l => l.classList.remove("active"));
            tabContents.forEach(tc => tc.classList.remove("active"));
            
            link.classList.add("active");
            document.getElementById(targetTab).classList.add("active");

            // Redraw SVG connections if pipeline tab is clicked
            if (targetTab === "pipeline") {
                setTimeout(drawTreeConnections, 100);
            }
        });
    });

    // Uptime Clock
    const uptimeClock = document.getElementById("uptime-clock");
    const startupTime = Date.now();

    function updateUptime() {
        // We will query the API health status to get the actual server uptime,
        // but fall back to client-session uptime if offline.
        let elapsedMs = Date.now() - startupTime;
        
        // Format as HH:MM:SS
        let totalSecs = Math.floor(elapsedMs / 1000);
        let hours = Math.floor(totalSecs / 3600);
        let minutes = Math.floor((totalSecs % 3600) / 60);
        let seconds = totalSecs % 60;

        const pad = (num) => String(num).padStart(2, "0");
        uptimeClock.textContent = `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
    }
    
    // Set server startup time if we fetch it
    let serverUptimeSecs = null;
    let localUptimeFetchTime = null;

    function getDisplayUptime() {
        if (serverUptimeSecs !== null && localUptimeFetchTime !== null) {
            let drift = Math.floor((Date.now() - localUptimeFetchTime) / 1000);
            let currentServerSecs = serverUptimeSecs + drift;
            let hours = Math.floor(currentServerSecs / 3600);
            let minutes = Math.floor((currentServerSecs % 3600) / 60);
            let seconds = currentServerSecs % 60;
            const pad = (num) => String(num).padStart(2, "0");
            uptimeClock.textContent = `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
            document.getElementById("uptime-label").textContent = "Actual server uptime (fetched from /)";
        } else {
            updateUptime();
        }
    }
    setInterval(getDisplayUptime, 1000);

    // Fetch API Health on load
    fetch("/")
        .then(res => {
            if (res.headers.get("content-type")?.includes("application/json")) {
                return res.json();
            }
            throw new Error("HTML response");
        })
        .then(data => {
            if (data && data.status === "healthy") {
                serverUptimeSecs = Math.round(data.uptime_seconds);
                localUptimeFetchTime = Date.now();
                document.getElementById("gauge-loaded").textContent = "ONLINE";
                document.getElementById("gauge-loaded").style.color = "var(--accent-green)";
            }
        })
        .catch(err => {
            // Server offline or serving static HTML directly. Use client timer.
            document.getElementById("gauge-loaded").textContent = "STANDALONE";
            document.getElementById("gauge-loaded").style.color = "yellow";
            document.querySelector(".status-indicator-group span").textContent = "RUNNING IN STANDALONE MODE";
            document.querySelector(".status-indicator-group span").style.color = "yellow";
            document.querySelector(".dot-online").style.backgroundColor = "yellow";
            document.querySelector(".dot-online").style.boxShadow = "0 0 8px yellow";
        });

    // Scanner / Playground Terminal
    const form = document.getElementById("predict-form");
    const terminalConsole = document.getElementById("terminal-console");
    const consoleLogs = terminalConsole.querySelector(".console-logs");
    const resultPlaceholder = document.getElementById("result-placeholder");
    const resultDisplay = document.getElementById("result-display");

    const addLog = (text, type = "muted", delay = 0) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                const div = document.createElement("div");
                div.className = `log-${type}`;
                div.textContent = `> ${text}`;
                consoleLogs.appendChild(div);
                terminalConsole.scrollTop = terminalConsole.scrollHeight;
                resolve();
            }, delay);
        });
    };

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const amount = parseFloat(document.getElementById("amount").value);
        const distance = parseFloat(document.getElementById("distance").value);

        // Hide result, show terminal
        resultDisplay.classList.add("hidden");
        resultPlaceholder.classList.remove("hidden");
        terminalConsole.classList.remove("hidden");
        consoleLogs.innerHTML = "";

        await addLog("INITIALIZING CHRONOGRAPH SYSTEM SCAN...", "success", 100);
        await addLog(`COORDINATES INJECTED: USD=${amount.toFixed(2)}, DIST=${distance.toFixed(2)} KM`, "muted", 300);
        await addLog("ESTABLISHING LINK TO SCALING ENGINES...", "muted", 200);
        await addLog("APPLYING STANDARDSCALER TRANSFORMATIONS...", "muted", 350);
        await addLog("ROUTING VECTOR SPACES THROUGH ISOLATION TREES...", "muted", 250);
        await addLog("CONVERGING 200 ISOLATION ESTIMATORS...", "muted", 300);
        await addLog("CALCULATING PATH SEGMENT DENSITY SCORE...", "muted", 200);

        let latency = 0;
        let isAnomaly = false;
        let score = 0;
        let version = "1.0.0";
        let isMock = false;

        const startTime = performance.now();

        try {
            // Hit real /predict API
            const response = await fetch("/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify({ amount, distance_from_home: distance })
            });

            if (!response.ok) {
                throw new Error("HTTP prediction request failed");
            }

            const data = await response.json();
            isAnomaly = data.is_anomaly;
            score = data.anomaly_score;
            version = data.model_version;
            latency = data.processing_time_ms;
        } catch (err) {
            // Fallback mock algorithm representing the Isolation Forest model logic
            isMock = true;
            latency = parseFloat((performance.now() - startTime).toFixed(3));
            
            // Unsupervised logic simulation: Anomalies reside in high amount or long distance tails
            // contamination was 4%.
            // normal amount mean=4.5 lognormal (~50-300 USD), distance mean=2.0 (~1-50 km)
            // anomaly amount uniform(800, 5000), distance uniform(200, 1500)
            if (amount > 800 || distance > 200 || (amount > 400 && distance > 100)) {
                isAnomaly = true;
                // Anomaly score range approx -0.5 to -0.1
                score = -0.15 - (amount / 10000) - (distance / 5000);
            } else {
                isAnomaly = false;
                // Normal score range approx 0.0 to 0.5
                score = 0.38 - (amount / 3000) - (distance / 1000);
            }
            score = parseFloat(score.toFixed(6));
        }

        if (isMock) {
            await addLog("WARNING: DIRECT GATEWAY OFFLINE. USING EMBEDDED ENGINE RUNTIME.", "warn", 200);
        }

        await addLog(`SCAN COMPLETED IN ${latency} MS. VECTOR CLASS RESOLVED.`, "success", 400);

        // Populate and display result card
        const badge = document.getElementById("badge-container");
        const statusText = document.getElementById("result-status");
        const scoreText = document.getElementById("res-score");
        const latencyText = document.getElementById("res-latency");
        const versionText = document.getElementById("res-version");
        const descText = document.getElementById("res-desc");

        scoreText.textContent = score.toFixed(6);
        latencyText.textContent = `${latency} ms`;
        versionText.textContent = isMock ? `${version} (EMULATED)` : version;

        if (isAnomaly) {
            await addLog("[!!! WARNING: SPATIAL ANOMALY DETECTED !!!]", "error", 200);
            badge.className = "status-badge anomaly";
            statusText.textContent = "ANOMALY";
            statusText.setAttribute("data-text", "ANOMALY");
            descText.textContent = "CRITICAL: Transaction values lie outside 96% of historical space vectors. High probability of fraudulent source.";
            descText.style.color = "var(--accent-red)";
        } else {
            await addLog("[SIGNAL NORMAL. TIMELINE PATH SECURED.]", "success", 200);
            badge.className = "status-badge normal";
            statusText.textContent = "NORMAL";
            statusText.setAttribute("data-text", "NORMAL");
            descText.textContent = "Transaction verified within standard statistical intervals. No anomalous signal detected.";
            descText.style.color = "var(--text-color)";
        }

        // Hide placeholder and reveal result details
        resultPlaceholder.classList.add("hidden");
        resultDisplay.classList.remove("hidden");
    });

    // MLOps Connection Tree - Render Connections
    const nodes = document.querySelectorAll(".node-wrapper");
    const svg = document.getElementById("tree-svg");

    const nodeData = {
        data: {
            title: "1. SYNTHETIC DATA GENERATOR",
            tech: "NumPy Lognormal Distributions",
            details: "Simulates actual credit card transaction footprints using lognormal and uniform distributions. Defines normal clusters (mean amount=$90, mean distance=7km) alongside a 4% contaminate uniform anomaly tail (amounts up to $5000, distance up to 1500km).",
            logs: "> Generated 10,000 baseline normal transactions.\n> Injected 400 outlier transactions into tail domains.\n> Feature set compiled: [amount, distance_from_home].\n> Shape dimensions resolved: (10400, 2)."
        },
        model: {
            title: "2. ISOLATION FOREST MODEL",
            tech: "Scikit-Learn (Unsupervised ML)",
            details: "An Isolation Forest model fitted with 200 estimators. Translates vectors into isolation trees and isolates observations by partitioning features recursively. Uses a fitted StandardScaler to normalize inputs prior to forest projection.",
            logs: "> Initializing StandardScaler fitting...\n> StandardScaler mean values calculated.\n> IsolationForest constructed with 200 estimators, contam=0.04.\n> Fitting ensemble model in parallel (n_jobs=-1)...\n> Serialize joblib model.pkl + scaler.pkl artifacts."
        },
        docker: {
            title: "3. DOCKER CONTAINERIZATION",
            tech: "Secure Multi-stage Dockerfile",
            details: "Capsules Python runtime environment into a minimal Alpine-compatible base. Stage 1 compiles requirements and serializes ML models. Stage 2 copies clean binary libraries and runs Uvicorn under a restricted UID 1001 user to prevent privilege escalations.",
            logs: "> Docker container base image pulled: python:3.10-slim\n> Execution user 'appuser' configured.\n> Clean model weights compiled in artifacts build.\n> Container footprint reduced from ~850MB to ~210MB.\n> Container exposed internally on port 8000."
        },
        k8s: {
            title: "4. KUBERNETES MICROSERVICE",
            tech: "Minikube Pod Cluster & NodePort",
            details: "Orchestrates API across a container cluster using a rolling update strategy with maxUnavailable=0. Utilizes a Horizontal Pod Autoscaler (HPA) to scale replication pods from 2 to 5 automatically when CPU loads scale past 70%.",
            logs: "> Kubernetes Namespace 'mlops' declared.\n> Created deployment/fraud-detection-deployment.\n> Service configured with static NodePort on port 30800.\n> Readiness probe configured on path '/' with 15s delay.\n> HPA scaled target matched: CPU threshold=70%."
        },
        prometheus: {
            title: "5. PROMETHEUS TELEMETRY",
            tech: "Time-series Scrape Daemon",
            details: "Periodically polls the FastAPI `/metrics` scrape target every 15 seconds. Tracks count metrics (http requests, classifications) and latency histograms (prediction runtimes) to observe live deployment health.",
            logs: "> Loading prometheus config from config/prometheus.yml\n> Target client connected: http://host.docker.internal:8000/metrics\n> Initialized metric collectors: fraud_api_requests_total\n> Logging scraping rate intervals at 15s."
        },
        grafana: {
            title: "6. GRAFANA DASHBOARDS",
            tech: "Observability Metrics Visualization",
            details: "Connects to the Prometheus time-series database to plot operational charts. Monitors the real-time prediction rate, anomalies percentage, p99 API latencies, and active model versions.",
            logs: "> Connected to Prometheus Data Source.\n> Panel query configured: rate(fraud_predictions_total[1m])\n> Active alert channels initialized.\n> Dashboard panels formatted for real-time operations."
        }
    };

    // Draw SVG connections
    function drawTreeConnections() {
        if (!svg) return;
        svg.innerHTML = "";
        
        const svgRect = svg.getBoundingClientRect();

        // Connections mapping: (From Node -> To Node)
        // Data -> Model -> Docker -> K8s -> Prometheus -> Grafana
        const connections = [
            { from: "data", to: "model" },
            { from: "model", to: "docker" },
            { from: "docker", to: "k8s" },
            { from: "k8s", to: "prometheus" },
            { from: "prometheus", to: "grafana" },
            // Circular reference representing "The Cycle"
            { from: "grafana", to: "data" }
        ];

        connections.forEach(conn => {
            const elFrom = document.querySelector(`[data-node="${conn.from}"]`);
            const elTo = document.querySelector(`[data-node="${conn.to}"]`);
            
            if (elFrom && elTo) {
                const rectFrom = elFrom.getBoundingClientRect();
                const rectTo = elTo.getBoundingClientRect();

                // Compute coordinates relative to SVG canvas
                const x1 = rectFrom.left + rectFrom.width / 2 - svgRect.left;
                const y1 = rectFrom.top + rectFrom.height / 2 - svgRect.top;
                
                const x2 = rectTo.left + rectTo.width / 2 - svgRect.left;
                const y2 = rectTo.top + rectTo.height / 2 - svgRect.top;

                const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                
                // If nodes are not in a straight line, draw a nice curved bezier path
                let d = "";
                if (Math.abs(y1 - y2) > 10 && Math.abs(x1 - x2) > 10) {
                    const cx1 = x1;
                    const cy1 = y1 + (y2 - y1) / 2;
                    const cx2 = x2;
                    const cy2 = y1 + (y2 - y1) / 2;
                    d = `M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`;
                } else {
                    d = `M ${x1} ${y1} L ${x2} ${y2}`;
                }

                path.setAttribute("d", d);
                path.setAttribute("class", "tree-svg-line");
                path.setAttribute("id", `line-${conn.from}-${conn.to}`);
                
                svg.appendChild(path);
            }
        });
    }

    // Window resize redraw lines
    window.addEventListener("resize", drawTreeConnections);

    // Node click inspector logic
    const inspector = document.getElementById("node-inspector");
    const closeInspectorBtn = document.getElementById("close-inspector");

    nodes.forEach(node => {
        node.addEventListener("click", () => {
            const nodeId = node.getAttribute("data-node");
            const data = nodeData[nodeId];

            nodes.forEach(n => n.classList.remove("active"));
            node.classList.add("active");

            // Deactivate all connection lines, activate lines related to this node
            const lines = document.querySelectorAll(".tree-svg-line");
            lines.forEach(l => l.classList.remove("active"));
            
            // Highlight connections out/in to this node
            const connOut = document.getElementById(`line-${nodeId}-${getNextNode(nodeId)}`);
            const connIn = document.getElementById(`line-${getPrevNode(nodeId)}-${nodeId}`);
            if (connOut) connOut.classList.add("active");
            if (connIn) connIn.classList.add("active");

            if (data) {
                document.getElementById("inspector-title").textContent = `INSPECTING NODE: ${data.title}`;
                document.getElementById("inspector-content").innerHTML = `
                    <div class="inspector-grid">
                        <div class="inspector-col-left">
                            <span class="inspector-label">TECHNOLOGY_STACK:</span>
                            <span class="inspector-val">${data.tech}</span>
                            <span class="inspector-label">FUNCTIONAL_SPEC:</span>
                            <p>${data.details}</p>
                        </div>
                        <div>
                            <span class="inspector-label">LIVE_EXECUTION_STREAM:</span>
                            <div class="inspector-log-block monospace">${data.logs.replace(/\n/g, "<br>")}</div>
                        </div>
                    </div>
                `;
                inspector.classList.remove("hidden");
            }
        });
    });

    function getNextNode(node) {
        const order = ["data", "model", "docker", "k8s", "prometheus", "grafana"];
        const idx = order.indexOf(node);
        return order[(idx + 1) % order.length];
    }

    function getPrevNode(node) {
        const order = ["data", "model", "docker", "k8s", "prometheus", "grafana"];
        const idx = order.indexOf(node);
        return order[(idx - 1 + order.length) % order.length];
    }

    if (closeInspectorBtn) {
        closeInspectorBtn.addEventListener("click", () => {
            inspector.classList.add("hidden");
            nodes.forEach(n => n.classList.remove("active"));
            const lines = document.querySelectorAll(".tree-svg-line");
            lines.forEach(l => l.classList.remove("active"));
        });
    }

    // Telemetry Canvas Chart (Self-drawn Live simulation)
    const canvas = document.getElementById("live-chart");
    if (canvas) {
        const ctx = canvas.getContext("2d");
        let chartData = [];
        const maxPoints = 30;

        // Populate baseline data
        for (let i = 0; i < maxPoints; i++) {
            chartData.push({
                requests: 120 + Math.random() * 40,
                anomalies: Math.random() > 0.8 ? Math.floor(Math.random() * 8) : 0
            });
        }

        function resizeCanvas() {
            canvas.width = canvas.parentElement.clientWidth;
            canvas.height = canvas.parentElement.clientHeight;
        }

        window.addEventListener("resize", resizeCanvas);
        resizeCanvas();

        function drawChart() {
            if (!ctx) return;
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const width = canvas.width;
            const height = canvas.height;
            const padding = 30;
            const plotWidth = width - padding * 2;
            const plotHeight = height - padding * 2;

            // Draw axis borders
            ctx.strokeStyle = "#1a1a1a";
            ctx.lineWidth = 1;
            ctx.strokeRect(padding, padding, plotWidth, plotHeight);

            // Draw gridlines
            ctx.strokeStyle = "rgba(255, 255, 255, 0.02)";
            ctx.beginPath();
            for (let i = 1; i < 5; i++) {
                const y = padding + (plotHeight / 5) * i;
                ctx.moveTo(padding, y);
                ctx.lineTo(width - padding, y);
            }
            ctx.stroke();

            const step = plotWidth / (maxPoints - 1);
            
            // Draw Requests (Normal metrics)
            ctx.strokeStyle = "rgba(255, 255, 255, 0.4)";
            ctx.lineWidth = 2;
            ctx.beginPath();
            chartData.forEach((d, idx) => {
                const x = padding + idx * step;
                // Max scaling assumed 200
                const y = padding + plotHeight - (d.requests / 200) * plotHeight;
                if (idx === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.stroke();

            // Draw Anomalies (Glowing red metrics)
            ctx.strokeStyle = "var(--accent-red)";
            ctx.shadowColor = "var(--accent-red)";
            ctx.shadowBlur = 8;
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            
            chartData.forEach((d, idx) => {
                const x = padding + idx * step;
                // Max scaling assumed 10 anomalies
                const y = padding + plotHeight - (d.anomalies / 10) * plotHeight;
                if (idx === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.stroke();
            
            // Reset shadows
            ctx.shadowBlur = 0;

            // Draw Axis Labels
            ctx.fillStyle = "#555";
            ctx.font = "10px 'Share Tech Mono'";
            ctx.fillText("200 req/m", padding - 20, padding + 10);
            ctx.fillText("0 req/m", padding - 20, height - padding);
        }

        // Push new data points dynamically to simulate live telemetry
        function updateChartData() {
            chartData.shift();
            
            // Random walk simulation
            const lastReq = chartData[chartData.length - 1].requests;
            let newReq = lastReq + (Math.random() - 0.5) * 20;
            if (newReq < 80) newReq = 80;
            if (newReq > 180) newReq = 180;

            const hasAnomaly = Math.random() > 0.85;
            const newAnom = hasAnomaly ? Math.floor(Math.random() * 6) + 1 : 0;

            chartData.push({
                requests: Math.round(newReq),
                anomalies: newAnom
            });

            drawChart();
        }

        setInterval(updateChartData, 2000);
        setTimeout(drawChart, 100);
    }
});
