/**
 * TRACE-X Question Answering (QA) System — Standalone Client JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    initQAPage();
});

function initQAPage() {
    const btnAnswer = document.getElementById('btn-find-answer');
    if (btnAnswer) {
        btnAnswer.addEventListener('click', processQA);
    }

    const btnClear = document.getElementById('btn-clear-qa');
    if (btnClear) {
        btnClear.addEventListener('click', clearQA);
    }

    // Sample Question shortcut buttons
    document.querySelectorAll('.qa-sample-q-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const sampleQ = this.getAttribute('data-q');
            const qInput = document.getElementById('input-qa-question');
            if (qInput && sampleQ) {
                qInput.value = sampleQ;
                processQA();
            }
        });
    });

    // Sample Evidence shortcut button
    const btnLoadSampleEvidence = document.getElementById('btn-load-sample-evidence');
    if (btnLoadSampleEvidence) {
        btnLoadSampleEvidence.addEventListener('click', function() {
            const sampleText = "John Smith, an employee of Microsoft, visited Chennai on 12 March 2026 to investigate a reported incident. He met with officer Robert Brown at the Chennai Central Railway Station headquarters at 14:00 hours. The investigation team collected network logs and evidence files from Cyberdyne Systems to analyze potential security breaches.";
            const contextInput = document.getElementById('input-qa-context');
            if (contextInput) {
                contextInput.value = sampleText;
            }
        });
    }

    // QA Evidence Upload Setup
    setupQAUploadHandler('upload-qa-file', 'input-qa-context', 'qa-upload-status');
    setupQAUploadHandler('upload-qa-image', 'input-qa-context', 'qa-upload-status');
}

function setupQAUploadHandler(fileInputId, targetTextareaId, statusContainerId) {
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
            statusContainer.innerHTML = `<div class="alert alert-info py-2 px-3 small m-0 mb-2"><i class="fa-solid fa-spinner fa-spin me-1"></i> Extracting text from ${files.length} file(s)...</div>`;
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

                let msg = `<div class="alert alert-success py-2 px-3 small m-0 mb-2"><i class="fa-solid fa-circle-check me-1"></i> Extracted text from <strong>${data.filenames.join(', ')}</strong> (${data.extracted_text.length} chars).</div>`;
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


function processQA() {
    const contextInput = document.getElementById('input-qa-context');
    const questionInput = document.getElementById('input-qa-question');
    const statusBadge = document.getElementById('qa-status-badge');
    const spinner = document.getElementById('qa-spinner');

    if (!contextInput || !questionInput) return;

    const context = contextInput.value.trim();
    const question = questionInput.value.trim();

    if (!context) {
        alert('Please provide evidence context text.');
        return;
    }

    if (!question) {
        alert('Please enter a question to ask.');
        return;
    }

    if (spinner) spinner.classList.remove('d-none');
    if (statusBadge) {
        statusBadge.className = 'badge bg-warning text-dark';
        statusBadge.textContent = 'Processing...';
    }

    fetch('/qa/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context: context, question: question })
    })
    .then(res => res.json())
    .then(data => {
        if (spinner) spinner.classList.add('d-none');

        document.getElementById('qa-placeholder').classList.add('d-none');
        document.getElementById('qa-results-container').classList.remove('d-none');

        if (!data.success || data.status === 'Error') {
            if (statusBadge) {
                statusBadge.className = 'badge bg-danger';
                statusBadge.textContent = 'Error';
            }
            document.getElementById('qa-answer-text').innerText = data.error_message || 'An error occurred during analysis.';
            document.getElementById('qa-evidence-text').innerText = '--';
            document.getElementById('qa-method-name').innerText = data.method || 'Extractive Evidence Retrieval';
            document.getElementById('qa-confidence-val').innerText = 'N/A';
            return;
        }

        if (data.status === 'Answer Not Found') {
            if (statusBadge) {
                statusBadge.className = 'badge bg-secondary';
                statusBadge.textContent = 'Answer Not Found';
            }
            document.getElementById('qa-answer-text').innerHTML = `<span class="text-warning"><i class="fa-solid fa-triangle-exclamation me-1"></i> ${data.answer}</span>`;
            document.getElementById('qa-evidence-text').innerText = data.supporting_evidence || 'No matching sentence found in evidence context.';
            document.getElementById('qa-method-name').innerText = data.method;
            document.getElementById('qa-confidence-val').innerText = '0.0%';
            return;
        }

        // Answer Found
        if (statusBadge) {
            statusBadge.className = 'badge bg-success';
            statusBadge.textContent = 'Answer Extracted';
        }

        document.getElementById('qa-answer-text').innerText = data.answer;
        document.getElementById('qa-evidence-text').innerText = data.supporting_evidence;
        document.getElementById('qa-method-name').innerText = data.method;
        document.getElementById('qa-confidence-val').innerText = `${data.confidence || 0}%`;
    })
    .catch(err => {
        if (spinner) spinner.classList.add('d-none');
        if (statusBadge) {
            statusBadge.className = 'badge bg-danger';
            statusBadge.textContent = 'Network Error';
        }
        console.error("QA Error:", err);
    });
}

function clearQA() {
    const contextInput = document.getElementById('input-qa-context');
    const questionInput = document.getElementById('input-qa-question');
    const statusBadge = document.getElementById('qa-status-badge');

    if (contextInput) contextInput.value = '';
    if (questionInput) questionInput.value = '';

    if (statusBadge) {
        statusBadge.className = 'badge bg-secondary';
        statusBadge.textContent = 'Awaiting Input';
    }

    document.getElementById('qa-placeholder').classList.remove('d-none');
    document.getElementById('qa-results-container').classList.add('d-none');
}
