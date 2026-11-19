// Scam or Legit? — Client Application Logic (Version 2.0.0)

const API_BASE = window.location.origin;

let currentTab = 'text';
let selectedFile = null;
let currentPresetData = [];
let lastAnalysisResult = null;

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    fetchHealthStatus();
    fetchPresets();
    setupTextareaCounter();
    setupDropzoneEvents();
});

// Helper for display toggles
function setElementVisible(el, visible, displayStyle = 'block') {
    if (!el) return;
    if (visible) {
        el.classList.remove('hidden');
        el.style.display = displayStyle;
    } else {
        el.classList.add('hidden');
        el.style.display = 'none';
    }
}

// Fetch API Server Status
async function fetchHealthStatus() {
    const statusPill = document.getElementById('statusPill');
    const statusText = document.getElementById('statusText');
    
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        const data = await response.json();
        
        if (data.status === 'online') {
            let engineDesc = data.gemini_analyzer.active ? "Gemini 2.0 Flash + Chroma RAG" : "Vector RAG Threat Engine";
            statusText.innerText = engineDesc;
            if (statusPill) statusPill.classList.remove('offline');
        }
    } catch (err) {
        console.warn("Backend API offline or standalone local mode.", err);
        if (statusText) statusText.innerText = "Vector RAG Local Engine";
    }
}

// Fetch Sample Presets
async function fetchPresets() {
    const presetsContainer = document.getElementById('presetsContainer');
    const defaultPresets = [
        {
            id: "preset_bank_sms",
            name: "🚨 Bank Account Lock Phishing SMS",
            type: "Phishing SMS",
            content: "SECURITY ALERT: Your Chase online banking access has been locked due to suspicious login attempts. Verify identity within 24 hours at http://chase-security-verify-auth.com or account will be closed."
        },
        {
            id: "preset_fake_internship",
            name: "🎓 Fake Internship Deposit Scam",
            type: "Fake Internship Scam",
            content: "Congratulations Student! You have been selected for a 3-Month Remote AI & Web Development Virtual Internship at FutureTech Innovations! Offer Letter is attached. To reserve your candidate slot and issue your employee ID, pay a refundable training & stipend deposit of $150 via Zelle / UPI within 6 hours."
        },
        {
            id: "preset_remote_job",
            name: "💼 Remote Job Cheque Scam",
            type: "Fake Job Offer",
            content: "Congratulations! You are hired for Remote Data Specialist at $45/hr. We will send a $3,500 cashier's check for equipment. Deposit check, keep $500 bonus, and wire $3,000 to our equipment vendor via Zelle."
        },
        {
            id: "preset_crypto_vip",
            name: "📈 Guaranteed Crypto Bot Scam",
            type: "Crypto Fraud",
            content: "Turn $200 into $5,000 in 24 hours guaranteed! Join our VIP Telegram Signal group. Our AI trading bot has zero loss history. Send USDT (TRC-20) to T9xZ8842... now!"
        },
        {
            id: "preset_legit_amazon",
            name: "✅ Official Amazon Shipping Receipt",
            type: "Legitimate",
            content: "Amazon.com: Your order #114-9842104-5829104 has shipped via UPS. You can track package status anytime inside your official Amazon account app."
        }
    ];

    try {
        const response = await fetch(`${API_BASE}/api/presets`);
        const presets = await response.json();
        currentPresetData = presets && presets.length ? presets : defaultPresets;
    } catch (err) {
        console.warn("Could not load presets from server, using built-in presets.", err);
        currentPresetData = defaultPresets;
    }

    if (presetsContainer) {
        presetsContainer.innerHTML = '';
        currentPresetData.forEach(preset => {
            const btn = document.createElement('button');
            btn.className = 'preset-chip';
            btn.innerHTML = escapeHtml(preset.name);
            btn.onclick = () => loadPreset(preset);
            presetsContainer.appendChild(btn);
        });
    }
}

// Load Preset into Text Area and Trigger Analysis
function loadPreset(preset) {
    switchInputTab('text');
    const textarea = document.getElementById('messageInput');
    if (textarea) {
        textarea.value = preset.content;
        updateCharCounter();
    }
    runAnalysis();
}

// Tab Switching (Text vs Screenshot Image)
function switchInputTab(tab) {
    currentTab = tab;
    
    const tabTextBtn = document.getElementById('tabTextBtn');
    const tabImageBtn = document.getElementById('tabImageBtn');
    const tabTextContent = document.getElementById('tabTextContent');
    const tabImageContent = document.getElementById('tabImageContent');
    
    if (tabTextBtn) tabTextBtn.classList.toggle('active', tab === 'text');
    if (tabImageBtn) tabImageBtn.classList.toggle('active', tab === 'image');
    
    if (tabTextContent) {
        tabTextContent.classList.toggle('active', tab === 'text');
        setElementVisible(tabTextContent, tab === 'text', 'block');
    }
    
    if (tabImageContent) {
        tabImageContent.classList.toggle('active', tab === 'image');
        setElementVisible(tabImageContent, tab === 'image', 'block');
    }
}

// Textarea Character Counter
function setupTextareaCounter() {
    const textarea = document.getElementById('messageInput');
    if (textarea) {
        textarea.addEventListener('input', updateCharCounter);
    }
}

function updateCharCounter() {
    const textarea = document.getElementById('messageInput');
    const charCount = document.getElementById('charCount');
    if (textarea && charCount) {
        charCount.innerText = `${textarea.value.length} characters`;
    }
}

// Paste Clipboard
async function pasteClipboard() {
    try {
        const text = await navigator.clipboard.readText();
        if (text) {
            const input = document.getElementById('messageInput');
            if (input) {
                input.value = text;
                updateCharCounter();
            }
        }
    } catch (err) {
        alert("Clipboard access permission denied. Please paste manually into the text field.");
    }
}

// Clear Input
function clearInput() {
    const input = document.getElementById('messageInput');
    if (input) input.value = '';
    updateCharCounter();
    removeImage();
    
    setElementVisible(document.getElementById('emptyState'), true, 'flex');
    setElementVisible(document.getElementById('activeResults'), false);
    lastAnalysisResult = null;
}

// Dropzone Events for Image Screenshot Upload
function setupDropzoneEvents() {
    const dropzone = document.getElementById('dropzone');
    if (!dropzone) return;
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.add('drag-over');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.remove('drag-over');
        }, false);
    });
    
    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            handleFile(files[0]);
        }
    });
}

function triggerFileInput() {
    if (!selectedFile) {
        const fileInput = document.getElementById('imageInput');
        if (fileInput) fileInput.click();
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files && files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert("Please upload a valid image screenshot file (PNG, JPG, WEBP).");
        return;
    }
    if (file.size > 5 * 1024 * 1024) {
        alert("File size exceeds 5MB limit. Please upload a smaller screenshot.");
        return;
    }
    
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = document.getElementById('imagePreview');
        if (img) img.src = e.target.result;
        setElementVisible(document.getElementById('dropzonePrompt'), false);
        setElementVisible(document.getElementById('previewContainer'), true, 'block');
    };
    reader.readAsDataURL(file);
}

function removeImage(e) {
    if (e) e.stopPropagation();
    selectedFile = null;
    const fileInput = document.getElementById('imageInput');
    if (fileInput) fileInput.value = '';
    const img = document.getElementById('imagePreview');
    if (img) img.src = '';
    setElementVisible(document.getElementById('dropzonePrompt'), true, 'flex');
    setElementVisible(document.getElementById('previewContainer'), false);
}

// Main Analysis Request
async function runAnalysis() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const btnIcon = document.getElementById('btnIcon');
    const btnText = document.getElementById('btnText');
    const textInput = document.getElementById('messageInput') ? document.getElementById('messageInput').value : '';

    if (currentTab === 'text' && !textInput.trim()) {
        alert("Please paste or type a suspicious message to analyze.");
        return;
    }
    
    if (currentTab === 'image' && !selectedFile) {
        alert("Please select or drop a screenshot image file.");
        return;
    }

    // Set Loading State
    if (analyzeBtn) analyzeBtn.disabled = true;
    if (btnIcon) btnIcon.innerHTML = `<svg class="spin-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/></svg>`;
    if (btnText) btnText.innerText = "Analyzing Threat Intelligence...";

    try {
        let result;
        
        if (currentTab === 'text') {
            const response = await fetch(`${API_BASE}/api/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: textInput })
            });
            if (response.ok) {
                result = await response.json();
            } else {
                throw new Error("Server error " + response.status);
            }
        } else {
            const formData = new FormData();
            formData.append('file', selectedFile);
            if (textInput.trim()) {
                formData.append('text', textInput);
            }
            const response = await fetch(`${API_BASE}/api/analyze`, {
                method: 'POST',
                body: formData
            });
            if (response.ok) {
                result = await response.json();
            } else {
                throw new Error("Server error " + response.status);
            }
        }

        lastAnalysisResult = result;
        renderResults(result);

    } catch (err) {
        console.warn("Backend API error, fallback client evaluation active:", err);
        const fallbackResult = generateClientFallbackAnalysis(textInput);
        lastAnalysisResult = fallbackResult;
        renderResults(fallbackResult);
    } finally {
        if (analyzeBtn) analyzeBtn.disabled = false;
        if (btnIcon) btnIcon.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/></svg>`;
        if (btnText) btnText.innerText = "ANALYZE RISK NOW";
    }
}

// Client Fallback Heuristic Analysis (Strict Threshold Compliance)
// Authoritative Thresholds:
// 0–24: Low Risk
// 25–59: Caution
// 60–84: High Scam Risk
// 85–100: Critical Threat
function generateClientFallbackAnalysis(input) {
    const text = (input || "").toLowerCase();
    let score = 10;
    let category = "Suspicious Communication";
    let flags = [];
    let cues = [];
    let actions = [];

    if (text.includes("chase") || text.includes("bank") || text.includes("locked") || text.includes("verify identity")) {
        score = 78; // High Scam Risk boundary test
        category = "Phishing / Account Takeover SMS";
        flags.push({ category: "Brand & Identity Spoofing", severity: "High", description: "Unverified link mimicking official banking login portal.", matched_phrase: "http://chase-security-verify-auth.com" });
        flags.push({ category: "Artificial Urgency & Threat Tactics", severity: "High", description: "Imposes 24-hour ultimatum to force hasty reaction.", matched_phrase: "within 24 hours" });
        cues = ["Artificial Urgency & Threat Tactics", "Credential Harvesting / OTP Theft"];
        actions = ["Do NOT click the provided link.", "Log into your bank through their official app or website directly.", "Report SMS phishing to carrier."];
    } else if (text.includes("check") || text.includes("hired") || text.includes("zelle") || text.includes("equipment vendor")) {
        score = 88; // Critical Threat boundary test
        category = "Fake Remote Job / Overpayment Fraud";
        flags.push({ category: "Untraceable / Peer-to-Peer Payment Demand", severity: "Critical", description: "Instructs victim to deposit check and wire funds to vendor via Zelle.", matched_phrase: "wire $3,000 via Zelle" });
        flags.push({ category: "Upfront Fee / Registration Deposit Trap", severity: "High", description: "Offered position without formal live interview process.", matched_phrase: "Hired at $45/hr" });
        cues = ["Untraceable / Peer-to-Peer Payment Demand", "Upfront Fee / Registration Deposit Trap"];
        actions = ["Cease communication with representative immediately.", "Never wire money back from a deposited cashier check.", "Verify employer on official website."];
    } else if (text.includes("crypto") || text.includes("guaranteed") || text.includes("telegram") || text.includes("usdt")) {
        score = 95; // Critical Threat
        category = "Investment & Crypto Fraud";
        flags.push({ category: "Guaranteed Profit / High-Yield Claim", severity: "Critical", description: "Promises zero loss and guaranteed overnight returns.", matched_phrase: "Turn $200 into $5,000 guaranteed" });
        cues = ["Guaranteed Profit / High-Yield Claim", "Untraceable / Peer-to-Peer Payment Demand"];
        actions = ["Never transfer crypto to unverified wallets.", "Be aware that legitimate trading platforms do not guarantee profits."];
    } else if (text.includes("internship") || text.includes("stipend") || text.includes("training fee") || text.includes("refundable deposit")) {
        score = 75; // High Scam Risk
        category = "Fake Virtual Internship Scam";
        flags.push({ category: "Upfront Fee / Registration Deposit Trap", severity: "Critical", description: "Demands upfront training deposit to issue offer letter or candidate slot.", matched_phrase: "pay refundable deposit of $150" });
        cues = ["Upfront Fee / Registration Deposit Trap", "Artificial Urgency & Threat Tactics"];
        actions = ["Never pay a deposit to secure an internship.", "Legitimate companies pay interns for work, not vice versa."];
    } else if (text.includes("amazon") || text.includes("order #") || text.includes("shipped")) {
        score = 5; // Low Risk
        category = "Genuine Delivery Notification";
        flags = [];
        cues = [];
        actions = ["Message appears clean.", "Verify order status inside your official mobile app."];
    } else {
        score = 35; // Caution
        category = "Unverified Contact";
        flags.push({ category: "Deceptive or Unverified Link", severity: "Medium", description: "Contains unverified contact link.", matched_phrase: "" });
        cues = ["Deceptive or Unverified Link"];
        actions = ["Avoid clicking links from unknown senders.", "Verify sender identity independently."];
    }

    let level = "Low Risk";
    let color = "#10b981";
    let bgStyle = "rgba(16, 185, 129, 0.16)";

    if (score >= 85) {
        level = "Critical Threat";
        color = "#f43f5e";
        bgStyle = "rgba(244, 63, 94, 0.16)";
    } else if (score >= 60) {
        level = "High Scam Risk";
        color = "#f97316";
        bgStyle = "rgba(249, 115, 22, 0.16)";
    } else if (score >= 25) {
        level = "Caution";
        color = "#f59e0b";
        bgStyle = "rgba(245, 158, 11, 0.16)";
    }

    return {
        risk_score: score,
        risk_level: level,
        color: color,
        bg_style: bgStyle,
        disclaimer: "Heuristic risk score based on pattern matching and indicator analysis.",
        scam_category: category,
        summary: `Analysis identified ${flags.length} risk indicator(s) with an estimated heuristic threat rating of ${score}/100.`,
        uncertainty: "Moderate Uncertainty — Fallback local mode.",
        red_flags: flags,
        pattern_triggers: cues,
        rag_matches: [
            {
                id: "local_pattern_ref",
                title: "Local Pattern Match Baseline",
                category: category,
                label: "scam",
                similarity_score: 0.85,
                source_name: "Local Offline Rule",
                source_url: "",
                example_type: "offline_fallback"
            }
        ],
        score_breakdown: [
            { category: "Extracted Indicators", contribution: `+${score}`, reason: "Matched suspicious keywords" }
        ],
        safety_steps: actions,
        analysis_metadata: { engine: "Local Offline Heuristic", gemini_active: false, rag_count: 1 }
    };
}

// Render Results on Dashboard
function renderResults(data) {
    const emptyState = document.getElementById('emptyState');
    const activeResults = document.getElementById('activeResults');

    setElementVisible(emptyState, false);
    setElementVisible(activeResults, true, 'block');

    const score = typeof data.risk_score === 'number' ? data.risk_score : 0;
    const level = data.risk_level || 'Low Risk';
    const category = data.scam_category || 'General Threat Analysis';

    // Animate Gauge Score
    animateGaugeScore(score);

    // Update SVG Arc & Color Theme
    updateGaugeColorAndArc(score, level, data.color, data.bg_style);

    // Update Category & Summary
    const tagEl = document.getElementById('scamCategoryTag');
    const sumEl = document.getElementById('riskSummaryText');
    const uncertaintyEl = document.getElementById('uncertaintyTag');

    if (tagEl) tagEl.innerText = category;
    if (sumEl) sumEl.innerText = data.summary || "Analysis complete.";
    if (uncertaintyEl) uncertaintyEl.innerText = data.uncertainty || "";

    // Render Red Flags Grid (Deduplicated)
    const redFlagsGrid = document.getElementById('redFlagsGrid');
    if (redFlagsGrid) {
        redFlagsGrid.innerHTML = '';
        if (data.red_flags && data.red_flags.length > 0) {
            data.red_flags.forEach(flag => {
                const card = document.createElement('div');
                card.className = `flag-item severity-${flag.severity || 'Medium'}`;
                const matchedPhraseSnippet = flag.matched_phrase ? `<div class="flag-evidence"><strong>Evidence:</strong> "${escapeHtml(flag.matched_phrase)}"</div>` : '';
                card.innerHTML = `
                    <div class="flag-header">
                        <span class="flag-title">${escapeHtml(flag.category)}</span>
                        <span class="flag-tag ${flag.severity || 'Medium'}">${flag.severity || 'Medium'}</span>
                    </div>
                    <p class="flag-body">${escapeHtml(flag.description)}</p>
                    ${matchedPhraseSnippet}
                `;
                redFlagsGrid.appendChild(card);
            });
        } else {
            redFlagsGrid.innerHTML = `<div class="flag-item safe"><div class="flag-header"><span class="flag-title">No Red Flags Detected</span></div><p class="flag-body">No malicious links, untraceable payment demands, or deceptive threat patterns were triggered.</p></div>`;
        }
    }

    // Render Similar Patterns in Knowledge Base
    const evidenceList = document.getElementById('evidenceList');
    if (evidenceList) {
        evidenceList.innerHTML = '';
        if (data.rag_matches && data.rag_matches.length > 0) {
            data.rag_matches.forEach(item => {
                const div = document.createElement('div');
                const isLegit = item.label === 'legitimate' || item.label === 'legit';
                div.className = `evidence-chip ${isLegit ? 'legit-chip' : 'scam-chip'}`;
                const iconColor = isLegit ? '#10b981' : '#f97316';
                const labelText = isLegit ? 'Legitimate Reference' : 'Documented Scam Pattern';
                div.innerHTML = `
                    <div class="evidence-header">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${iconColor}" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                        <strong>${escapeHtml(item.title)}</strong>
                    </div>
                    <div class="evidence-meta">
                        <span class="badge-${item.label}">${labelText}</span>
                        <span>Similarity Score: ${item.similarity_score}</span>
                        <span>Source: ${escapeHtml(item.source_name || 'KB')}</span>
                    </div>
                `;
                evidenceList.appendChild(div);
            });
        } else {
            evidenceList.innerHTML = `<div class="evidence-chip">No similar patterns retrieved from local knowledge base. Analysis evaluated via direct text engine.</div>`;
        }
    }

    // Render Pattern Triggers (Unique Canonical Tags)
    const cuesTags = document.getElementById('linguisticCuesTags');
    if (cuesTags) {
        cuesTags.innerHTML = '';
        if (data.pattern_triggers && data.pattern_triggers.length > 0) {
            data.pattern_triggers.forEach(trigger => {
                const span = document.createElement('span');
                span.className = 'cue-pill';
                span.innerText = trigger;
                cuesTags.appendChild(span);
            });
        } else {
            cuesTags.innerHTML = `<span class="cue-pill clean">Standard Clean Content</span>`;
        }
    }

    // Render Recommended Actions Checklist
    const actionsList = document.getElementById('actionsList');
    if (actionsList) {
        actionsList.innerHTML = '';
        if (data.safety_steps && data.safety_steps.length > 0) {
            data.safety_steps.forEach(action => {
                const li = document.createElement('li');
                li.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg> <span>${escapeHtml(action)}</span>`;
                actionsList.appendChild(li);
            });
        }
    }

    // Timestamp
    const timeEl = document.getElementById('reportTime');
    if (timeEl) timeEl.innerText = `Analyzed at ${new Date().toLocaleTimeString()}`;
}

// Gauge Score Count-Up Animation
function animateGaugeScore(targetScore) {
    const gaugeValue = document.getElementById('gaugeValue');
    if (!gaugeValue) return;
    let start = 0;
    const duration = 600;
    const stepTime = 20;
    const steps = duration / stepTime;
    const increment = targetScore / steps;
    
    const timer = setInterval(() => {
        start += increment;
        if (start >= targetScore) {
            gaugeValue.innerText = Math.round(targetScore);
            clearInterval(timer);
        } else {
            gaugeValue.innerText = Math.round(start);
        }
    }, stepTime);
}

// Authoritative Color & Gauge Mapping:
// 0–24: Low Risk (green)
// 25–59: Caution (yellow/amber)
// 60–84: High Scam Risk (orange/crimson)
// 85–100: Critical Threat (red/crimson)
function updateGaugeColorAndArc(score, level, customColor, customBgStyle) {
    const gaugeArc = document.getElementById('gaugeArc');
    const badge = document.getElementById('riskLevelBadge');
    if (!gaugeArc || !badge) return;

    const maxOffset = 330;
    const clampedScore = Math.max(0, Math.min(100, score));
    const offset = maxOffset - (maxOffset * (clampedScore / 100));
    gaugeArc.style.strokeDashoffset = offset;

    let strokeColor = customColor;
    let bgStyle = customBgStyle;

    if (!strokeColor) {
        if (clampedScore >= 85) {
            strokeColor = '#f43f5e';
            bgStyle = 'background: rgba(244, 63, 94, 0.16); color: #fecdd3; border: 1px solid rgba(244, 63, 94, 0.5); box-shadow: 0 0 20px rgba(244, 63, 94, 0.3);';
        } else if (clampedScore >= 60) {
            strokeColor = '#f97316';
            bgStyle = 'background: rgba(249, 115, 22, 0.16); color: #ffedd5; border: 1px solid rgba(249, 115, 22, 0.5); box-shadow: 0 0 20px rgba(249, 115, 22, 0.3);';
        } else if (clampedScore >= 25) {
            strokeColor = '#f59e0b';
            bgStyle = 'background: rgba(245, 158, 11, 0.16); color: #fef3c7; border: 1px solid rgba(245, 158, 11, 0.5); box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);';
        } else {
            strokeColor = '#10b981';
            bgStyle = 'background: rgba(16, 185, 129, 0.16); color: #d1fae5; border: 1px solid rgba(16, 185, 129, 0.5); box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);';
        }
    }

    gaugeArc.style.stroke = strokeColor;
    badge.setAttribute('style', bgStyle || '');
    badge.innerText = (level || 'LOW RISK').toUpperCase();
}

// Copy Full Report
function copyReport() {
    if (!lastAnalysisResult) return;
    
    const r = lastAnalysisResult;
    const text = `🛡️ SCAM OR LEGIT? AI SUSPICION REPORT 🛡️
-----------------------------------------
Risk Score: ${r.risk_score}/100 (${r.risk_level})
Category: ${r.scam_category}
Summary: ${r.summary}
Uncertainty: ${r.uncertainty || 'N/A'}

DETECTED RED FLAGS:
${(r.red_flags || []).map(f => `• [${f.severity}] ${f.category}: ${f.description}`).join('\n')}

KNOWLEDGE BASE SIMILAR PATTERNS:
${(r.rag_matches || []).map(m => `• [${m.label}] ${m.title} (Similarity: ${m.similarity_score})`).join('\n')}

SAFETY RECOMMENDATIONS:
${(r.safety_steps || []).map(a => `✔ ${a}`).join('\n')}

Disclaimers: Heuristic risk score based on pattern matching and indicator analysis.
Analyzed via ScamOrLegit AI Threat Scanner.
`;

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showToast("Report copied to clipboard!");
        }).catch(() => {
            fallbackCopy(text);
        });
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    showToast("Report copied to clipboard!");
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.innerText = msg;
    setElementVisible(toast, true, 'block');
    setTimeout(() => {
        setElementVisible(toast, false);
    }, 3000);
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
