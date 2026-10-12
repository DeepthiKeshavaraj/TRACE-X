/**
 * TRACE-X Intelligence System — Frontend Application JavaScript
 */

let categoryChartInstance = null;
let lengthChartInstance = null;
let modelComparisonChartInstance = null;
let activeModelDetails = null;

// Speech Recording variables
let mediaRecorder = null;
let audioChunks = [];
let recordingStartTime = 0;
let recordingTimerInterval = null;
let liveSpeechRecognizer = null;

// ==================== DASHBOARD PAGE ====================

function loadDashboardSummary() {
    fetch('/api/dashboard-summary')
        .then(response => response.json())
        .then(data => {
            const missingAlert = document.getElementById('missing-dataset-alert');
            if (missingAlert) {
                if (!data.dataset_found) {
                    missingAlert.classList.remove('d-none');
                } else {
                    missingAlert.classList.add('d-none');
                }
            }

            if (document.getElementById('kpi-total-records')) {
                document.getElementById('kpi-total-records').innerText = data.total_records.toLocaleString();
                document.getElementById('kpi-categories').innerText = data.categories_count;
                document.getElementById('kpi-train-records').innerText = data.train_records.toLocaleString();
                document.getElementById('kpi-test-records').innerText = data.test_records.toLocaleString();
                document.getElementById('kpi-best-acc').innerText = data.best_model_accuracy;
                document.getElementById('kpi-best-f1').innerText = data.best_model_f1;
            }
        })
        .catch(err => console.error("Error loading dashboard summary:", err));
}

// ==================== DATA & PREPROCESSING PAGE ====================

function loadDataPageInfo() {
    fetchRawFilesStatus();
    loadEdaStats();

    const btnVal = document.getElementById('btn-run-validation');
    if (btnVal) {
        btnVal.addEventListener('click', runValidation);
    }

    const btnPrep = document.getElementById('btn-run-preprocessing');
    if (btnPrep) {
        btnPrep.addEventListener('click', runPreprocessing);
    }
}

function fetchRawFilesStatus() {
    fetch('/api/data-status')
        .then(res => res.json())
        .then(data => {
            const missingAlert = document.getElementById('missing-dataset-alert');
            if (missingAlert) {
                if (data.found_count === 0) {
                    missingAlert.classList.remove('d-none');
                } else {
                    missingAlert.classList.add('d-none');
                }
            }

            const tbody = document.getElementById('raw-files-table-body');
            if (!tbody) return;

            tbody.innerHTML = '';
            (data.files || []).forEach(file => {
                const tr = document.createElement('tr');
                const isFound = file.status === 'Found';
                const statusBadge = isFound
                    ? '<span class="badge bg-success"><i class="fa-solid fa-check me-1"></i> Found</span>'
                    : `<span class="badge bg-danger"><i class="fa-solid fa-xmark me-1"></i> ${file.status}</span>`;

                tr.innerHTML = `
                    <td class="fw-bold text-white"><i class="fa-solid fa-file-csv text-cyan me-2"></i>${file.file}</td>
                    <td>${statusBadge}</td>
                    <td class="font-monospace text-cyan fw-bold">${file.records.toLocaleString()}</td>
                    <td class="font-monospace text-purple fw-bold">${file.columns}</td>
                `;
                tbody.appendChild(tr);
            });

            if (document.getElementById('stat-total-raw-records')) {
                document.getElementById('stat-total-raw-records').innerText = (data.total_raw_records || 0).toLocaleString();
                document.getElementById('stat-total-categories').innerText = data.total_categories || 0;
            }
        })
        .catch(err => console.error("Error fetching raw status:", err));
}

function runValidation() {
    const outputPanel = document.getElementById('validation-output');
    if (outputPanel) outputPanel.classList.remove('d-none');

    fetch('/api/run-validation', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (!data.valid) {
                alert(data.error || "Validation failed.");
                return;
            }

            document.getElementById('val-missing').innerText = data.total_missing_values;
            document.getElementById('val-duplicates').innerText = data.duplicate_records;
            document.getElementById('val-invalid-cats').innerText = (data.invalid_categories && data.invalid_categories.length)
                ? data.invalid_categories.join(', ') : 'None';
            document.getElementById('val-empty-text').innerText = data.empty_text_records;
            document.getElementById('val-shape').innerText = `[${data.dataset_shape[0]} rows, ${data.dataset_shape[1]} cols]`;
        });
}

function runPreprocessing() {
    const spinner = document.getElementById('preprocessing-spinner');
    if (spinner) spinner.classList.remove('d-none');

    fetch('/api/run-preprocessing', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (spinner) spinner.classList.add('d-none');
            if (!data.success) {
                alert(data.message || "Preprocessing failed.");
                return;
            }

            const m = data.metrics || {};
            document.getElementById('prep-input').innerText = (m.input_records || 0).toLocaleString();
            document.getElementById('prep-output').innerText = (m.output_records || 0).toLocaleString();
            document.getElementById('prep-removed').innerText = (m.removed_records || 0).toLocaleString();
            document.getElementById('prep-missing').innerText = (m.missing_values || 0).toLocaleString();
            document.getElementById('prep-duplicates').innerText = (m.duplicate_records || 0).toLocaleString();

            loadEdaStats();
        })
        .catch(err => {
            if (spinner) spinner.classList.add('d-none');
            console.error("Error running preprocessing:", err);
        });
}

function loadEdaStats() {
    fetch('/api/eda-stats')
        .then(res => res.json())
        .then(data => {
            if (!data.exists) return;

            if (document.getElementById('prep-output') && document.getElementById('prep-output').innerText === '--') {
                document.getElementById('prep-output').innerText = data.total_records.toLocaleString();
            }

            renderCategoryDistChart(data.category_counts || {});
            renderTextLengthChart(data.histogram_bins || []);
            renderEdaTable(data.word_stats || {}, data.char_stats || {});
        });
}

function renderCategoryDistChart(countsObj) {
    const ctx = document.getElementById('chart-category-dist');
    if (!ctx) return;

    const labels = Object.keys(countsObj);
    const dataVals = Object.values(countsObj);

    if (categoryChartInstance) categoryChartInstance.destroy();

    categoryChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Records',
                data: dataVals,
                backgroundColor: ['#06b6d4', '#c084fc', '#6366f1', '#10b981', '#f59e0b'],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#cbd5e1' }, grid: { color: '#1e293b' } },
                y: { ticks: { color: '#cbd5e1' }, grid: { color: '#1e293b' } }
            }
        }
    });
}

function renderTextLengthChart(binsArray) {
    const ctx = document.getElementById('chart-text-length');
    if (!ctx) return;

    const labels = binsArray.map(b => b.bin);
    const dataVals = binsArray.map(b => b.count);

    if (lengthChartInstance) lengthChartInstance.destroy();

    lengthChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Document Count',
                data: dataVals,
                backgroundColor: '#6366f1',
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#cbd5e1' }, grid: { color: '#1e293b' } },
                y: { ticks: { color: '#cbd5e1' }, grid: { color: '#1e293b' } }
            }
        }
    });
}

function renderEdaTable(wStats, cStats) {
    const tbody = document.getElementById('eda-stats-tbody');
    if (!tbody) return;

    tbody.innerHTML = `
        <tr>
            <td class="fw-bold text-cyan">Word Count</td>
            <td class="text-white font-monospace fw-bold">${wStats.min || 0}</td>
            <td class="text-white font-monospace fw-bold">${wStats.max || 0}</td>
            <td class="text-cyan font-monospace fw-bold">${wStats.mean || 0}</td>
            <td class="text-purple font-monospace fw-bold">${wStats.median || 0}</td>
            <td class="text-amber font-monospace fw-bold">${wStats.std || 0}</td>
        </tr>
        <tr>
            <td class="fw-bold text-purple">Character Count</td>
            <td class="text-white font-monospace fw-bold">${cStats.min || 0}</td>
            <td class="text-white font-monospace fw-bold">${cStats.max || 0}</td>
            <td class="text-cyan font-monospace fw-bold">${cStats.mean || 0}</td>
            <td class="text-purple font-monospace fw-bold">${cStats.median || 0}</td>
            <td class="text-amber font-monospace fw-bold">${cStats.std || 0}</td>
        </tr>
    `;
}

// ==================== CLASSIFICATION PAGE ====================

function loadClassificationPageInfo() {
    loadModelResults();

    const btnTrain = document.getElementById('btn-train-models');
    if (btnTrain) {
        btnTrain.addEventListener('click', triggerTrainModels);
    }

    const selectModel = document.getElementById('select-eval-model');
    if (selectModel) {
        selectModel.addEventListener('change', function() {
            renderSelectedModelEvaluation(this.value);
        });
    }

    const btnClassify = document.getElementById('btn-classify-text');
    if (btnClassify) {
        btnClassify.addEventListener('click', runCustomPrediction);
    }

    const samples = {
        'business': 'Global financial stock markets surged today as major tech conglomerates reported record quarterly revenues and profits, while central banks held interest rates steady.',
        'education': 'Universities and public schools across the nation introduced new digital STEM learning programs and postgraduate research scholarships for doctoral candidates.',
        'entertainment': 'The international film festival announced its annual award winners yesterday, with independent cinema productions breaking box office streaming records.',
        'sports': 'The national football team secured a thrilling 3-2 victory in the final minutes of extra time to claim the championship title before a record stadium crowd.',
        'technology': 'Computer scientists unveiled a breakthrough artificial intelligence language model capable of automated code generation and quantum algorithm optimization.'
    };

    document.querySelectorAll('.sample-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const key = this.getAttribute('data-sample');
            const textArea = document.getElementById('input-evidence-text');
            if (textArea && samples[key]) {
                textArea.value = samples[key];
                runCustomPrediction();
            }
        });
    });
}

function triggerTrainModels() {
    const spinner = document.getElementById('training-spinner');
    if (spinner) spinner.classList.remove('d-none');

    fetch('/api/train-models', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (spinner) spinner.classList.add('d-none');
            if (!data.success) {
                alert(data.message || "Model training failed.");
                return;
            }
            processModelResults(data);
        })
        .catch(err => {
            if (spinner) spinner.classList.add('d-none');
            console.error("Error training models:", err);
        });
}

function loadModelResults() {
    fetch('/api/model-results')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                processModelResults(data);
            }
        });
}

function processModelResults(data) {
    activeModelDetails = data.details || {};
    const comparison = data.comparison || [];
    
    const tbody = document.getElementById('comparison-table-body');
    if (tbody) {
        tbody.innerHTML = '';
        comparison.forEach(row => {
            const isBest = row.Model === data.best_model_name;
            const badgeHtml = isBest
                ? '<span class="badge bg-success px-3 py-1 fs-6"><i class="fa-solid fa-crown me-1"></i> Best Model</span>'
                : '<span class="badge bg-secondary">Evaluated</span>';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="text-start fw-bold text-white fs-6">${row.Model}</td>
                <td class="font-monospace text-cyan fw-bold fs-6">${row.Accuracy}%</td>
                <td class="font-monospace text-amber fw-bold fs-6">${row.Precision}%</td>
                <td class="font-monospace text-purple fw-bold fs-6">${row.Recall}%</td>
                <td class="font-monospace text-green fw-bold fs-6">${row['F1 Score']}%</td>
                <td>${badgeHtml}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    renderModelComparisonChart(comparison);

    const selectModel = document.getElementById('select-eval-model');
    const selected = selectModel ? selectModel.value : 'Multinomial Naive Bayes';
    renderSelectedModelEvaluation(selected);
}

function renderModelComparisonChart(comparisonArray) {
    const ctx = document.getElementById('chart-model-comparison');
    if (!ctx) return;

    const labels = comparisonArray.map(c => c.Model);
    const accData = comparisonArray.map(c => c.Accuracy);
    const f1Data = comparisonArray.map(c => c['F1 Score']);

    if (modelComparisonChartInstance) modelComparisonChartInstance.destroy();

    modelComparisonChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                { label: 'Accuracy (%)', data: accData, backgroundColor: '#06b6d4', borderRadius: 6 },
                { label: 'F1 Score (%)', data: f1Data, backgroundColor: '#6366f1', borderRadius: 6 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#ffffff', font: { weight: 'bold' } } } },
            scales: {
                x: { ticks: { color: '#ffffff', font: { weight: 'bold' } }, grid: { color: '#1e293b' } },
                y: { min: 80, max: 100, ticks: { color: '#ffffff', font: { weight: 'bold' } }, grid: { color: '#1e293b' } }
            }
        }
    });
}

function renderSelectedModelEvaluation(modelName) {
    if (!activeModelDetails || !activeModelDetails[modelName]) return;

    const modelInfo = activeModelDetails[modelName];
    const cm = modelInfo.confusion_matrix || [];
    const labels = modelInfo.labels || [];
    const report = modelInfo.classification_report || {};

    const cmContainer = document.getElementById('confusion-matrix-container');
    if (cmContainer) {
        let tableHtml = '<table class="table table-dark table-bordered text-center m-0 align-middle small"><thead><tr><th>Actual \\ Pred</th>';
        labels.forEach(l => { tableHtml += `<th class="text-cyan fw-bold">${l}</th>`; });
        tableHtml += '</tr></thead><tbody>';

        cm.forEach((row, rIdx) => {
            tableHtml += `<tr><th class="text-start text-cyan fw-bold">${labels[rIdx]}</th>`;
            const maxInRow = Math.max(...row, 1);
            row.forEach(val => {
                let cellClass = 'cm-zero';
                if (val > 0) {
                    const ratio = val / maxInRow;
                    cellClass = ratio > 0.6 ? 'cm-high' : (ratio > 0.2 ? 'cm-mid' : 'cm-low');
                }
                tableHtml += `<td><div class="cm-cell ${cellClass}">${val}</div></td>`;
            });
            tableHtml += '</tr>';
        });
        tableHtml += '</tbody></table>';
        cmContainer.innerHTML = tableHtml;
    }

    const rBody = document.getElementById('eval-report-tbody');
    if (rBody) {
        rBody.innerHTML = '';
        labels.forEach(cat => {
            const catStats = report[cat] || {};
            const prec = ((catStats.precision || 0) * 100).toFixed(1);
            const rec = ((catStats.recall || 0) * 100).toFixed(1);
            const f1 = ((catStats['f1-score'] || 0) * 100).toFixed(1);

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="text-start fw-bold text-white fs-6">${cat}</td>
                <td class="font-monospace text-cyan fw-bold fs-6">${prec}%</td>
                <td class="font-monospace text-amber fw-bold fs-6">${rec}%</td>
                <td class="font-monospace text-green fw-bold fs-6">${f1}%</td>
            `;
            rBody.appendChild(tr);
        });
    }
}

function runCustomPrediction() {
    const textInput = document.getElementById('input-evidence-text');
    const modelSelect = document.getElementById('select-predict-model');

    const text = textInput ? textInput.value.trim() : '';
    const model = modelSelect ? modelSelect.value : null;

    if (!text) {
        alert("Please enter news or evidence text to classify.");
        return;
    }

    fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, model: model })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            alert(data.message || "Prediction failed.");
            return;
        }

        const placeholder = document.getElementById('prediction-placeholder');
        const resultsBox = document.getElementById('prediction-results');

        if (placeholder) placeholder.classList.add('d-none');
        if (resultsBox) resultsBox.classList.remove('d-none');

        const catTitle = document.getElementById('pred-category-title');
        const catBox = document.getElementById('pred-category-box');
        const confScore = document.getElementById('pred-confidence-score');
        const modelUsed = document.getElementById('pred-model-used');

        const colors = {
            'Business': '#60a5fa',
            'Education': '#c084fc',
            'Entertainment': '#f472b6',
            'Sports': '#34d399',
            'Technology': '#22d3ee'
        };
        const catColor = colors[data.predicted_category] || '#06b6d4';

        if (catTitle) {
            catTitle.innerText = data.predicted_category;
            catTitle.style.color = catColor;
            catTitle.style.fontSize = '2.2rem';
            catTitle.style.fontWeight = '800';
            catTitle.style.letterSpacing = '0.05em';
            catTitle.style.textShadow = `0 0 15px ${catColor}80`;
        }

        if (catBox) {
            catBox.style.borderColor = catColor;
            catBox.style.backgroundColor = `${catColor}20`;
            catBox.style.boxShadow = `0 0 20px ${catColor}30`;
        }

        if (confScore) confScore.innerText = data.confidence !== null ? `${data.confidence}%` : 'N/A';
        if (modelUsed) modelUsed.innerText = data.model_used;

        const probContainer = document.getElementById('pred-probabilities-bars');
        if (probContainer) {
            probContainer.innerHTML = '';
            const probs = data.probabilities || {};
            Object.keys(probs).sort().forEach(cat => {
                const val = probs[cat];
                const barColor = colors[cat] || '#6366f1';
                const div = document.createElement('div');
                div.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="text-white fw-bold small">${cat}</span>
                        <span class="font-monospace fw-bold small" style="color: ${barColor}">${val}%</span>
                    </div>
                    <div class="progress bg-darker" style="height: 8px; border-radius: 4px;">
                        <div class="progress-bar" style="width: ${val}%; background-color: ${barColor}; box-shadow: 0 0 8px ${barColor};"></div>
                    </div>
                `;
                probContainer.appendChild(div);
            });
        }
    });
}

// ==================== SPEECH PROCESSING PAGE ====================

function initSpeechPage() {
    // 1. Audio File Upload Form Handler
    const form = document.getElementById('form-speech-upload');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('input-audio-file');
            if (!fileInput || !fileInput.files.length) {
                alert("Please select an audio file to process.");
                return;
            }

            const formData = new FormData(form);
            const spinner = document.getElementById('speech-spinner');
            if (spinner) spinner.classList.remove('d-none');

            fetch('/api/speech/transcribe', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (spinner) spinner.classList.add('d-none');
                if (!data.success) {
                    alert(data.message || "Speech processing failed.");
                    return;
                }
                renderSpeechResults(data);
            })
            .catch(err => {
                if (spinner) spinner.classList.add('d-none');
                console.error("Speech transcription error:", err);
                alert("Error communicating with speech recognition server.");
            });
        });
    }

    // 2. Microphone Live Recording Logic ("Record Now")
    const btnStartRecord = document.getElementById('btn-start-record');
    const btnStopRecord = document.getElementById('btn-stop-record');

    if (btnStartRecord && btnStopRecord) {
        btnStartRecord.addEventListener('click', startLiveRecording);
        btnStopRecord.addEventListener('click', stopLiveRecording);
    }

    // 3. Process Audio File Button Handler (Record Now Tab)
    const btnProcessRecord = document.getElementById('btn-process-record');
    if (btnProcessRecord) {
        btnProcessRecord.addEventListener('click', function() {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                stopLiveRecording();
            } else {
                sendRecordAudioToServer();
            }
        });
    }

    // 4. Clear Button Handlers
    const btnClear = document.getElementById('btn-clear-speech');
    const btnClearRecord = document.getElementById('btn-clear-record');
    const clearFn = function() {
        if (form) form.reset();
        if (document.getElementById('input-rec-ref-transcript')) {
            document.getElementById('input-rec-ref-transcript').value = '';
        }
        document.getElementById('speech-result-placeholder').classList.remove('d-none');
        document.getElementById('speech-result-container').classList.add('d-none');
        document.getElementById('btn-copy-transcript').classList.add('d-none');
        document.getElementById('info-file-name').innerText = '--';
        document.getElementById('info-file-type').innerText = '--';
        document.getElementById('info-file-size').innerText = '--';
        document.getElementById('info-duration').innerText = '--';
        document.getElementById('info-proc-time').innerText = '--';
        document.getElementById('info-status').innerHTML = '<span class="badge bg-secondary">Awaiting Input</span>';
        document.getElementById('wer-eval-container').innerHTML = '<div class="p-3 bg-darker rounded border border-dark text-center py-4"><i class="fa-solid fa-vial text-secondary fa-2x mb-2 opacity-50"></i><p class="text-secondary small m-0">Reference transcript not provided. WER/CER cannot be calculated for this input.</p></div>';
        document.getElementById('wer-eval-scores').classList.add('d-none');
        const speechClassBox = document.getElementById('speech-classification-box');
        if (speechClassBox) speechClassBox.classList.add('d-none');
    };

    if (btnClear) btnClear.addEventListener('click', clearFn);
    if (btnClearRecord) btnClearRecord.addEventListener('click', clearFn);

    // 4. Copy Transcript Button Handler
    const btnCopy = document.getElementById('btn-copy-transcript');
    if (btnCopy) {
        btnCopy.addEventListener('click', function() {
            const txt = document.getElementById('output-transcript-text').innerText;
            if (txt && txt !== '--') {
                navigator.clipboard.writeText(txt).then(() => {
                    const orig = btnCopy.innerHTML;
                    btnCopy.innerHTML = '<i class="fa-solid fa-check me-1"></i> Copied!';
                    setTimeout(() => { btnCopy.innerHTML = orig; }, 2000);
                });
            }
        });
    }
}

function startLiveRecording() {
    const btnStart = document.getElementById('btn-start-record');
    const btnStop = document.getElementById('btn-stop-record');
    const statusBox = document.getElementById('recording-status-box');
    const idleBox = document.getElementById('recording-idle-box');
    const timerDisplay = document.getElementById('record-timer');

    audioChunks = [];
    recordingStartTime = Date.now();

    // Prepare Results UI
    document.getElementById('speech-result-placeholder').classList.add('d-none');
    document.getElementById('speech-result-container').classList.remove('d-none');
    document.getElementById('live-streaming-indicator').classList.remove('d-none');
    document.getElementById('btn-copy-transcript').classList.remove('d-none');
    
    document.getElementById('info-file-name').innerText = 'Live Microphone Recording';
    document.getElementById('info-file-type').innerText = 'Audio (Microphone Input)';
    document.getElementById('info-status').innerHTML = '<span class="badge bg-danger pulse-glow"><i class="fa-solid fa-circle me-1"></i> Recording...</span>';

    // 1. Browser Speech Recognition (Live Stream Words to Transcript Column)
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        liveSpeechRecognizer = new SpeechRecognition();
        liveSpeechRecognizer.continuous = true;
        liveSpeechRecognizer.interimResults = true;
        liveSpeechRecognizer.lang = 'en-US';

        liveSpeechRecognizer.onresult = function(event) {
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                finalTranscript += event.results[i][0].transcript;
            }
            if (finalTranscript.strip !== '') {
                updateTranscriptDisplay(finalTranscript);
            }
        };

        try {
            liveSpeechRecognizer.start();
        } catch (e) {
            console.log("Speech recognition start note:", e);
        }
    }

    // 2. Browser MediaRecorder for Audio Chunks
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.ondataavailable = e => {
                    if (e.data.size > 0) audioChunks.push(e.data);
                };
                mediaRecorder.start();

                // UI Toggle
                btnStart.classList.add('d-none');
                btnStop.classList.remove('d-none');
                btnStop.removeAttribute('disabled');
                
                if (statusBox) statusBox.classList.remove('d-none');
                if (idleBox) idleBox.classList.add('d-none');

                // Timer Interval
                recordingTimerInterval = setInterval(() => {
                    const elapsedSec = Math.floor((Date.now() - recordingStartTime) / 1000);
                    const mins = String(Math.floor(elapsedSec / 60)).padStart(2, '0');
                    const secs = String(elapsedSec % 60).padStart(2, '0');
                    if (timerDisplay) timerDisplay.innerText = `${mins}:${secs}`;
                }, 1000);
            })
            .catch(err => {
                alert("Microphone permission denied or microphone unavailable: " + err);
            });
    } else {
        alert("Live microphone recording is not supported in this browser version. Please choose an audio file instead.");
    }
}

function stopLiveRecording() {
    const btnStart = document.getElementById('btn-start-record');
    const btnStop = document.getElementById('btn-stop-record');
    const statusBox = document.getElementById('recording-status-box');
    const idleBox = document.getElementById('recording-idle-box');

    if (recordingTimerInterval) clearInterval(recordingTimerInterval);
    
    if (liveSpeechRecognizer) {
        try { liveSpeechRecognizer.stop(); } catch (e) {}
    }

    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        mediaRecorder.onstop = () => {
            sendRecordAudioToServer();
        };
    } else if (audioChunks && audioChunks.length > 0) {
        sendRecordAudioToServer();
    }

    // UI Reset
    btnStop.classList.add('d-none');
    btnStart.classList.remove('d-none');
    if (statusBox) statusBox.classList.add('d-none');
    if (idleBox) idleBox.classList.remove('d-none');
}

function sendRecordAudioToServer() {
    const elapsedSec = recordingStartTime ? Math.round((Date.now() - recordingStartTime) / 1000) : 0;
    if (elapsedSec > 0) {
        document.getElementById('info-duration').innerText = `${elapsedSec} sec`;
    }

    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio', audioBlob, 'live_microphone_recording.wav');

    const refText = document.getElementById('input-rec-ref-transcript') 
        ? document.getElementById('input-rec-ref-transcript').value.trim() : '';
    if (refText) {
        formData.append('reference_text', refText);
    }

    const currentText = document.getElementById('output-transcript-text') 
        ? document.getElementById('output-transcript-text').innerText.trim() : '';
    if (currentText && currentText !== '--') {
        formData.append('live_transcript', currentText);
    }

    const spinner = document.getElementById('speech-spinner');
    if (spinner) spinner.classList.remove('d-none');

    fetch('/api/speech/transcribe', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (spinner) spinner.classList.add('d-none');
        document.getElementById('live-streaming-indicator').classList.add('d-none');
        if (data.success) {
            renderSpeechResults(data);
        }
    })
    .catch(err => {
        if (spinner) spinner.classList.add('d-none');
        document.getElementById('live-streaming-indicator').classList.add('d-none');
    });
}

function updateTranscriptDisplay(text) {
    const outText = document.getElementById('output-transcript-text');
    if (outText) outText.innerText = text;

    const words = text.split(/\s+/).filter(w => w.length > 0);
    const chars = text.length;
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);

    if (document.getElementById('stat-speech-words')) document.getElementById('stat-speech-words').innerText = words.length;
    if (document.getElementById('stat-speech-chars')) document.getElementById('stat-speech-chars').innerText = chars;
    if (document.getElementById('stat-speech-sentences')) document.getElementById('stat-speech-sentences').innerText = sentences.length;
    if (document.getElementById('output-speech-cleaned')) document.getElementById('output-speech-cleaned').innerText = text.toLowerCase().trim();
}

function renderSpeechResults(data) {
    const info = data.file_info || {};
    const metrics = data.metrics || {};
    const evalData = data.evaluation || {};

    if (data.file_info && data.file_info.file_name) {
        document.getElementById('info-file-name').innerText = info.file_name || '--';
        document.getElementById('info-file-type').innerText = info.file_type || '--';
        document.getElementById('info-file-size').innerText = info.file_size || '--';
        document.getElementById('info-duration').innerText = info.duration_seconds ? `${info.duration_seconds} sec` : (document.getElementById('info-duration').innerText !== '--' ? document.getElementById('info-duration').innerText : 'N/A');
        document.getElementById('info-proc-time').innerText = `${info.processing_time_seconds || 0.1} sec`;
    }

    const isCompleted = data.status === 'Completed' || (data.transcript && data.transcript.trim() !== '') || data.success;
    const statusBadge = isCompleted
        ? '<span class="badge bg-success"><i class="fa-solid fa-check me-1"></i> Completed</span>'
        : `<span class="badge bg-danger">${data.status || 'Error'}</span>`;
    document.getElementById('info-status').innerHTML = statusBadge;

    document.getElementById('speech-result-placeholder').classList.add('d-none');
    document.getElementById('speech-result-container').classList.remove('d-none');
    document.getElementById('btn-copy-transcript').classList.remove('d-none');

    if (data.transcript && data.transcript.trim() !== '') {
        document.getElementById('output-transcript-text').innerText = data.transcript;
        document.getElementById('stat-speech-sentences').innerText = metrics.sentence_count || 0;
        document.getElementById('stat-speech-words').innerText = metrics.word_count || 0;
        document.getElementById('stat-speech-chars').innerText = metrics.char_count || 0;
        document.getElementById('output-speech-cleaned').innerText = data.cleaned_transcript || '--';
    }

    // WER & CER Evaluation
    const evalScoresBox = document.getElementById('wer-eval-scores');
    const evalContainer = document.getElementById('wer-eval-container');

    if (evalData.reference_provided && evalData.wer !== null) {
        evalScoresBox.classList.remove('d-none');
        document.getElementById('val-wer').innerText = `${evalData.wer}%`;
        document.getElementById('val-cer').innerText = `${evalData.cer}%`;
        evalContainer.innerHTML = `<div class="p-3 bg-darker rounded border border-success text-center mb-2"><span class="badge bg-success mb-1">Reference Evaluation Active</span><small class="text-white d-block">Ground-truth reference evaluated against extracted transcript using Levenshtein distance.</small></div>`;
    } else {
        evalScoresBox.classList.add('d-none');
        evalContainer.innerHTML = `<div class="p-3 bg-darker rounded border border-dark text-center py-4"><i class="fa-solid fa-vial text-secondary fa-2x mb-2 opacity-50"></i><p class="text-secondary small m-0">${evalData.message || 'Reference transcript not provided. WER/CER cannot be calculated for this input.'}</p></div>`;
    }

    // Speech Classification Category Display
    const speechClassBox = document.getElementById('speech-classification-box');
    const categoryBadge = document.getElementById('speech-category-badge');
    const categoryConf = document.getElementById('speech-category-conf');
    const categoryModel = document.getElementById('speech-category-model');

    if (speechClassBox && data.classification && data.classification.category) {
        speechClassBox.classList.remove('d-none');
        if (categoryBadge) categoryBadge.innerText = data.classification.category;
        const rawConf = data.classification.confidence;
        const formattedConf = (rawConf > 1) ? `${Math.round(rawConf)}%` : `${Math.round(rawConf * 100)}%`;
        if (categoryConf) categoryConf.innerText = formattedConf;
        if (categoryModel) categoryModel.innerText = data.classification.model_used || 'Best Classifier';
    } else if (speechClassBox) {
        speechClassBox.classList.add('d-none');
    }
}

// ==================== MULTILINGUAL NLP PAGE ====================

function initMultilingualPage() {
    const sampleTexts = {
        'en': 'Police investigators arrived at the scene and initiated a detailed examination of the evidence.',
        'ta': 'விசாரணை அதிகாரிகள் சம்பவ இடத்திற்கு விரைந்து சென்று சோதனையில் ஈடுபட்டனர்.',
        'hi': 'पुलिस ने मामले की जांच शुरू कर दी है और मुख्य गवाह से पूछताछ की जा रही है।',
        'fr': "Les enquêteurs ont analysé les preuves trouvées sur les lieux de l'incident.",
        'es': 'Las autoridades policiales iniciaron una investigación detallada sobre los informes del caso.',
        'de': 'Die Ermittler haben die Beweise am Tatort sorgfältig analysiert und dokumentiert.'
    };

    document.querySelectorAll('.sample-multi-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const langKey = this.getAttribute('data-lang');
            const textArea = document.getElementById('input-multilingual-text');
            if (textArea && sampleTexts[langKey]) {
                textArea.value = sampleTexts[langKey];
                processMultilingualText();
            }
        });
    });

    const btnProcess = document.getElementById('btn-process-multilingual');
    if (btnProcess) {
        btnProcess.addEventListener('click', processMultilingualText);
    }

    const btnTranslate = document.getElementById('btn-translate-multilingual');
    if (btnTranslate) {
        btnTranslate.addEventListener('click', processMultilingualText);
    }

    const btnClear = document.getElementById('btn-clear-multilingual');
    if (btnClear) {
        btnClear.addEventListener('click', function() {
            const textArea = document.getElementById('input-multilingual-text');
            if (textArea) textArea.value = '';
            document.getElementById('multi-placeholder').classList.remove('d-none');
            document.getElementById('multi-results-container').classList.add('d-none');
            document.getElementById('translation-output-box').classList.add('d-none');
            document.getElementById('record-original-evidence').innerText = 'No evidence processed yet.';
            document.getElementById('record-processed-evidence').innerText = 'Awaiting detection / translation.';
        });
    }
}

function processMultilingualText() {
    const textArea = document.getElementById('input-multilingual-text');
    const text = textArea ? textArea.value.trim() : '';

    if (!text) {
        alert("Please enter multilingual text to detect and process.");
        return;
    }

    fetch('/api/multilingual/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            alert(data.message || "Multilingual processing failed.");
            return;
        }

        document.getElementById('multi-placeholder').classList.add('d-none');
        document.getElementById('multi-results-container').classList.remove('d-none');

        document.getElementById('output-detected-lang').innerText = data.detected_language;
        document.getElementById('output-lang-code').innerText = `ISO Code: ${data.language_code}`;
        document.getElementById('output-token-count').innerText = data.token_count;
        document.getElementById('output-char-count').innerText = data.char_count;
        document.getElementById('output-normalized-text').innerText = data.normalized_text;

        document.getElementById('record-original-evidence').innerText = data.original_evidence;

        // Display English Translation
        const transBox = document.getElementById('translation-output-box');
        const transText = document.getElementById('output-translated-text');
        const transStatus = document.getElementById('translation-status-msg');

        if (transBox) transBox.classList.remove('d-none');
        if (transText) transText.innerText = data.translated_text || data.original_evidence;
        if (transStatus) transStatus.innerText = "Translated to English representation successfully.";
        
        document.getElementById('record-processed-evidence').innerText = data.translated_text || data.original_evidence;
    })
    .catch(err => {
        console.error("Multilingual API error:", err);
    });
}

// ==================== SHARED FILE & IMAGE EXTRACTION JS HANDLER ====================

function setupFileUploadHandler(fileInputId, targetTextareaId, statusContainerId) {
    const fileInput = document.getElementById(fileInputId);
    const targetTextarea = document.getElementById(targetTextareaId);
    const statusContainer = document.getElementById(statusContainerId);

    if (!fileInput || !targetTextarea) return;

    fileInput.addEventListener('change', async function () {
        const files = this.files;
        if (!files || files.length === 0) return;

        // Validate 10 MB file size limit
        for (let f of files) {
            if (f.size > 10 * 1024 * 1024) {
                if (statusContainer) {
                    statusContainer.innerHTML = `<div class="alert alert-danger py-2 px-3 small m-0 mb-2"><i class="fa-solid fa-triangle-exclamation me-1"></i> File "${f.name}" exceeds 10 MB upload size limit.</div>`;
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

                targetTextarea.dispatchEvent(new Event('input'));

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

document.addEventListener('DOMContentLoaded', function () {
    // Multilingual Upload Setup
    setupFileUploadHandler('upload-multilingual-file', 'input-multilingual-text', 'multilingual-upload-status');
    setupFileUploadHandler('upload-multilingual-image', 'input-multilingual-text', 'multilingual-upload-status');

    // NER Upload Setup
    setupFileUploadHandler('upload-ner-file', 'ner-input-text', 'ner-upload-status');
    setupFileUploadHandler('upload-ner-image', 'ner-input-text', 'ner-upload-status');
});

