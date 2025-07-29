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

expandBtn.addEventListener('click', () => {
    isExpanded = !isExpanded;
    chatWindow.classList.toggle('expanded');
    expandBtn.innerHTML = isExpanded
        ? '<i class="fas fa-compress"></i>'
        : '<i class="fas fa-expand"></i>';
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



function fetchCDCARMJson() {
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
function displayPredictionResults(predictions, ownerFilter = "") {
    if (!predictions.length) {
        const botMsg = createBotMessage();
        botMsg.innerHTML = `<p>No matching tests found for the selected owner.</p>`;
        chatBody.appendChild(botMsg);
        chatBody.scrollTop = chatBody.scrollHeight;
        return;
    }

    console.log("Raw predictions received:", predictions);

    // Separate predicted and unpredicted tests
    const predictedTests = predictions.filter(p => p.IsPredicted === "Yes");
    const unpredictedTests = predictions.filter(p => p.IsPredicted !== "Yes");

    allPredictions = predictions;

    // Build unique owner list (including both predicted and unpredicted)
    const ownerTestMap = {};
    predictions.forEach(p => {
        const owner = (p.Owner || "Unknown").trim();
        if (!ownerTestMap[owner]) ownerTestMap[owner] = new Set();
        ownerTestMap[owner].add(p.TestName);
    });

    const totalCount = Object.values(ownerTestMap).reduce((acc, set) => acc + set.size, 0);

    const ownerOptions = [
        `<option value="__all__"${!ownerFilter || ownerFilter === "__all__" ? " selected" : ""}>All (${totalCount})</option>`
    ].concat(
        Object.entries(ownerTestMap).map(([owner, tests]) =>
            `<option value="${owner}" ${owner.toLowerCase() === ownerFilter.toLowerCase() ? 'selected' : ''}>
                ${owner} (${tests.size})
            </option>`
        )
    ).join('');

    // Apply owner filter if selected
    let filteredPredicted = [...predictedTests];
    let filteredUnpredicted = [...unpredictedTests];
    if (ownerFilter && ownerFilter !== "__all__") {
        filteredPredicted = filteredPredicted.filter(p => (p.Owner || "").trim().toLowerCase() === ownerFilter.toLowerCase());
        filteredUnpredicted = filteredUnpredicted.filter(p => (p.Owner || "").trim().toLowerCase() === ownerFilter.toLowerCase());
    }

    // Sort predicted by confidence score
    filteredPredicted.sort((a, b) => (b.ConfidenceScore || 0) - (a.ConfidenceScore || 0));

    const createTableRows = (tests) => {
        const grouped = {};
        tests.forEach(p => {
            const test = p.TestName || "Unnamed Test";
            if (!grouped[test]) {
                grouped[test] = {
                    Owner: p.Owner || "Unknown",
                    Product: p.Product,
                    Release: p.Release,
                    Platform: p.Platform,
                    WorkItems: new Set(),
                    IsPredicted: p.IsPredicted === "Yes"
                };
            }
            if (p.PredictedWorkItemId && p.PredictedWorkItemId !== "-") {
                p.PredictedWorkItemId.split(";").forEach(wi => grouped[test].WorkItems.add(wi.trim()));
            }
        });
        return Object.entries(grouped).map(([testName, info]) => `
            <tr>
                <td><a href="${buildTestLink(testName, info.Product, info.Release, info.Platform)}" target="_blank">${testName}</a></td>
                <td>${info.Owner}</td>
                <td>${info.IsPredicted && info.WorkItems.size > 0
                    ? [...info.WorkItems].map(wi =>
                        `<a href="https://tfs.ansys.com:8443/tfs/ANSYS_Development/Portfolio/_workitems/edit/${wi}" target="_blank">${wi}</a>`
                      ).join(", ")
                    : "No Prediction"}</td>
            </tr>
        `).join('');
    };

    // Clear previous block
    chatBody.querySelector('.prediction-results-container')?.remove();

    const botMsg = createBotMessage();
    botMsg.classList.add('prediction-results-container');
    botMsg.innerHTML = `
      <h4>🔎 Test Failure Results:</h4>
      <div class="prediction-controls">
        <label for="ownerFilterSelect">Owner Filter:</label>
        <select class="option-input ownerFilterSelect">${ownerOptions}</select>
        <button class="applyOwnerFilterBtn"><i class="fas fa-filter"></i> Apply</button>
        <button class="exportCSV"><i class="fas fa-download"></i> Export CSV</button>
      </div>
      <div class="prediction-notes">
        <p><strong>🔹 Sorting:</strong> Tests are sorted by descending confidence score.</p>
        <p><strong>🔹 Test Names:</strong> Clicking a test name will open the corresponding ARM report.</p>
        <p><strong>🔹 Predicted Work Item IDs:</strong> Clicking an ID will open the TFS bug page for that work item.</p>
      </div>
      ${filteredPredicted.length ? `
      <h5>✅ Predicted Tests</h5>
      <div style="max-height:200px; overflow:auto;">
        <table class="prediction-table predictionResultTable">
          <thead><tr><th>Test Name</th><th>Owner</th><th>Predicted Work Item IDs</th></tr></thead>
          <tbody>${createTableRows(filteredPredicted)}</tbody>
        </table>
      </div>` : `<p>No predicted tests available.</p>`}
      ${filteredUnpredicted.length ? `
      <h5>⚠ Unpredicted Tests</h5>
      <div style="max-height:200px; overflow:auto;">
        <table class="prediction-table predictionResultTable">
          <thead><tr><th>Test Name</th><th>Owner</th><th>Status</th></tr></thead>
          <tbody>${createTableRows(filteredUnpredicted)}</tbody>
        </table>
      </div>` : `<p>No unpredicted tests available.</p>`}
      <button class="applyOwnerFilterBtn startInvestigationBtn" style="margin-top:10px;">
       <i class="fas fa-redo"></i> Start Test Failure Investigation
      </button>
    `;
    chatBody.appendChild(botMsg);
    chatBody.scrollTop = chatBody.scrollHeight;

    botMsg.querySelector('.applyOwnerFilterBtn').addEventListener('click', () => {
        const owner = botMsg.querySelector('.ownerFilterSelect').value.trim();
        displayPredictionResults(predictions, owner);
    });

    botMsg.querySelector('.exportCSV').addEventListener('click', () => {
        exportTableToCSV(botMsg.querySelector('.predictionResultTable'));
    });

    botMsg.querySelector('.startInvestigationBtn').addEventListener('click', showCDCARMJsonOptions);
}


function exportTableToCSV(tableSelector, filename = "prediction_results.csv") {
    const rows = document.querySelectorAll(`${tableSelector} tr`);
    let csv = [];

    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(col => {
            rowData.push(`"${col.textContent.trim().replace(/"/g, '""')}"`);
        });
        csv.push(rowData.join(","));
    });

    const csvString = csv.join("\n");
    const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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