// Ensure chat starts closed, then auto-popup
document.addEventListener('DOMContentLoaded', function () {
    // Force chat to be closed on page load
    const chatWindow = document.getElementById('chatWindow');
    const chatIcon = document.getElementById('chatIcon');

    if (chatWindow) chatWindow.style.display = 'none';
    if (chatIcon) chatIcon.style.display = 'flex';

    // Clear any existing chat content
    const chatBody = document.getElementById('chatBody');
    if (chatBody) chatBody.innerHTML = '';

    // Then load your datalists
    populateDynamicDatalists();

    // AUTO-POPUP: Open chat automatically after 1 second
    setTimeout(() => {
        if (chatIcon && chatWindow) {
            chatWindow.style.display = 'flex';
            chatIcon.style.display = 'none';
            clearAndShowWelcome();
        }
    }, 1000);
});

// DOM Elements
const chatWidget = document.getElementById('chatWidget');
const chatIcon = document.getElementById('chatIcon');
const chatWindow = document.getElementById('chatWindow');
const minimizeBtn = document.getElementById('minimizeBtn');
const expandBtn = document.getElementById('expandBtn');
const closeBtn = document.getElementById('closeBtn');
const optionPanel = document.getElementById('optionPanel');
const chatBody = document.getElementById('chatBody');
const chatFooter = document.getElementById('chatFooter');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');

// State variables
let isExpanded = false;
let currentContext = null;
let selectedFile = null;
let allPredictions = [];
let productMap = {};
let releaseMap = {};
let platformMap = {};

// Chat icon click handler - FIXED
chatIcon.addEventListener('click', () => {
    console.log('Chat icon clicked - opening chat');
    chatWindow.style.display = 'flex';
    chatIcon.style.display = 'none';

    // Clear everything first, then show welcome
    clearAndShowWelcome();
});

minimizeBtn.addEventListener('click', () => {
    chatWindow.style.display = 'none';
    chatIcon.style.display = 'flex';
    if (isExpanded) {
        chatWindow.classList.remove('expanded');
        expandBtn.innerHTML = '<i class="fas fa-expand"></i>';
        isExpanded = false;
    }
});

expandBtn.addEventListener("click", function () {
  chatWindow.classList.toggle("expanded");

  if (chatWindow.classList.contains("expanded")) {
    // Change icon to "contract"
    expandBtn.innerHTML = '<i class="fas fa-compress"></i>';
    expandBtn.title = "Contract";
  } else {
    // Change icon back to "expand"
    expandBtn.innerHTML = '<i class="fas fa-expand"></i>';
    expandBtn.title = "Expand";
  }
});

closeBtn.addEventListener('click', () => {
    chatWindow.style.display = 'none';
    chatIcon.style.display = 'flex';
});

// Chat message handling
sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

function clearAndShowWelcome() {
    // Clear previous content
    chatBody.innerHTML = '';
    optionPanel.innerHTML = '';
    optionPanel.style.display = 'none';
    chatFooter.style.display = 'none';
    chatBody.style.display = 'block';

    // Create welcome container
    const welcomeContainer = createBotMessage();
    welcomeContainer.innerHTML = `
        <div class="welcome-message">
            <p>👋 Welcome to Test Failure Analyzer! How can I help you today?</p>
            <p>You can select an option below or type your question here.</p>
            <p><strong>Here are quick suggestions to get you started:</strong></p>
        </div>
        <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 15px;">
            <button id="helpBtn" class="option-btn">
                <i class="fas fa-question-circle"></i>
                <span>Help & Information</span>
            </button>
            <button id="cdcarmJsonBtn" class="option-btn">
                <i class="fas fa-file-download"></i>
                <span>Start Test Failure Investigation</span>
            </button>
        </div>
    `;
    chatBody.appendChild(welcomeContainer);
    chatBody.scrollTop = 0; // Ensure no scroll

    // Show footer
    chatFooter.style.display = 'flex';

    // Add listeners
    document.getElementById('helpBtn').addEventListener('click', showHelpInformation);
    document.getElementById('cdcarmJsonBtn').addEventListener('click', showCDCARMJsonOptions);
}


// FIXED: Show buttons without creating another welcome message - CDCARM URL button removed
function showWelcomeButtons() {
    // Put buttons in chatBody (same container as welcome message) instead of optionPanel
    const buttonMessage = createBotMessage();
    buttonMessage.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 15px;">
            <button id="helpBtn" class="option-btn">
                <i class="fas fa-question-circle"></i>
                <span>Help & Information</span>
            </button>
            <button id="cdcarmJsonBtn" class="option-btn">
                <i class="fas fa-file-download"></i>
                <span>Start Test Failure Investigation </span>
            </button>
        </div>
    `;

    chatBody.appendChild(buttonMessage); // Add to chatBody, not optionPanel

    // Add event listeners - CDCARM URL button removed
    document.getElementById('helpBtn').addEventListener('click', showHelpInformation);
    document.getElementById('cdcarmJsonBtn').addEventListener('click', showCDCARMJsonOptions);

    chatFooter.style.display = 'flex';
    chatBody.scrollTop = chatBody.scrollHeight;
}

// Keep the old function for compatibility but make it use the new one
function showWelcomeMessage() {
    clearAndShowWelcome();
}

function showUploadOptions() {
    replyWithBotMessage("Upload & Analysis feature coming soon.");
}

function showHelpInformation() {
    optionPanel.style.display = 'none';
    chatBody.style.display = 'block';
    chatFooter.style.display = 'flex';
    currentContext = 'help';

    showTypingIndicator().then(() => {
        const helpMessage = createBotMessage();
        helpMessage.innerHTML = `
            <p><strong>Test Failure Analyzer Help</strong></p>
            <p>This assistant can help you with:</p>
            <ul style="margin-left: 20px; padding-left: 0;">
                <li><strong>Fetch CDCARM JSON</strong> - Download test failure data as JSON for offline analysis</li>
            </ul>
            <p>To get started, select an option from the menu or type your question below.</p>
           <button class="back-to-menu" id="backToMenuHelp"><i class="fas fa-home"></i><span style="margin-left: 6px;">Home</span>
           </button>

        `;
        chatBody.appendChild(helpMessage);
        chatBody.scrollTop = chatBody.scrollHeight;

        document.getElementById('backToMenuHelp').addEventListener('click', showMainMenu);
    });
}

function showMainMenu() {
    clearAndShowWelcome();
    currentContext = null;
    selectedFile = null;
}

function sendMessage() {
    const message = chatInput.value.trim();
    if (message) {
        const userMsg = createUserMessage(message);
        chatBody.appendChild(userMsg);
        chatInput.value = '';
        chatBody.scrollTop = chatBody.scrollHeight;

        showTypingIndicator().then(() => {
            processMessage(message);
        });
    }
}

function processMessage(message) {
    const lowerMsg = message.toLowerCase();

    if (lowerMsg.includes('menu') || lowerMsg.includes('back') || lowerMsg.includes('options')) {
        showMainMenu();
        return;
    }

    if (currentContext === 'help') {
        // Your existing help context code
    } else {
        if (lowerMsg.includes('hello') || lowerMsg.includes('hi')) {
            replyWithBotMessage("Hello! 👋 How can I help you today?");
        } else if (lowerMsg.includes('json') || lowerMsg.includes('download') || lowerMsg.includes('fetch')) {
            showCDCARMJsonOptions();
        } else {
            replyWithBotMessage("I'm here to help you analyze test failures. How can I assist you today?");
        }
    }
}

function handleJsonDownload(payload) {
    console.log('Handling JSON download payload:', payload);

    if (!payload) {
        replyWithBotMessage("Error: No download data received");
        return;
    }

    const isValidPayload = payload.data_type === "json_download" ||
        (payload.content && payload.filename);

    if (!isValidPayload) {
        replyWithBotMessage("Error: Invalid download data format");
        console.log('Invalid payload format:', payload);
        return;
    }

    const content = payload.content;
    const filename = payload.filename || 'cdcarm_data.json';
    const recordCount = payload.record_count || 'unknown number of';

    const downloadMessage = createBotMessage();
    downloadMessage.innerHTML = `
        <div class="download-container">
            <p>✅ Successfully fetched ${recordCount} records.</p>
            <button class="download-btn" id="downloadJsonBtn">
                <i class="fas fa-download"></i> Download results

            </button>
            <button class="back-to-menu" id="startInvestigationBtn">
                <i class="fas fa-redo"></i> Start Test Failure Investigation
            </button>

        </div>
    `;
    chatBody.appendChild(downloadMessage);
    chatBody.scrollTop = chatBody.scrollHeight;

    document.getElementById('downloadJsonBtn').addEventListener('click', () => {
        try {
            let jsonData;
            try {
                jsonData = atob(content);
            } catch (e) {
                jsonData = content;
            }

            console.log('Decoded JSON data (first 100 chars):',
                typeof jsonData === 'string' ? jsonData.substring(0, 100) : "Not a string");

            const blob = new Blob([jsonData], { type: 'application/json' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            replyWithBotMessage("Download started. The file should be saved to your downloads folder.");
        } catch (error) {
            console.error('Download error:', error);
            replyWithBotMessage(`Error downloading file: ${error.message}. Please try again.`);
        }
    });

    document.getElementById('startInvestigationBtn').addEventListener('click', showCDCARMJsonOptions);

}

async function populateDynamicDatalists() {
    try {
        // Fetch Products
        const productRes = await fetch("/api/products");
        const products = await productRes.json();
        const productList = document.getElementById("productsList");
        products.forEach(p => {
            productMap[p.Name] = p.Id;
            const opt = document.createElement("option");
            opt.value = p.Name;
            productList.appendChild(opt);
        });
        console.log(`✅ Products fetched: ${products.length}`);

        // Fetch Releases
        const releaseRes = await fetch("/api/releases");
        const releases = await releaseRes.json();
        const releaseList = document.getElementById("releasesList");
        releases.forEach(r => {
            releaseMap[r.Name] = r.Id;
            const opt = document.createElement("option");
            opt.value = r.Name;
            releaseList.appendChild(opt);
        });
        console.log(`✅ Releases fetched: ${releases.length}`);

        // Fetch Platforms
        const platformRes = await fetch("/api/platforms");
        const platforms = await platformRes.json();
        const platformList = document.getElementById("platformsList");
        platforms.forEach(pl => {
            platformMap[pl.Name] = pl.Id;
            const opt = document.createElement("option");
            opt.value = pl.Name;
            platformList.appendChild(opt);
        });
        console.log(`✅ Platforms fetched: ${platforms.length}`);
    } catch (error) {
        console.error("⚠️ Error loading datalists:", error);
    }
}

function showTypingIndicator() {
    return new Promise(resolve => {
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = '<span></span><span></span><span></span>';
        chatBody.appendChild(typingIndicator);
        chatBody.scrollTop = chatBody.scrollHeight;

        setTimeout(() => {
            chatBody.removeChild(typingIndicator);
            resolve();
        }, 800);
    });
}

function createUserMessage(text) {
    const message = document.createElement('div');
    message.className = 'message user-message';
    message.textContent = text;
    return message;
}

function createBotMessage() {
    const message = document.createElement('div');
    message.className = 'message bot-message';
    return message;
}

function replyWithBotMessage(text) {
    const botReply = createBotMessage();
    botReply.textContent = text;
    chatBody.appendChild(botReply);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function showCDCARMJsonOptions() {
    optionPanel.style.display = 'none';
    chatBody.style.display = 'block';
    chatFooter.style.display = 'flex';
    currentContext = 'cdcarm_json';

    // Remove any existing form before creating a new one
    const existingForm = document.getElementById('cdcarmFormContainer');
    if (existingForm) {
        existingForm.remove();
    }

    showTypingIndicator().then(() => {
        const message = createBotMessage();
        message.id = "cdcarmFormContainer"; // Assign ID to detect duplicates
        message.innerHTML = `
            <p>Let's fetch ARM Error report data for investigation. Please provide the following information:</p>
            <div class="cdcarm-json-options active">
                <div class="option-group">
                    <label class="option-label">Products:</label>
                    <input type="text" class="option-input" id="productsInput" list="productsList" placeholder="DISCO" value="DISCO">
                </div>
                <div class="option-group">
                    <label class="option-label">Releases:</label>
                    <input type="text" class="option-input" id="releasesInput" list="releasesList" placeholder="26.1" value="26.1">
                </div>
                <div class="option-group">
                    <label class="option-label">Platforms:</label>
                    <input type="text" class="option-input" id="platformsInput" list="platformsList" placeholder="Windows" value="Windows">
                </div>
                <div class="option-group">
                    <label class="option-label">Min Failing Builds:</label>
                    <input type="number" class="option-input" id="minFailingInput" placeholder="2" value="2" min="1">
                </div>
                <button class="fetch-json-btn" id="fetchJsonBtn">
                    <i class="fas fa-download"></i> Run Predictions
                </button>
            </div>
        `;

        chatBody.appendChild(message);
        chatBody.scrollTop = chatBody.scrollHeight;

        // Attach new event listener to the fresh button
        const fetchJsonBtn = document.getElementById('fetchJsonBtn');
        if (fetchJsonBtn) {
            fetchJsonBtn.addEventListener('click', fetchCDCARMJson);
        }
    });
}



/* function fetchCDCARMJson() {
    const products = (document.getElementById('productsInput').value.trim() || "DISCO")
        .split(",").map(p => p.trim()).filter(p => p);
    const releases = (document.getElementById('releasesInput').value.trim() || "26.1")
        .split(",").map(r => r.trim()).filter(r => r);
    const platforms = (document.getElementById('platformsInput').value.trim() || "Windows")
        .split(",").map(p => p.trim()).filter(p => p);
    const minFailingBuilds = document.getElementById('minFailingInput').value.trim() || "2";
    const ownerFilter = document.getElementById('ownerJsonInput')?.value.trim() || "__all__";

    const formElement = document.querySelector(".cdcarm-json-options");
    if (formElement) {
        formElement.style.opacity = "0.5";
        formElement.style.pointerEvents = "none";
    }

    const userMsg = createUserMessage(
        `Running prediction for Products: ${products}, Releases: ${releases}, Platforms: ${platforms}, Min Failing Builds: ${minFailingBuilds}`
    );
    chatBody.appendChild(userMsg);
    chatBody.scrollTop = chatBody.scrollHeight;

    const progressMessage = createBotMessage();
    progressMessage.innerHTML = `
        <div class="status-with-progress">
            <div class="status-icon">⏳</div>
            <div class="status-info">
                <p class="status-text">Running prediction... Please wait while we analyze the test failures.</p>
                <div class="progress-container">
                    <div class="progress-bar" id="jsonProgressBar"></div>
                </div>
            </div>
        </div>
    `;
    chatBody.appendChild(progressMessage);
    chatBody.scrollTop = chatBody.scrollHeight;
    const progressBar = document.getElementById('jsonProgressBar');
    progressBar.style.width = '30%';

    fetch("/fetch_cdcarm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            products,
            releases,
            platforms,
            min_failing_builds: minFailingBuilds
        })
    })
    .then(response => response.json())
    .then(data => {
        progressBar.style.width = '100%';
        setTimeout(() => chatBody.removeChild(progressMessage), 500);

        console.log("Backend response:", data);

        const allTests = [
            ...(data.predicted || []),
            ...(data.unpredicted || [])
        ].filter(item => !item.HasInvestigation);

        if (!allTests.length) {
            replyWithBotMessage("⚠ No tests to display (all failing tests already have investigations).");
        } else {
            displayPredictionResults(allTests, ownerFilter);
        }
    })
    .catch(error => {
        console.error("Prediction flow error:", error);
        progressBar.style.width = '100%';
        setTimeout(() => {
            chatBody.removeChild(progressMessage);
            replyWithBotMessage(`⚠️ Error during prediction: ${error.message}`);
        }, 500);
    });
} */

async function fetchCDCARMJson() {
    const products = (document.getElementById('productsInput').value.trim() || "DISCO")
        .split(",").map(p => p.trim()).filter(p => p);
    const releases = (document.getElementById('releasesInput').value.trim() || "26.1")
        .split(",").map(r => r.trim()).filter(r => r);
    const platforms = (document.getElementById('platformsInput').value.trim() || "Windows")
        .split(",").map(p => p.trim()).filter(p => p);
    const minFailingBuilds = document.getElementById('minFailingInput').value.trim() || "2";
    const ownerFilter = document.getElementById('ownerJsonInput')?.value.trim() || "__all__";

    // Disable form while running
    const formElement = document.querySelector(".cdcarm-json-options");
    if (formElement) {
        formElement.style.opacity = "0.5";
        formElement.style.pointerEvents = "none";
    }

    // User message
    const userMsg = createUserMessage(
        `Running prediction for Products: ${products}, Releases: ${releases}, Platforms: ${platforms}, Min Failing Builds: ${minFailingBuilds}`
    );
    chatBody.appendChild(userMsg);
    chatBody.scrollTop = chatBody.scrollHeight;

  const prog = showPredictionProgress(chatBody, /* taskId: */ `pred_${Date.now()}`);

  try {
    // STEP 1: Fetch from ARM
    prog.setActive(1);
    // If you can’t measure network progress, mark as indeterminate:
    prog.setIndeterminate(1, true);
    const response = await fetch("/fetch_cdcarm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ products, releases, platforms, min_failing_builds: minFailingBuilds })
    });
    prog.setIndeterminate(1, false);
    prog.setProgress(1, 100);
    prog.setDone(1);

    // STEP 2: Extract patterns from ARM (client-side parse/filter)
    prog.setActive(2);
    const data = await response.json();

    // If you loop N items, update % as you go:
    const items = [...(data.predicted || []), ...(data.unpredicted || [])];
    if (items.length === 0) {
      prog.setProgress(2, 100);
    } else {
      let processed = 0;
      for (const item of items) {
        // your real extraction logic here ...
        processed++;
        prog.setProgress(2, Math.round((processed / items.length) * 100));
      }
    }
    prog.setDone(2);

    // STEP 3: Match in Azure DevOps
    prog.setActive(3);
    // If server already did matching, show quick completion:
    prog.setIndeterminate(3, true);
    await Promise.resolve(); // or a small await call if you actually do work here
    prog.setIndeterminate(3, false);
    prog.setProgress(3, 100);
    prog.setDone(3);

    // STEP 4: Rendering to table
    prog.setActive(4);
    const allTests = items.filter(i => !i.HasInvestigation);

    // If rendering many rows, update by chunk:
    const chunk = 50;
    let rendered = 0;
    const toRender = allTests.length;

    // If your renderer runs in one call, you can still fake a responsive bar:
    if (toRender > 0) {
      for (let i = 0; i < toRender; i += chunk) {
        const slice = allTests.slice(i, i + chunk);
        // Option A: incremental render (append slice rows) and yield:
        // appendRows(slice);
        // await new Promise(r => requestAnimationFrame(r));

        rendered = Math.min(toRender, i + chunk);
        prog.setProgress(4, Math.round((rendered / toRender) * 100));
      }
    } else {
      prog.setProgress(4, 100);
    }

    // Now call your existing renderer once:
    displayPredictionResults(allTests, "__choose__");

    prog.setDone(4);
    prog.finish();

  } catch (e) {
    console.error(e);
    prog.setError(e?.message || String(e));
  }
}

function showPredictionProgress(parentEl = chatBody) {
  // Remove any old card
  parentEl.querySelector(".prediction-progress-card")?.remove();

  // Create message container (reuse your bubble style)
  const msg = createBotMessage();
  const card = document.createElement("div");
  card.className = "prediction-progress-card";
  card.innerHTML = `
    <div class="prediction-progress-header">
      <span class="hourglass">⏳</span>
      <span>Running prediction… Please wait while we analyze the test failures.</span>
    </div>
    <ul class="progress-steps">
      <li class="step active" data-step="1">
        <span class="icon">📡</span>
        <span class="label">Fetching data from ARM</span>
        <span class="state spinner"></span>
      </li>
      <li class="step pending" data-step="2">
        <span class="icon">🧩</span>
        <span class="label">Extracting patterns from ARM</span>
        <span class="state"></span>
      </li>
      <li class="step pending" data-step="3">
        <span class="icon">🔍</span>
        <span class="label">Matching patterns in Azure DevOps</span>
        <span class="state"></span>
      </li>
      <li class="step pending" data-step="4">
        <span class="icon">📊</span>
        <span class="label">Rendering results</span>
        <span class="state"></span>
      </li>
    </ul>
    <div class="progress-footer-note">Tip: this may take a minute depending on build size.</div>
    <div class="progress-error" style="display:none;"></div>
  `;
  msg.appendChild(card);
  parentEl.appendChild(msg);
  parentEl.scrollTop = parentEl.scrollHeight;

  const steps = Array.from(card.querySelectorAll(".step"));
  const getStepEl = (n) => steps.find(s => Number(s.dataset.step) === n);

  function setActive(n) {
    steps.forEach(s => {
      const st = s.querySelector(".state");
      s.classList.remove("active");
      if (!s.classList.contains("done")) {
        s.classList.add("pending");
        st.className = "state"; // clear
      }
    });
    const el = getStepEl(n);
    if (!el) return;
    el.classList.remove("pending");
    el.classList.add("active");
    el.querySelector(".state").className = "state spinner";
  }

  function setDone(n) {
    const el = getStepEl(n);
    if (!el) return;
    el.classList.remove("pending", "active");
    el.classList.add("done");
    el.querySelector(".state").className = "state checkmark";
  }

  function setError(message) {
    const err = card.querySelector(".progress-error");
    err.textContent = message || "Something went wrong during prediction.";
    err.style.display = "block";
  }

  function finish() {
    // Mark any remaining active as done
    steps.forEach(s => { if (s.classList.contains("active")) s.classList.replace("active","done"); s.querySelector(".state").className = "state checkmark"; });
    card.querySelector(".progress-footer-note").textContent = "Completed.";
  }

  // Optional: simple auto-advance for demos
  function autoAdvance(msPerStep = 1500) {
    let n = 1;
    const timer = setInterval(() => {
      setDone(n);
      n++;
      if (n <= 4) setActive(n);
      if (n > 4) { clearInterval(timer); finish(); }
    }, msPerStep);
    return () => clearInterval(timer);
  }

  // controller API
  return { root: card, setActive, setDone, setError, finish, autoAdvance };
}

// Map of taskId -> controller (optional, if you may run multiple concurrently)
const predictionProgressRegistry = new Map();

/**
 * Show a 4-step prediction progress card with per-step meters.
 * @param {HTMLElement} parentEl
 * @param {string} taskId - unique id for this run (e.g. timestamp, uuid)
 */
function showPredictionProgress(parentEl = chatBody, taskId = `task_${Date.now()}`) {
  // Remove old card of same taskId if it exists
  predictionProgressRegistry.get(taskId)?.root?.remove();

  const msg  = createBotMessage();
  const card = document.createElement("div");
  card.className = "prediction-progress-card";
  card.innerHTML = `
    <div class="prediction-progress-header">
      <span class="hourglass">⏳</span>
      <span>Running prediction… Please wait while we analyze the test failures.</span>
    </div>
    <ul class="progress-steps">
      <li class="step active" data-step="1">
        <span class="icon">📡</span>
        <span class="label">Fetching data from ARM</span>
        <span class="state spinner"></span>
        <div class="meter"><div class="bar"></div></div>
      </li>
      <li class="step pending" data-step="2">
        <span class="icon">🧩</span>
        <span class="label">Extracting patterns from ARM</span>
        <span class="state"></span>
        <div class="meter"><div class="bar"></div></div>
      </li>
      <li class="step pending" data-step="3">
        <span class="icon">🔍</span>
        <span class="label">Matching patterns in Azure DevOps</span>
        <span class="state"></span>
        <div class="meter"><div class="bar"></div></div>
      </li>
      <li class="step pending" data-step="4">
        <span class="icon">📊</span>
        <span class="label">Rendering results</span>
        <span class="state"></span>
        <div class="meter"><div class="bar"></div></div>
      </li>
    </ul>
    <div class="progress-footer-note">Tip: this may take a minute depending on build size.</div>
    <div class="progress-error" style="display:none;"></div>
  `;
  msg.appendChild(card);
  parentEl.appendChild(msg);
  parentEl.scrollTop = parentEl.scrollHeight;

  const steps = Array.from(card.querySelectorAll(".step"));
  const getStepEl = (n) => steps.find(s => Number(s.dataset.step) === n);
  const getBar    = (n) => getStepEl(n)?.querySelector(".bar");
  const getState  = (n) => getStepEl(n)?.querySelector(".state");

  function setActive(n) {
    steps.forEach(s => {
      const st = s.querySelector(".state");
      if (!s.classList.contains("done")) {
        s.classList.remove("active");
        s.classList.add("pending");
        st.className = "state";
      }
      s.classList.remove("indeterminate");
    });
    const el = getStepEl(n);
    if (!el) return;
    el.classList.remove("pending");
    el.classList.add("active");
    getState(n).className = "state spinner";
  }

  function setDone(n) {
    const el = getStepEl(n);
    if (!el) return;
    el.classList.remove("pending","active","indeterminate");
    el.classList.add("done");
    getState(n).className = "state checkmark";
    const bar = getBar(n);
    if (bar) bar.style.width = "100%";
  }

  // 0–100 numeric progress; switches off indeterminate
  function setProgress(n, pct) {
    const el = getStepEl(n);
    if (!el) return;
    el.classList.remove("indeterminate");
    const bar = getBar(n);
    if (bar) bar.style.width = `${Math.max(0, Math.min(100, pct))}%`;
  }

  // Turn on/off indeterminate shimmer for a step’s bar
  function setIndeterminate(n, on = true) {
    const el = getStepEl(n);
    if (!el) return;
    if (on) {
      el.classList.add("indeterminate");
      const bar = getBar(n);
      if (bar) bar.style.width = "40%"; // width used by animation
    } else {
      el.classList.remove("indeterminate");
    }
  }

  function setLabel(n, text) {
    const el = getStepEl(n);
    if (!el) return;
    const lbl = el.querySelector(".label");
    if (lbl) lbl.textContent = text;
  }

  function setError(message) {
    const err = card.querySelector(".progress-error");
    err.textContent = message || "Something went wrong during prediction.";
    err.style.display = "block";
  }

  function finish() {
    steps.forEach((s, idx) => {
      const n = idx + 1;
      if (!s.classList.contains("done")) {
        setDone(n);
      }
    });
    card.querySelector(".progress-footer-note").textContent = "Completed.";
  }

  const controller = { taskId, root: card, setActive, setDone, setProgress, setIndeterminate, setLabel, setError, finish };
  predictionProgressRegistry.set(taskId, controller);
  return controller;
}


// helper for test link
function buildTestLink(testName, productName, releaseName, platformName) {
    // Resolve product
    if (!productName) {
        const input = document.getElementById('productsInput');
        productName = input ? input.value.trim() : "DISCO";
    }

    // Resolve release
    if (!releaseName) {
        const input = document.getElementById('releasesInput');
        releaseName = input ? input.value.trim() : "26.1";
    }

    // Resolve platform
    if (!platformName) {
        const input = document.getElementById('platformsInput');
        platformName = input ? input.value.trim() : "Windows";
    }

    const encoded = encodeURIComponent(testName);
    const productId = productMap[productName] || 72;       // fallback: DISCO = 72
    const releaseId = releaseMap[releaseName] || 289;      // fallback: 25.2 = 289
    const platformId = platformMap[platformName] || 1;     // fallback: Windows = 1

    return `https://cdcarm.win.ansys.com/Reports/Unified/ErrorReport/Product/${productId}?applicationId=-1&platformId=${platformId}&releaseId=${releaseId}&allPackages=True&filterCollection=MatchType%3DAll%26Filter0%3DType%3AARM.WebFilters.TestResults.Filters.TestNameFilter%2COperator%3ACONTAINS%2CValue%3A${encoded}&highlighterCollection=MatchType%3DAll%26Filter0%3DType%3AARM.WebFilters.TestResults.Highlighters.RunAgeHighlighter%2COperator%3AGREATER_THAN_OR_EQUAL%2CValue%3A7&officialOnly=False&chronicFailureThreshold=0&noCache=False&showNonChronicFailures=true`;
}



// helper for investigation link
function buildInvestigationLink(workItemId) {
    return `https://tfs.ansys.com:8443/tfs/ANSYS_Development/Portfolio/_workitems/edit/${workItemId}`;
}

/*function displayClusteredResults(clusteredSummary) {
    if (!clusteredSummary || !clusteredSummary.length) {
        const botMsg = createBotMessage();
        botMsg.innerHTML = `
            <div style="padding:10px; border:1px solid #ccc; border-radius:6px; background:#f8f9fa;">
                <h4>❌ No Similar Error Clusters Found</h4>
                <p>We couldn't group the test failures into meaningful clusters based on similarity of failure messages.</p>
                <ul style="margin-left:18px; color:#555; font-size:0.9em;">
                <li>The failure messages might be too unique or lack common patterns.</li>
                <li>There may be insufficient test failures to form clusters.</li>
                <li>Current filters (Product: <b>${productInput}</b>, Release: <b>${releaseInput}</b>, Platform: <b>${platformInput}</b>) might be too restrictive.</li>
                </ul>
                <p><b>Next Steps:</b></p>
                <ul style="margin-left:18px; color:#555; font-size:0.9em;">
                <li>Review individual failed test results manually.</li>
                <li>Adjust the "Min Failing Builds" parameter and try again.</li>
                <li>Verify if the error logs have enough similarity for clustering.</li>
                </ul>
            </div>
            `;
        chatBody.appendChild(botMsg);
        chatBody.scrollTop = chatBody.scrollHeight;
        return;
    }

    // Get current inputs for fallback resolution inside buildTestLink
    const productInput = document.getElementById('productsInput')?.value.trim() || "DISCO";
    const releaseInput = document.getElementById('releasesInput')?.value.trim() || "26.1";
    const platformInput = document.getElementById('platformsInput')?.value.trim() || "Windows";

    const botMsg = createBotMessage();
    botMsg.innerHTML = `
      <h4>🧩 Clustered Failure Groups (Unanchored)</h4>
      <div style="margin-bottom:8px; font-size: 0.9em; color: #555;">
        <p>🔹 These groups were formed by clustering unpredicted test failures based on similar failure messages.</p>
        <p>🔹 <strong>Test name links:</strong> open the ARM test page in a new tab.</p>
      </div>
      ${clusteredSummary.map((group, groupIndex) => {
        // Deduplicate tests within each group
        const uniqueTests = Array.from(new Map(group.map(t => [t.TestName + t.Owner, t])).values());
        return `
          <div class="cluster-block" style="border:1px solid #ccc; padding:10px; margin-bottom:10px; border-radius:6px;">
            <h5 style="margin-bottom:6px;">
              🧠 Cluster ${groupIndex + 1}
              <span style="background:#eee; font-size:0.8em; padding:2px 6px; border-radius:4px; margin-left:6px;">
                ${uniqueTests.length} test${uniqueTests.length > 1 ? 's' : ''}
              </span>
            </h5>
            <ul style="padding-left: 16px;">
              ${uniqueTests.map(test => `
                <li style="margin-bottom:4px;">
                  <a href="${buildTestLink(test.TestName, test.Product || productInput, releaseInput, platformInput)}" target="_blank" style="text-decoration:underline; color:#007bff;">
                    ${test.TestName}
                  </a>
                  <span style="margin-left: 10px; color: #888;">(${test.Owner})</span>
                </li>
              `).join('')}
            </ul>
          </div>
        `;
      }).join('')}
      <button class="back-to-menu" id="backToMenuClustered" style="margin-top:10px;">
        <i class="fas fa-home"></i><span style="margin-left: 6px;">Home</span>
      </button>
    `;
    chatBody.appendChild(botMsg);
    chatBody.scrollTop = chatBody.scrollHeight;

    document.getElementById('backToMenuClustered').addEventListener('click', () => {
        allPredictions = [];
        showMainMenu();
    });
}*/

/**
 * Displays prediction results in the chat window, allowing filtering by owner and exporting to CSV.
 * If no predicted tests exist, shows all failing tests with a message.
 * @param {Array} predictions - Array of prediction result objects to display.
 * @param {string} [ownerFilter=""] - Optional owner filter to restrict displayed results.
 */
/* function displayPredictionResults(predictions, ownerFilter) {
    // Guard
    if (!Array.isArray(predictions) || predictions.length === 0) {
        const botMsg = createBotMessage();
        botMsg.innerHTML = `<p>No matching tests found for the selected owner.</p>`;
        chatBody.appendChild(botMsg);
        chatBody.scrollTop = chatBody.scrollHeight;
        return;
    }

    // --- First-instance logic: show placeholder until user chooses ---
    const isInitial = ownerFilter === "" || ownerFilter == null || ownerFilter === "__choose__";
    const normalizedOwner = isInitial ? "__choose__" : String(ownerFilter || "__all__").trim().toLowerCase();

    // Build owner -> unique tests and overall unique test count
    const ownerTestMap = {};
    const allUniqueTests = new Set();
    for (const p of predictions) {
        const owner = (p.Owner || "Unknown").trim();
        const test  = p.TestName || "Unnamed Test";
        allUniqueTests.add(test);
        (ownerTestMap[owner] ||= new Set()).add(test);
    }
    const totalUniqueCount = allUniqueTests.size;

    // Owner options: placeholder (selected) on first instance
    const ownerOptions = [
        `<option value="__choose__"${isInitial ? " selected" : ""} hidden>— Select All or an owner —</option>`,
        `<option value="__all__"${(!isInitial && normalizedOwner === "__all__") ? " selected" : ""}>All (${totalUniqueCount})</option>`
    ].concat(
        Object.entries(ownerTestMap)
            .sort((a,b) => a[0].localeCompare(b[0]))
            .map(([owner, tests]) =>
                `<option value="${owner}" ${(!isInitial && owner.toLowerCase() === normalizedOwner) ? "selected" : ""}>
                    ${owner} (${tests.size})
                 </option>`
            )
    ).join("");

    // Split predicted/unpredicted (robust yes-check)
    const isYes = (v) => {
        if (v === true) return true;
        const s = String(v ?? "").trim().toLowerCase();
        return s === "yes";
    };
    let predictedTests   = predictions.filter(p => isYes(p.IsPredicted));
    let unpredictedTests = predictions.filter(p => !isYes(p.IsPredicted));

    // Apply owner filter only if not initial and not All
    if (!isInitial && normalizedOwner !== "__all__") {
        const matchOwner = (p) => String(p.Owner || "Unknown").trim().toLowerCase() === normalizedOwner;
        predictedTests   = predictedTests.filter(matchOwner);
        unpredictedTests = unpredictedTests.filter(matchOwner);
    }

    // Sort predicted by confidence score (desc)
    predictedTests.sort((a, b) => (b.ConfidenceScore || 0) - (a.ConfidenceScore || 0));

    // Row builder (group by test)
    const createTableRows = (tests) => {
        const grouped = {};
        for (const p of tests) {
            const test = p.TestName || "Unnamed Test";
            (grouped[test] ||= {
                Owner: p.Owner || "Unknown",
                Product: p.Product,
                Release: p.Release,
                Platform: p.Platform,
                WorkItems: new Set(),
                IsPredicted: isYes(p.IsPredicted)
            });
            const ids = String(p.PredictedWorkItemId || "")
                .split(";").map(s => s.trim()).filter(Boolean);
            ids.forEach(id => grouped[test].WorkItems.add(id));
        }
        return Object.entries(grouped).map(([testName, info]) => `
            <tr>
              <td><a href="${buildTestLink(testName, info.Product, info.Release, info.Platform)}" target="_blank">${testName}</a></td>
              <td>${info.Owner}</td>
              <td>${
                info.IsPredicted && info.WorkItems.size
                  ? [...info.WorkItems].map(wi =>
                      `<a href="https://tfs.ansys.com:8443/tfs/ANSYS_Development/Portfolio/_workitems/edit/${wi}" target="_blank">${wi}</a>`
                    ).join(", ")
                  : "No Prediction"
              }</td>
            </tr>
        `).join("");
    };

    // Clear previous and render
    chatBody.querySelector(".prediction-results-container")?.remove();

    const botMsg = createBotMessage();
    botMsg.classList.add("prediction-results-container");
    botMsg.innerHTML = `
      <h4>🔎 Test Failure Results:</h4>
      <div class="prediction-controls">
        <label for="ownerFilterSelect">Owner Filter:</label>
        <select class="option-input ownerFilterSelect" aria-label="Owner Filter">${ownerOptions}</select>
        <button class="exportCSV"${isInitial ? " disabled" : ""}><i class="fas fa-download"></i> Export CSV</button>
      </div>

      <div class="prediction-notes">
        <p><strong>🔹 Sorting:</strong> Tests are sorted by descending confidence score.</p>
        <p><strong>🔹 Tip:</strong> Changing the owner updates the tables immediately.</p>
        <p><strong>🔹 Test Names:</strong> Click to open the corresponding ARM report.</p>
        <p><strong>🔹 Predicted Work Item IDs:</strong> Click to open the TFS bug page.</p>
      </div>

      ${
        isInitial
          ? `<div class="placeholder" style="padding:10px 12px; border-radius:8px; background:#f6f7fb; color:#4a4f63; margin:4px 0 12px;">
                <strong>👉 Choose “All” or one of the owners</strong> to load the results.
             </div>`
          : (predictedTests.length
              ? `
                <h5>✅ Predicted Tests</h5>
                <div style="max-height:200px; overflow:auto;">
                  <table class="prediction-table predictionResultTable predictedTable">
                    <thead><tr><th>Test Name</th><th>Owner</th><th>Predicted Work Item IDs</th></tr></thead>
                    <tbody>${createTableRows(predictedTests)}</tbody>
                  </table>
                </div>`
              : `<p>No predicted tests available.</p>`
            )
      }

      ${
        !isInitial
          ? (unpredictedTests.length
              ? `
                <h5>⚠ Unpredicted Tests</h5>
                <div style="max-height:200px; overflow:auto;">
                  <table class="prediction-table predictionResultTable unpredictedTable">
                    <thead><tr><th>Test Name</th><th>Owner</th><th>Status</th></tr></thead>
                    <tbody>${createTableRows(unpredictedTests)}</tbody>
                  </table>
                </div>`
              : `<p>No unpredicted tests available.</p>`
            )
          : ``
      }

      <button class="startInvestigationBtn" style="margin-top:10px;">
        <i class="fas fa-redo"></i> Start Test Failure Investigation
      </button>
    `;
    chatBody.appendChild(botMsg);
    chatBody.scrollTop = chatBody.scrollHeight;

    // Wire controls
    const ownerSelectEl = botMsg.querySelector(".ownerFilterSelect");
    ownerSelectEl.addEventListener("change", (e) => {
        const v = (e.target.value || "__all__").trim();
        if (v === "__choose__") return;          // ignore placeholder
        displayPredictionResults(predictions, v); // instant re-render
    });

    // CSV/Investigation handlers
    const exportBtn = botMsg.querySelector(".exportCSV");
    exportBtn.addEventListener("click", () => {
        if (exportBtn.disabled) return;
        const table = botMsg.querySelector(".predictedTable") || botMsg.querySelector(".predictionResultTable");
        exportTableToCSV(table);
    });

    botMsg.querySelector(".startInvestigationBtn").addEventListener("click", showCDCARMJsonOptions);
}
 */

function displayPredictionResults(predictions, ownerFilter) {
    // Guard
    if (!Array.isArray(predictions) || predictions.length === 0) {
        const botMsg = createBotMessage();
        botMsg.innerHTML = `<p>No matching tests found for the selected owner.</p>`;
        chatBody.appendChild(botMsg);
        chatBody.scrollTop = chatBody.scrollHeight;
        return;
    }

    // Helpers
    const norm = (v) => (v == null ? "" : String(v)).trim().toLowerCase();
    const isYes = (v) => v === true || norm(v) === "yes";

    // First-instance (placeholder) rules
    // ownerFilter accepted forms: undefined/null/"__choose__" (initial), "__all__", string (one owner), array<string> (multiple)
    const isInitial = ownerFilter == null || ownerFilter === "__choose__" ||
                      (Array.isArray(ownerFilter) && ownerFilter.length === 0);

    let selectedAll = false;
    let selectedSet = null; // Set of normalized owners if any chosen

    if (!isInitial) {
        if (ownerFilter === "__all__") {
            selectedAll = true;
        } else if (Array.isArray(ownerFilter)) {
            selectedAll = ownerFilter.includes("__all__");
            selectedSet  = new Set(ownerFilter.map(o => norm(o)));
        } else {
            selectedSet = new Set([norm(ownerFilter)]);
        }
    }

    // Build owner -> unique tests and global unique test count
    const ownerTestMap = {};
    const allUniqueTests = new Set();
    for (const p of predictions) {
        const owner = (p.Owner || "Unknown").trim();
        const test  = p.TestName || "Unnamed Test";
        allUniqueTests.add(test);
        (ownerTestMap[owner] ||= new Set()).add(test);
    }
    const totalUniqueCount = allUniqueTests.size;

    // Split predicted/unpredicted
    let predictedTests   = predictions.filter(p => isYes(p.IsPredicted));
    let unpredictedTests = predictions.filter(p => !isYes(p.IsPredicted));

    // Apply owner filtering only after Apply (i.e., not in initial placeholder state)
    if (!isInitial && !selectedAll && selectedSet && selectedSet.size > 0) {
        const matchOwner = (p) => selectedSet.has(norm(p.Owner || "Unknown"));
        predictedTests   = predictedTests.filter(matchOwner);
        unpredictedTests = unpredictedTests.filter(matchOwner);
    }
    // selectedAll -> no filtering

    // Sort predicted by confidence score
    predictedTests.sort((a, b) => (b.ConfidenceScore || 0) - (a.ConfidenceScore || 0));

    // Row builder (group by TestName)
    const createTableRows = (tests) => {
        const grouped = {};
        for (const p of tests) {
            const test = p.TestName || "Unnamed Test";
            (grouped[test] ||= {
                Owner: p.Owner || "Unknown",
                Product: p.Product,
                Release: p.Release,
                Platform: p.Platform,
                WorkItems: new Set(),
                IsPredicted: isYes(p.IsPredicted)
            });
            const ids = String(p.PredictedWorkItemId || "")
                .split(";").map(s => s.trim()).filter(Boolean);
            ids.forEach(id => grouped[test].WorkItems.add(id));
        }
        return Object.entries(grouped).map(([testName, info]) => `
            <tr>
              <td><a href="${buildTestLink(testName, info.Product, info.Release, info.Platform)}" target="_blank">${testName}</a></td>
              <td>${info.Owner}</td>
              <td>${
                info.IsPredicted && info.WorkItems.size
                  ? [...info.WorkItems].map(wi =>
                      `<a href="https://tfs.ansys.com:8443/tfs/ANSYS_Development/Portfolio/_workitems/edit/${wi}" target="_blank">${wi}</a>`
                    ).join(", ")
                  : "No Prediction"
              }</td>
            </tr>
        `).join("");
    };

    // Clear previous block and render container
    chatBody.querySelector(".prediction-results-container")?.remove();

    const botMsg = createBotMessage();
    botMsg.classList.add("prediction-results-container");
    botMsg.innerHTML = `
      <h4>🔎 Test Failure Results:</h4>

      <div class="prediction-controls">
        <label>Owner Filter:</label>

        <!-- Chips Summary + Collapsible List -->
        <div class="owner-chipbox">
          <details class="owner-collapsible" ${isInitial ? "" : "open"}>
            <summary class="owner-summary">
              <span class="owner-chips"></span>
              <span class="owner-caret">▾</span>
            </summary>
            <div class="owner-list"></div>
          </details>
        </div>

        <button class="applyOwnerFilterBtn"><i class="fas fa-filter"></i> Apply</button>
        <button class="exportCSV"${isInitial ? " disabled" : ""}><i class="fas fa-download"></i> Export CSV</button>
      </div>

      <div class="prediction-notes">
        <p><strong>🔹 Sorting:</strong> Tests are sorted by descending confidence score.</p>
        <p><strong>🔹 Tip:</strong> Choose <em>All</em> or one/more owners, then click <em>Apply</em>.</p>
        <p><strong>🔹 Test Names:</strong> Click to open the corresponding ARM report.</p>
        <p><strong>🔹 Predicted Work Item IDs:</strong> Click to open the TFS bug page.</p>
      </div>

      ${
        isInitial
          ? `<div class="placeholder" style="padding:10px 12px; border-radius:8px; background:#f6f7fb; color:#4a4f63; margin:4px 0 12px;">
                <strong>👉 Please select “All” or choose one/more owners</strong>, then click <em>Apply</em> to load results.
             </div>`
          : (predictedTests.length
              ? `
                <h5>✅ Predicted Tests</h5>
                <div style="max-height:200px; overflow:auto;">
                  <table class="prediction-table predictionResultTable predictedTable">
                    <thead><tr><th>Test Name</th><th>Owner</th><th>Predicted Work Item IDs</th></tr></thead>
                    <tbody>${createTableRows(predictedTests)}</tbody>
                  </table>
                </div>`
              : `<p>No predicted tests available.</p>`
            )
      }

      ${
        !isInitial
          ? (unpredictedTests.length
              ? `
                <h5>⚠ Unpredicted Tests</h5>
                <div style="max-height:200px; overflow:auto;">
                  <table class="prediction-table predictionResultTable unpredictedTable">
                    <thead><tr><th>Test Name</th><th>Owner</th><th>Status</th></tr></thead>
                    <tbody>${createTableRows(unpredictedTests)}</tbody>
                  </table>
                </div>`
              : `<p>No unpredicted tests available.</p>`
            )
          : ``
      }

      <button class="startInvestigationBtn" style="margin-top:10px;">
        <i class="fas fa-redo"></i> Start Test Failure Investigation
      </button>
    `;
    chatBody.appendChild(botMsg);
    chatBody.scrollTop = chatBody.scrollHeight;

    // ==== Build the collapsible checklist + chips ====
    const listHost  = botMsg.querySelector(".owner-list");
    const chipsHost = botMsg.querySelector(".owner-chips");
    const applyBtn  = botMsg.querySelector(".applyOwnerFilterBtn");
    const exportBtn = botMsg.querySelector(".exportCSV");

    const ownerEntries = Object.entries(ownerTestMap).sort((a,b)=>a[0].localeCompare(b[0]));
    const checklistHTML = `
      <label class="owner-item">
        <input type="checkbox" value="__all__" class="owner-checkbox">
        <span class="owner-label"><strong>All</strong> (${totalUniqueCount})</span>
      </label>
      <div class="owner-divider"></div>
      ${ownerEntries.map(([owner, tests]) => `
        <label class="owner-item">
          <input type="checkbox" value="${owner}" class="owner-checkbox">
          <span class="owner-label">${owner} (${tests.size})</span>
        </label>
      `).join("")}
    `;
    listHost.innerHTML = checklistHTML;

    // Hydrate from ownerFilter
    (function hydrateSelectionFromParam() {
      const boxes = listHost.querySelectorAll(".owner-checkbox");
      if (isInitial) return;
      if (ownerFilter === "__all__") {
        boxes.forEach(b => b.checked = (b.value === "__all__"));
        return;
      }
      if (Array.isArray(ownerFilter)) {
        const set = new Set(ownerFilter.map(o => norm(o)));
        boxes.forEach(b => { b.checked = set.has(norm(b.value)); });
      } else {
        boxes.forEach(b => { b.checked = (norm(b.value) === norm(ownerFilter)); });
      }
    })();

    // Selected values
    function getSelectedValues() {
      return Array.from(listHost.querySelectorAll(".owner-checkbox:checked")).map(b => b.value);
    }

    // Chips render
    function renderChips() {
      const vals = getSelectedValues();
      if (vals.length === 0 || vals.includes("__all__")) {
        chipsHost.innerHTML = `<span class="chip chip-all">All owners</span>`;
        return;
      }
      chipsHost.innerHTML = vals.slice(0, 6).map(v => `<span class="chip">${v}</span>`).join("")
        + (vals.length > 6 ? `<span class="chip chip-more">+${vals.length-6}</span>` : "");
    }

    // Select-all exclusivity
    listHost.addEventListener("change", (e) => {
      const t = e.target;
      if (!(t instanceof HTMLInputElement) || t.className !== "owner-checkbox") return;

      if (t.value === "__all__") {
        if (t.checked) {
          listHost.querySelectorAll('.owner-checkbox:not([value="__all__"])').forEach(b => b.checked = false);
        }
      } else if (t.checked) {
        const allBox = listHost.querySelector('.owner-checkbox[value="__all__"]');
        if (allBox) allBox.checked = false;
      }
      renderChips();
    });

    // Initial chips
    renderChips();

    // === Buttons ===
    applyBtn.addEventListener("click", () => {
      const selected = getSelectedValues();
      if (selected.length === 0) {
        displayPredictionResults(predictions, "__choose__"); // placeholder state
        return;
      }
      if (selected.includes("__all__")) {
        displayPredictionResults(predictions, "__all__");
      } else {
        displayPredictionResults(predictions, selected); // array of owners
      }
    });

    exportBtn.addEventListener("click", () => {
      if (exportBtn.disabled) return;
      const table = botMsg.querySelector(".predictedTable") || botMsg.querySelector(".predictionResultTable");
      if (!table) {
        alert("No table to export. Select owners and click Apply first.");
        return;
      }
      exportTableToCSV(table, "prediction_results.csv");
    });

    botMsg.querySelector(".startInvestigationBtn").addEventListener("click", showCDCARMJsonOptions);
}


function exportTableToCSV(tableOrSelector, filename = "prediction_results.csv") {
  // Resolve table element
  const table = (typeof tableOrSelector === "string")
    ? document.querySelector(tableOrSelector)
    : tableOrSelector;

  if (!table) {
    console.warn("exportTableToCSV: table not found.", tableOrSelector);
    return;
  }

  // Collect rows from this table only
  const rows = Array.from(table.querySelectorAll("tr"));
  if (!rows.length) {
    console.warn("exportTableToCSV: no rows to export.");
    return;
  }

  // Build CSV
  const csv = rows.map(row => {
    const cols = Array.from(row.querySelectorAll("th, td"));
    return cols.map(col => {
      // text content with quotes escaped
      return `"${col.textContent.trim().replace(/"/g, '""')}"`;
    }).join(",");
  }).join("\n");

  // Blob + download (with BOM so Excel opens UTF-8)
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
  const url  = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.style.display = "none";
  document.body.appendChild(link);

  // Safari compatibility: programmatic click event
  link.dispatchEvent(new MouseEvent("click"));
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}




function tryFetchData(products, releases, platforms, minFailingBuilds, owner, progressBar, progressMessage) {
    console.log('Calling Flask backend at /fetch_cdcarm with:', { products, releases, platforms, minFailingBuilds, owner });

    progressBar.style.width = '30%';

    fetch("fetch_cdcarm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            products,
            releases,
            platforms,
            min_failing_builds: minFailingBuilds,
            owner
        })
    })
        .then(response => {
            if (!response.ok) throw new Error("Network response was not OK");
            return response.json();
        })
        .then(data => {
            progressBar.style.width = '100%';
            console.log('Received data:', data);

            setTimeout(() => {
                chatBody.removeChild(progressMessage);

                const recordCount = data.record_count || 0;
                const content = data.content || "";
                const filename = data.filename || "cdcarm_data.json";

                const downloadMessage = createBotMessage();
                downloadMessage.innerHTML = `
                <div class="download-container">
                    <p>✅ Successfully fetched ${recordCount} records.</p>
                    <button class="download-btn" id="downloadJsonBtn">
                        <i class="fas fa-download"></i> Download JSON File
                    </button>
                    <button class="back-to-menu" id="startInvestigationBtn">
                        <i class="fas fa-redo"></i> Start Test Failure Investigation
                    </button>

                </div>
            `;
                chatBody.appendChild(downloadMessage);
                chatBody.scrollTop = chatBody.scrollHeight;

                document.getElementById('downloadJsonBtn').addEventListener('click', () => {
                    let jsonData;
                    try {
                        jsonData = atob(content);
                    } catch (e) {
                        jsonData = content;
                    }

                    const blob = new Blob([jsonData], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                });

                document.getElementById('startInvestigationBtn').addEventListener('click', showCDCARMJsonOptions);

            }, 500);
        })
        .catch(error => {
            console.error('Fetch failed, using dummy data fallback:', error);
            progressBar.style.width = '100%';
            setTimeout(() => {
                chatBody.removeChild(progressMessage);
                replyWithBotMessage(`⚠️ Error fetching from server: ${error.message}`);
                createDummyData(products, releases, platforms, minFailingBuilds, owner);
            }, 500);
        });
}

function createDummyData(products, releases, platforms, minFailingBuilds, owner) {
    const dummyData = [];
    for (let i = 1; i <= 5; i++) {
        dummyData.push({
            "Product": products.split(',')[0],
            "Release": releases.split(',')[0],
            "Platform": platforms.split(',')[0],
            "TestName": `DemoTest_${i}`,
            "TestId": i,
            "Result": "FAIL",
            "FailureMessage": `Demo failure message ${i}. This is NOT real data.`,
            "Owner": owner !== "all" ? owner : `user${i}`,
            "HasInvestigation": i % 2 === 0,
            "FailureCount": parseInt(minFailingBuilds) + i
        });
    }

    const jsonString = JSON.stringify(dummyData, null, 2);

    const downloadMessage = createBotMessage();
    downloadMessage.innerHTML = `
        <div class="download-container">
            <p>Demo data created (${dummyData.length} records).</p>
            <button class="download-btn" id="downloadDemoBtn">
                <i class="fas fa-download"></i> Download Demo JSON
            </button>
            <button class="back-to-menu" id="backToMenuDemo">
                <i class="fas fa-home"></i> Home
            </button>
        </div>
    `;
    chatBody.appendChild(downloadMessage);
    chatBody.scrollTop = chatBody.scrollHeight;

    document.getElementById('downloadDemoBtn').addEventListener('click', () => {
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'demo_data.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    document.getElementById('backToMenuDemo').addEventListener('click', showMainMenu);
}

function cleanupDuplicateButtons() {
    // Dummy no-op to suppress error
}