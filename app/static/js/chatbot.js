/**
 * TRACE-X Conversational AI / Chatbot Client JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    const messagesContainer = document.getElementById('chatbot-messages');
    const inputForm = document.getElementById('chatbot-input-form');
    const userInput = document.getElementById('chatbot-user-input');
    const evidenceInput = document.getElementById('chatbot-evidence-input');
    const btnApplyEvidence = document.getElementById('btn-apply-evidence');
    const btnLoadSample = document.getElementById('btn-load-sample-evidence');
    const btnClearEvidence = document.getElementById('btn-clear-evidence');
    const btnResetChat = document.getElementById('btn-reset-chat');
    const evidenceStatusBadge = document.getElementById('evidence-status-badge');
    const promptButtons = document.querySelectorAll('.chatbot-prompt-btn');

    let sessionId = localStorage.getItem('tracex_chatbot_session_id') || ('session_' + Math.random().toString(36).substring(2, 10));
    localStorage.setItem('tracex_chatbot_session_id', sessionId);

    const SAMPLE_EVIDENCE_TEXT = `CLASSIFIED INTELLIGENCE REPORT - OPERATION CYBER-TRACE
DATE: 14 OCTOBER 2024
LOCATION: SYDNEY, AUSTRALIA

On 12 October 2024, subject Marcus Vance was observed entering the Secure Communications Building located in Sydney at 14:30 hours. He met with Dr. Elena Rostova, a senior cryptographer working for CyberData Corp. 

During the meeting, Marcus Vance transferred an encrypted flash drive containing flight telemetry data for Flight AC-892. Later that evening, at 21:15 hours, Elena Rostova traveled to Melbourne to deliver the physical encryption keys to operative Viktor Krum.

On 13 October 2024, Viktor Krum accessed a remote server located in Singapore and downloaded 45 Gigabytes of intercepted signal logs. Australian Cyber Security Centre (ACSC) initiated tracking protocols at 03:00 hours on 14 October 2024.`;

    function updateEvidenceStatus(active) {
        if (!evidenceStatusBadge) return;
        if (active) {
            evidenceStatusBadge.className = 'badge bg-success';
            evidenceStatusBadge.innerHTML = '<i class="fa-solid fa-check me-1"></i> Context Loaded';
        } else {
            evidenceStatusBadge.className = 'badge bg-secondary';
            evidenceStatusBadge.innerHTML = 'No Evidence Loaded';
        }
    }

    function scrollToBottom() {
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    function appendMessage(sender, text, metadata = null) {
        if (!messagesContainer) return;

        const isUser = sender === 'user';
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        const row = document.createElement('div');
        row.className = `chat-bubble-row ${isUser ? 'user-row' : 'bot-row'} mb-3`;

        let bubbleHTML = '';

        if (isUser) {
            bubbleHTML = `
                <div class="chat-bubble user-bubble p-3 rounded">
                    <div class="bubble-header d-flex justify-content-end mb-1">
                        <small class="text-secondary opacity-75">${timeStr}</small>
                    </div>
                    <div class="bubble-text text-white">${escapeHtml(text)}</div>
                </div>
            `;
        } else {
            // Render markdown bold and quotes simply
            let formattedText = formatMarkdown(text);
            bubbleHTML = `
                <div class="bot-avatar me-2">
                    <i class="fa-solid fa-robot text-cyan"></i>
                </div>
                <div class="chat-bubble bot-bubble p-3 rounded">
                    <div class="bubble-header d-flex justify-content-between align-items-center mb-1">
                        <span class="badge bg-dark-card text-cyan font-monospace">TRACE-X AI</span>
                        <small class="text-secondary opacity-75">${timeStr}</small>
                    </div>
                    <div class="bubble-text text-light">${formattedText}</div>
                </div>
            `;
        }

        row.innerHTML = bubbleHTML;
        messagesContainer.appendChild(row);
        scrollToBottom();

        if (metadata && metadata.evidence_active !== undefined) {
            updateEvidenceStatus(metadata.evidence_active);
        }
    }

    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function formatMarkdown(txt) {
        let clean = txt;
        clean = clean.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        clean = clean.replace(/\*(.*?)\*/g, '<em>$1</em>');
        clean = clean.replace(/^>\s*(.*$)/gim, '<blockquote class="border-start border-cyan ps-2 text-cyan my-2">$1</blockquote>');
        clean = clean.replace(/\n/g, '<br>');
        return clean;
    }

    async function sendMessage(text) {
        if (!text || !text.trim()) return;

        appendMessage('user', text);
        userInput.value = '';

        const currentEvidence = evidenceInput ? evidenceInput.value.trim() : '';

        // Show typing indicator
        const typingRow = document.createElement('div');
        typingRow.id = 'typing-indicator-row';
        typingRow.className = 'chat-bubble-row bot-row mb-3';
        typingRow.innerHTML = `
            <div class="bot-avatar me-2"><i class="fa-solid fa-robot text-cyan"></i></div>
            <div class="chat-bubble bot-bubble p-3 rounded text-secondary">
                <i class="fa-solid fa-circle-notch fa-spin me-1 text-cyan"></i> Analyzing evidence context...
            </div>
        `;
        messagesContainer.appendChild(typingRow);
        scrollToBottom();

        try {
            const response = await fetch('/chatbot/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: text,
                    evidence: currentEvidence
                })
            });

            const data = await response.json();
            const indicator = document.getElementById('typing-indicator-row');
            if (indicator) indicator.remove();

            if (data.success && data.message) {
                appendMessage('bot', data.message.text, data.message.metadata);
            } else {
                appendMessage('bot', '⚠️ Error processing request: ' + (data.error || 'Server error.'));
            }
        } catch (err) {
            const indicator = document.getElementById('typing-indicator-row');
            if (indicator) indicator.remove();
            appendMessage('bot', '⚠️ Communication error with TRACE-X chatbot server.');
        }
    }

    if (inputForm) {
        inputForm.addEventListener('submit', function (e) {
            e.preventDefault();
            sendMessage(userInput.value);
        });
    }

    if (btnLoadSample && evidenceInput) {
        btnLoadSample.addEventListener('click', function () {
            evidenceInput.value = SAMPLE_EVIDENCE_TEXT;
            updateEvidenceStatus(true);
        });
    }

    if (btnApplyEvidence && evidenceInput) {
        btnApplyEvidence.addEventListener('click', function () {
            if (evidenceInput.value.trim()) {
                updateEvidenceStatus(true);
                sendMessage("Updated active evidence context.");
            } else {
                updateEvidenceStatus(false);
            }
        });
    }

    if (btnClearEvidence && evidenceInput) {
        btnClearEvidence.addEventListener('click', async function () {
            evidenceInput.value = '';
            updateEvidenceStatus(false);
            await fetch('/chatbot/clear-evidence', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            appendMessage('bot', 'Active evidence context cleared.');
        });
    }

    if (btnResetChat) {
        btnResetChat.addEventListener('click', async function () {
            await fetch('/chatbot/new', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            if (messagesContainer) messagesContainer.innerHTML = '';
            appendMessage('bot', 'New conversation session started.');
        });
    }

    promptButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const prompt = this.getAttribute('data-prompt');
            if (prompt) sendMessage(prompt);
        });
    });

    // Chatbot Active Evidence Upload Setup
    setupChatbotUploadHandler('upload-chatbot-file', 'chatbot-evidence-input', 'chatbot-upload-status');
    setupChatbotUploadHandler('upload-chatbot-image', 'chatbot-evidence-input', 'chatbot-upload-status');

    function setupChatbotUploadHandler(fileInputId, targetTextareaId, statusContainerId) {
        const fileInput = document.getElementById(fileInputId);
        const targetTextarea = document.getElementById(targetTextareaId);
        const statusContainer = document.getElementById(statusContainerId);

        if (!fileInput || !targetTextarea) return;

        fileInput.addEventListener('change', async function () {
            const files = this.files;
            if (!files || files.length === 0) return;

            for (let f of files) {
                if (f.size > 10 * 1024 * 1024) {
                    if (statusContainer) {
                        statusContainer.innerHTML = `<div class="alert alert-danger py-2 px-3 small m-0 mb-2"><i class="fa-solid fa-triangle-exclamation me-1"></i> File "${f.name}" exceeds 10 MB limit.</div>`;
                    }
                    return;
                }
            }

            if (statusContainer) {
                statusContainer.innerHTML = `<div class="alert alert-info py-2 px-3 small m-0 mb-2"><i class="fa-solid fa-spinner fa-spin me-1"></i> Extracting text...</div>`;
            }

            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }

            try {
                const res = await fetch('/api/extract-text', {
                    method: 'POST',
                    body: formData
                });

                const data = await res.json();

                if (data.success && data.extracted_text) {
                    if (targetTextarea.value.trim()) {
                        targetTextarea.value = targetTextarea.value.trim() + "\n\n" + data.extracted_text;
                    } else {
                        targetTextarea.value = data.extracted_text;
                    }

                    updateEvidenceStatus(true);

                    let msg = `<div class="alert alert-success py-2 px-3 small m-0 mb-2"><i class="fa-solid fa-circle-check me-1"></i> Extracted text from <strong>${data.filenames.join(', ')}</strong>. Click <em>"Update Active Evidence Context"</em> to apply.</div>`;
                    if (data.warnings && data.warnings.length > 0) {
                        msg += `<div class="alert alert-warning py-1 px-3 small m-0 mb-2"><i class="fa-solid fa-info-circle me-1"></i> ${data.warnings.join(' ')}</div>`;
                    }
                    if (statusContainer) statusContainer.innerHTML = msg;
                } else {
                    if (statusContainer) {
                        statusContainer.innerHTML = `<div class="alert alert-danger py-2 px-3 small m-0 mb-2"><i class="fa-solid fa-triangle-exclamation me-1"></i> ${data.error || 'Failed to extract text from upload.'}</div>`;
                    }
                }
            } catch (err) {
                if (statusContainer) {
                    statusContainer.innerHTML = `<div class="alert alert-danger py-2 px-3 small m-0 mb-2"><i class="fa-solid fa-triangle-exclamation me-1"></i> Error connecting to extraction server.</div>`;
                }
            }
        });
    }
});

