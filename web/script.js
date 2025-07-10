// Ensure chat starts closed, then auto-popup
document.addEventListener('DOMContentLoaded', function() {
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

// FIXED: Clear everything and show welcome message only once
function clearAndShowWelcome() {
    // Clear all content first
    chatBody.innerHTML = '';
    optionPanel.innerHTML = '';
    optionPanel.style.display = 'none';
    chatFooter.style.display = 'none';
    
    // Show chat body
    chatBody.style.display = 'block';
    
    // Create welcome message
    const welcomeMessage = createBotMessage();
    welcomeMessage.innerHTML = `
        <div class="welcome-message">
            <p>👋 Welcome to Test Failure Analyzer! How can I help you today?</p>
            <p>You can select an option below or type your question here.</p>
            <p><strong>Here are quick suggestions to get you started:</strong></p>
        </div>
    `;
    chatBody.appendChild(welcomeMessage);
    chatBody.scrollTop = chatBody.scrollHeight;
    
    // Wait a bit, then show buttons
    setTimeout(() => {
        showWelcomeButtons();
    }, 500);
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
                <span>Fetch ARM Error Reports </span>
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
            <button class="back-to-menu" id="backToMenuJson">
                <i class="fas fa-home"></i> Home
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
    
    document.getElementById('backToMenuJson').addEventListener('click', showMainMenu);
}

async function populateDynamicDatalists() {
    try {
        // Fetch Products
        const productRes = await fetch("http://localhost:5000/api/products");
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
        const releaseRes = await fetch("http://localhost:5000/api/releases");
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
        const platformRes = await fetch("http://localhost:5000/api/platforms");
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

    showTypingIndicator().then(() => {
        const message = createBotMessage();
        message.innerHTML = `
            <p>Let's fetch ARM Error report data for investigation. Please provide the following information:</p>
            <div class="cdcarm-json-options active">
                <div class="option-group">
                    <label class="option-label">Products:</label>
                    <input type="text" class="option-input" id="productsInput" list="productsList" placeholder="DISCO" value="DISCO">
                </div>
                
                <div class="option-group">
                    <label class="option-label">Releases:</label>
                    <input type="text" class="option-input" id="releasesInput" list="releasesList" placeholder="25.2" value="25.2">
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
        // //<div class="option-group">
        //             <label class="option-label">Owner (Case Sensitive):</label>
        //             <input type="text" class="option-input" id="ownerJsonInput" list="ownersList" placeholder="all" value="all">
        //         </div>
        chatBody.appendChild(message);
        chatBody.scrollTop = chatBody.scrollHeight;

        document.getElementById('fetchJsonBtn').addEventListener('click', fetchCDCARMJson);
        console.log("✅ Dynamic input fields with global datalists loaded.");
        cleanupDuplicateButtons();
    });
}

function fetchCDCARMJson() {
    const products = document.getElementById('productsInput').value.trim() || "DISCO";
    const releases = document.getElementById('releasesInput').value.trim() || "25.2";
    const platforms = document.getElementById('platformsInput').value.trim() || "Windows";
    const minFailingBuilds = document.getElementById('minFailingInput').value.trim() || "2";
    const ownerFilter = document.getElementById('ownerJsonInput').value.trim() || "all";

    const userMsg = createUserMessage(`Running prediction for Products: ${products}, Releases: ${releases}, Platforms: ${platforms}, Min Failing Builds: ${minFailingBuilds}`);//Owner Filter: ${ownerFilter}
    chatBody.appendChild(userMsg);
    chatBody.scrollTop = chatBody.scrollHeight;

    const progressMessage = createBotMessage();
    progressMessage.innerHTML = `
        <p>Fetching and analyzing data...</p>
        <div class="progress-container"><div class="progress-bar" id="jsonProgressBar"></div></div>
    `;
    chatBody.appendChild(progressMessage);
    const progressBar = document.getElementById('jsonProgressBar');
    progressBar.style.width = '30%';

    fetch("http://localhost:5000/fetch_cdcarm", {
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
        if (data.data_type === "prediction_table") {
            // filter on owner if required
            let filtered = data.merged_summary;
            if (ownerFilter !== "all") {
                filtered = filtered.filter(x => x.Owner.toLowerCase() === ownerFilter.toLowerCase());
            }
            displayPredictionResults(filtered);
            chatBody.removeChild(progressMessage);
        } else {
            throw new Error("Unexpected response type");
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
        releaseName = input ? input.value.trim() : "25.2";
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

function displayPredictionResults(predictions, ownerFilter = "") {
    if (!predictions.length) {
        const botMsg = createBotMessage();
        botMsg.innerHTML = `<p>No matching tests found for the selected owner.</p>`;
        chatBody.appendChild(botMsg);
        chatBody.scrollTop = chatBody.scrollHeight;
        return;
    }

    if (!allPredictions.length) allPredictions = predictions;

    const owners = [...new Set(allPredictions.map(p => p.Owner))];
    const ownerOptions = owners.map(owner => 
        `<option value="${owner}" ${owner.toLowerCase() === ownerFilter.toLowerCase() ? 'selected' : ''}>${owner}</option>`
    ).join('');

    const filtered = ownerFilter
        ? predictions.filter(p => p.Owner.trim().toLowerCase() === ownerFilter.toLowerCase())
        : predictions;

    // group by TestName
    const grouped = {};
    filtered.forEach(p => {
        const test = p.TestName;
        if (!grouped[test]) {
            grouped[test] = {
                Owner: p.Owner,
                Product: p.Product,
                WorkItems: new Set()
            };
        }
        if (p.PredictedWorkItemId && p.PredictedWorkItemId !== "-") {
            p.PredictedWorkItemId.split(";").forEach(wi => grouped[test].WorkItems.add(wi.trim()));
        }
    });

    const botMsg = createBotMessage();
    botMsg.innerHTML = `
      <h4>🔎 Prediction Results:</h4>
      <div class="owner-filter-container" style="margin-bottom:10px;">
        <label for="ownerFilterSelect"><strong>Owner Filter:</strong></label>
        <select id="ownerFilterSelect" class="option-input" style="width:200px;">
            <option value="">All</option>
            ${ownerOptions}
        </select>
        <button id="applyOwnerFilterBtn" class="fetch-json-btn">
            <i class="fas fa-filter"></i> Apply
        </button>
        <button id="exportCSV" class="fetch-json-btn" style="margin-left:10px;">
            <i class="fas fa-download"></i> Export CSV
        </button>
      </div>
      <div style="max-height:300px; overflow:auto;">
        <table class="prediction-table" id="predictionResultTable">
          <thead>
            <tr>
              <th>Test Name</th>
              <th>Owner</th>
              <th>Predicted Work Item IDs</th>
            </tr>
          </thead>
          <tbody>
            ${Object.entries(grouped).map(([testName, info]) => `
              <tr>
                <td>
                  <a href="${buildTestLink(testName, info.Product)}" target="_blank">${testName}</a>
                </td>
                <td>${info.Owner}</td>
                <td>
                  ${[...info.WorkItems].map(wi => 
                    `<a href="https://tfs.ansys.com:8443/tfs/ANSYS_Development/Portfolio/_workitems/edit/${wi}" target="_blank">${wi}</a>`
                  ).join(", ") || "-"}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
      <button class="back-to-menu" id="backToMenuPred" style="margin-top:10px;">
  <i class="fas fa-home"></i><span style="margin-left: 6px;">Home</span>
</button>
    `;
    chatBody.appendChild(botMsg);
    chatBody.scrollTop = chatBody.scrollHeight;

    document.getElementById('applyOwnerFilterBtn').addEventListener('click', () => {
        const owner = document.getElementById('ownerFilterSelect').value.trim();
        chatBody.removeChild(botMsg);
        displayPredictionResults(allPredictions, owner);
    });

    document.getElementById('exportCSV').addEventListener('click', () => {
        exportTableToCSV("#predictionResultTable");
    });

    document.getElementById('backToMenuPred').addEventListener('click', () => {
        allPredictions = [];
        showMainMenu();
    });
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

    fetch("http://localhost:5000/fetch_cdcarm", {
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
                    <button class="back-to-menu" id="backToMenuJson">
                        <i class="fas fa-home"></i> Home
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

            document.getElementById('backToMenuJson').addEventListener('click', showMainMenu);
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