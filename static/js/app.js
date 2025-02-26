/**
 * Record en Transcribe App - Frontend JavaScript
 * 
 * Dit script regelt de interactie met de web interface van de applicatie.
 * Het maakt verbinding met de backend API voor het beheren van opnames en transcripties.
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM elementen ophalen
    const microphoneSelect = document.getElementById('microphone-select');
    const languageSelect = document.getElementById('language-select');
    const startRecordingBtn = document.getElementById('start-recording');
    const stopRecordingBtn = document.getElementById('stop-recording');
    const recordingStatus = document.getElementById('recording-status');
    const recordingIndicator = document.getElementById('recording-indicator');
    const recordingTimer = document.getElementById('recording-timer');
    const transcribeRecordingBtn = document.getElementById('transcribe-recording');
    const uploadAudio = document.getElementById('upload-audio');
    const uploadProgress = document.getElementById('upload-progress');
    const uploadProgressBar = uploadProgress.querySelector('.progress-bar');
    const uploadFormats = document.getElementById('upload-formats');
    const transcribeUploadBtn = document.getElementById('transcribe-upload');
    const transcriptionResult = document.getElementById('transcription-result');
    const transcriptionProgress = document.getElementById('transcription-progress');
    const downloadAudioBtn = document.getElementById('download-audio');
    const downloadTranscriptionBtn = document.getElementById('download-transcription');
    const previewAudioBtn = document.getElementById('preview-audio');
    const notificationArea = document.getElementById('notification-area');
    const audioPlayer = document.getElementById('audio-player');
    const audioSource = document.getElementById('audio-source');
    const audioFilename = document.getElementById('audio-filename');
    const audioPlayerModal = new bootstrap.Modal(document.getElementById('audio-player-modal'));
    const queueModal = new bootstrap.Modal(document.getElementById('queue-modal'));
    const queueTableBody = document.getElementById('queue-table-body');
    const processAllQueueBtn = document.getElementById('process-all-queue');
    
    // Status variabelen
    let isRecording = false;
    let currentAudioFile = null;
    let currentTranscription = null;
    let recordingStartTime = null;
    let recordingTimerInterval = null;
    let uploadQueue = [];
    let supportedFormats = [];
    
    // Functie voor het weergeven van notificaties
    function showNotification(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        toast.classList.add('toast', 'custom-toast', 'show', `toast-${type}`);
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        const iconMap = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle'
        };
        
        toast.innerHTML = `
            <div class="toast-header">
                <i class="${iconMap[type]} me-2"></i>
                <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Sluiten"></button>
            </div>
            <div class="toast-body">${message}</div>
        `;
        
        notificationArea.appendChild(toast);
        
        // Toast automatisch laten verdwijnen
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode === notificationArea) {
                    notificationArea.removeChild(toast);
                }
            }, 500);
        }, duration);
        
        // Sluit-knop functionaliteit
        const closeBtn = toast.querySelector('.btn-close');
        closeBtn.addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode === notificationArea) {
                    notificationArea.removeChild(toast);
                }
            }, 500);
        });
    }
    
    // Functie om timer te updaten
    function updateRecordingTimer() {
        if (!recordingStartTime) return;
        
        const now = new Date();
        const diff = now - recordingStartTime;
        const seconds = Math.floor(diff / 1000) % 60;
        const minutes = Math.floor(diff / 60000);
        
        recordingTimer.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    
    // Functie om beschikbare microfoons op te halen
    async function loadMicrophones() {
        try {
            const response = await fetch('/api/devices');
            const data = await response.json();
            
            if (data.devices) {
                microphoneSelect.innerHTML = '<option value="">Selecteer een microfoon...</option>';
                
                data.devices.forEach(device => {
                    const option = document.createElement('option');
                    option.value = device.id;
                    option.textContent = device.name;
                    microphoneSelect.appendChild(option);
                });
                
                showNotification(`${data.devices.length} microfoons gevonden`, 'info');
            }
        } catch (error) {
            console.error('Fout bij het ophalen van microfoons:', error);
            showNotification('Kon geen microfoons laden.', 'error');
        }
    }
    
    // Functie om ondersteunde talen op te halen
    async function loadLanguages() {
        try {
            const response = await fetch('/api/languages');
            const data = await response.json();
            
            if (data.languages) {
                languageSelect.innerHTML = '';
                
                Object.entries(data.languages).forEach(([code, name]) => {
                    const option = document.createElement('option');
                    option.value = code;
                    option.textContent = name;
                    languageSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Fout bij het ophalen van talen:', error);
            // Standaardtalen blijven behouden als fallback
        }
    }
    
    // Functie om ondersteunde audioformaten op te halen
    async function loadAudioFormats() {
        try {
            const response = await fetch('/api/formats');
            const data = await response.json();
            
            if (data.formats) {
                supportedFormats = data.formats;
                
                // Update acceptattributen voor het upload element
                const acceptFormats = supportedFormats.join(',');
                uploadAudio.setAttribute('accept', acceptFormats);
                
                // Update het helptekst element
                const formatsText = supportedFormats.map(format => format.toUpperCase().replace('.', '')).join(', ');
                uploadFormats.textContent = `Ondersteunde formaten: ${formatsText} (max. ${data.max_size_formatted})`;
            }
        } catch (error) {
            console.error('Fout bij het ophalen van audioformaten:', error);
            // Standaardformaten blijven behouden als fallback
        }
    }
    
    // Functie om opname te starten
    async function startRecording() {
        const deviceId = microphoneSelect.value;
        
        if (!deviceId) {
            showNotification('Selecteer eerst een microfoon.', 'warning');
            return;
        }
        
        try {
            // Toon bezig-status
            startRecordingBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Bezig...';
            startRecordingBtn.disabled = true;
            
            const response = await fetch('/api/record/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ device_id: parseInt(deviceId) })
            });
            
            const data = await response.json();
            
            if (data.status === 'recording') {
                isRecording = true;
                recordingStatus.textContent = 'Opname bezig...';
                
                // Visuele feedback
                recordingIndicator.classList.remove('d-none');
                recordingTimer.classList.remove('d-none');
                
                // Start timer
                recordingStartTime = new Date();
                recordingTimerInterval = setInterval(updateRecordingTimer, 1000);
                updateRecordingTimer();
                
                startRecordingBtn.innerHTML = '<i class="fas fa-play me-2"></i>Start opname';
                startRecordingBtn.disabled = true;
                stopRecordingBtn.disabled = false;
                microphoneSelect.disabled = true;
                
                showNotification('Opname gestart', 'success');
            } else {
                startRecordingBtn.innerHTML = '<i class="fas fa-play me-2"></i>Start opname';
                startRecordingBtn.disabled = false;
                showNotification(`Kon opname niet starten: ${data.error || 'Onbekende fout'}`, 'error');
            }
        } catch (error) {
            console.error('Fout bij het starten van opname:', error);
            startRecordingBtn.innerHTML = '<i class="fas fa-play me-2"></i>Start opname';
            startRecordingBtn.disabled = false;
            showNotification('Kon opname niet starten door een serverfout.', 'error');
        }
    }
    
    // Functie om opname te stoppen
    async function stopRecording() {
        if (!isRecording) return;
        
        try {
            // Toon bezig-status
            stopRecordingBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Bezig...';
            stopRecordingBtn.disabled = true;
            
            const response = await fetch('/api/record/stop', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.status === 'stopped') {
                isRecording = false;
                recordingStatus.textContent = 'Opname gestopt';
                
                // Stop visuele feedback
                recordingIndicator.classList.add('d-none');
                
                // Stop timer
                clearInterval(recordingTimerInterval);
                recordingTimerInterval = null;
                
                stopRecordingBtn.innerHTML = '<i class="fas fa-stop me-2"></i>Stop opname';
                startRecordingBtn.disabled = false;
                stopRecordingBtn.disabled = true;
                microphoneSelect.disabled = false;
                transcribeRecordingBtn.disabled = false;
                
                currentAudioFile = data.file_path;
                downloadAudioBtn.disabled = false;
                previewAudioBtn.disabled = false;
                
                showNotification(`Opname succesvol gestopt (${Math.round(data.file_size / 1024)} KB)`, 'success');
                
                // Vraag of gebruiker wil transcriberen met modale dialoog of toast
                if (confirm('Wil je de opname transcriberen?')) {
                    transcribeAudio(currentAudioFile);
                }
            } else {
                stopRecordingBtn.innerHTML = '<i class="fas fa-stop me-2"></i>Stop opname';
                stopRecordingBtn.disabled = false;
                showNotification(`Kon opname niet stoppen: ${data.error || 'Onbekende fout'}`, 'error');
            }
        } catch (error) {
            console.error('Fout bij het stoppen van opname:', error);
            stopRecordingBtn.innerHTML = '<i class="fas fa-stop me-2"></i>Stop opname';
            stopRecordingBtn.disabled = false;
            showNotification('Kon opname niet stoppen door een serverfout.', 'error');
        }
    }
    
    // Functie om audio te transcriberen
    async function transcribeAudio(audioFile, language = null) {
        if (!audioFile) {
            showNotification('Geen audiobestand opgegeven om te transcriberen.', 'warning');
            return;
        }
        
        try {
            // Toon voortgangsindicator
            transcriptionProgress.classList.remove('d-none');
            transcriptionResult.innerHTML = '<p class="text-muted">Bezig met transcriberen...</p>';
            
            // Gebruik geselecteerde taal als die is opgegeven
            if (!language) {
                language = languageSelect.value;
            }
            
            const response = await fetch('/api/transcribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ audio_file: audioFile, language: language })
            });
            
            const data = await response.json();
            
            // Verberg voortgangsindicator
            transcriptionProgress.classList.add('d-none');
            
            if (data.text) {
                transcriptionResult.innerHTML = `<p>${data.text}</p>`;
                currentTranscription = data.file_path;
                downloadTranscriptionBtn.disabled = false;
                
                showNotification('Transcriptie succesvol voltooid', 'success');
            } else if (data.warning) {
                transcriptionResult.innerHTML = `<p class="text-warning">${data.text}</p>`;
                showNotification(data.warning, 'warning');
            } else {
                transcriptionResult.innerHTML = '<p class="text-danger">Transcriptie mislukt.</p>';
                showNotification(`Kon audio niet transcriberen: ${data.error || 'Onbekende fout'}`, 'error');
            }
        } catch (error) {
            console.error('Fout bij het transcriberen:', error);
            transcriptionProgress.classList.add('d-none');
            transcriptionResult.innerHTML = '<p class="text-danger">Transcriptie mislukt door een serverfout.</p>';
            showNotification('Kon audio niet transcriberen door een serverfout.', 'error');
        }
    }
    
    // Functie om bestand te uploaden
    async function uploadAudioFile(file) {
        try {
            // Toon upload voortgang
            uploadProgress.classList.remove('d-none');
            uploadProgressBar.style.width = '0%';
            transcribeUploadBtn.disabled = true;
            
            // Maak een FormData object voor het uploaden
            const formData = new FormData();
            formData.append('audio_file', file);
            
            // Implementeer upload met voortgangsindicatie
            const xhr = new XMLHttpRequest();
            
            // Voortgangsevent
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const percentComplete = Math.round((event.loaded / event.total) * 100);
                    uploadProgressBar.style.width = percentComplete + '%';
                    uploadProgressBar.setAttribute('aria-valuenow', percentComplete);
                }
            });
            
            // Promise om XHR request af te handelen
            const uploadPromise = new Promise((resolve, reject) => {
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4) {
                        if (xhr.status === 200) {
                            resolve(JSON.parse(xhr.responseText));
                        } else {
                            let errorData = {
                                error: 'Fout bij uploaden',
                                details: 'Onbekende fout'
                            };
                            
                            try {
                                errorData = JSON.parse(xhr.responseText);
                            } catch (e) {
                                // Als het niet als JSON kan worden geparsed, gebruik defaultwaarden
                            }
                            
                            reject(errorData);
                        }
                    }
                };
            });
            
            // Open en verstuur het request
            xhr.open('POST', '/api/upload', true);
            xhr.send(formData);
            
            // Wacht op resultaat
            const data = await uploadPromise;
            
            // Update UI na succesvolle upload
            uploadProgress.classList.add('d-none');
            
            currentAudioFile = data.file_path;
            downloadAudioBtn.disabled = false;
            previewAudioBtn.disabled = false;
            
            // Toon bestandsnaam en grootte
            const fileSizeKB = Math.round(data.file_size / 1024);
            showNotification(`Bestand "${data.filename}" succesvol geüpload (${fileSizeKB} KB)`, 'success');
            
            // Vraag of gebruiker wil transcriberen
            if (confirm('Wil je het geüploade bestand transcriberen?')) {
                transcribeAudio(currentAudioFile);
            }
            
            return data;
            
        } catch (error) {
            // Bij fouten, herstel UI
            uploadProgress.classList.add('d-none');
            console.error('Fout bij uploaden van audio:', error);
            showNotification(`Kon bestand niet uploaden: ${error.details || error.error || 'Onbekende fout'}`, 'error');
            throw error;
        }
    }
    
    // Functie om bestand toe te voegen aan wachtrij
    function addToQueue(file) {
        const fileId = 'file-' + Date.now() + '-' + Math.floor(Math.random() * 1000);
        
        const queueItem = {
            id: fileId,
            file: file,
            status: 'pending', // pending, uploading, transcribing, completed, error
            error: null,
            filePath: null
        };
        
        uploadQueue.push(queueItem);
        
        // Update wachtrij UI
        updateQueueTable();
        
        return fileId;
    }
    
    // Functie om wachtrij tabel bij te werken
    function updateQueueTable() {
        queueTableBody.innerHTML = '';
        
        if (uploadQueue.length === 0) {
            queueTableBody.innerHTML = '<tr><td colspan="4" class="text-center">Geen bestanden in de wachtrij</td></tr>';
            return;
        }
        
        uploadQueue.forEach(item => {
            const row = document.createElement('tr');
            
            // Status klasse bepalen
            let statusClass = '';
            let statusText = '';
            
            switch (item.status) {
                case 'pending':
                    statusClass = 'text-secondary';
                    statusText = 'Wachtend';
                    break;
                case 'uploading':
                    statusClass = 'text-primary';
                    statusText = 'Uploaden...';
                    break;
                case 'transcribing':
                    statusClass = 'text-info';
                    statusText = 'Transcriberen...';
                    break;
                case 'completed':
                    statusClass = 'text-success';
                    statusText = 'Voltooid';
                    break;
                case 'error':
                    statusClass = 'text-danger';
                    statusText = `Fout: ${item.error || 'Onbekende fout'}`;
                    break;
            }
            
            // Bestandsgrootte
            const fileSize = item.file.size / 1024; // KB
            const fileSizeText = fileSize < 1024 
                ? `${Math.round(fileSize)} KB` 
                : `${(fileSize / 1024).toFixed(2)} MB`;
            
            // Rij opbouwen
            row.innerHTML = `
                <td>${item.file.name}</td>
                <td>${fileSizeText}</td>
                <td class="${statusClass}">${statusText}</td>
                <td>
                    ${item.status === 'pending' ? '<button class="btn btn-sm btn-primary process-queue-item">Verwerken</button>' : ''}
                    ${item.status === 'error' ? '<button class="btn btn-sm btn-warning retry-queue-item">Opnieuw</button>' : ''}
                    ${item.status === 'completed' ? '<button class="btn btn-sm btn-info preview-queue-item">Afspelen</button>' : ''}
                    <button class="btn btn-sm btn-danger remove-queue-item">Verwijderen</button>
                </td>
            `;
            
            // Event listeners toevoegen
            const processBtn = row.querySelector('.process-queue-item');
            if (processBtn) {
                processBtn.addEventListener('click', () => processQueueItem(item.id));
            }
            
            const retryBtn = row.querySelector('.retry-queue-item');
            if (retryBtn) {
                retryBtn.addEventListener('click', () => processQueueItem(item.id));
            }
            
            const previewBtn = row.querySelector('.preview-queue-item');
            if (previewBtn) {
                previewBtn.addEventListener('click', () => previewQueueItem(item.id));
            }
            
            const removeBtn = row.querySelector('.remove-queue-item');
            if (removeBtn) {
                removeBtn.addEventListener('click', () => removeFromQueue(item.id));
            }
            
            queueTableBody.appendChild(row);
        });
    }
    
    // Functie om een item uit de wachtrij te verwerken
    async function processQueueItem(id) {
        const itemIndex = uploadQueue.findIndex(item => item.id === id);
        if (itemIndex === -1) return;
        
        const item = uploadQueue[itemIndex];
        
        // Status bijwerken
        item.status = 'uploading';
        updateQueueTable();
        
        try {
            // Uploaden
            const uploadResult = await uploadAudioFile(item.file);
            item.filePath = uploadResult.file_path;
            
            // Transcriberen
            item.status = 'transcribing';
            updateQueueTable();
            
            await transcribeAudio(item.filePath);
            
            // Voltooid
            item.status = 'completed';
            updateQueueTable();
            
        } catch (error) {
            // Fout
            item.status = 'error';
            item.error = error.details || error.error || 'Onbekende fout';
            updateQueueTable();
        }
    }
    
    // Functie om alle items in de wachtrij te verwerken
    async function processAllQueueItems() {
        const pendingItems = uploadQueue.filter(item => item.status === 'pending' || item.status === 'error');
        
        if (pendingItems.length === 0) {
            showNotification('Geen wachtende bestanden om te verwerken', 'info');
            return;
        }
        
        for (const item of pendingItems) {
            await processQueueItem(item.id);
        }
        
        showNotification('Alle bestanden verwerkt', 'success');
    }
    
    // Functie om een audio item uit de wachtrij af te spelen
    function previewQueueItem(id) {
        const item = uploadQueue.find(item => item.id === id);
        if (!item || !item.filePath) return;
        
        playAudio(item.filePath, item.file.name);
    }
    
    // Functie om een item uit de wachtrij te verwijderen
    function removeFromQueue(id) {
        const itemIndex = uploadQueue.findIndex(item => item.id === id);
        if (itemIndex === -1) return;
        
        uploadQueue.splice(itemIndex, 1);
        updateQueueTable();
    }
    
    // Functie om audio af te spelen
    function playAudio(filePath, fileName) {
        // Update de audiospeler bron
        audioSource.src = filePath;
        audioPlayer.load();
        
        // Update de bestandsnaam
        audioFilename.textContent = fileName || 'Audio';
        
        // Toon de modal
        audioPlayerModal.show();
        
        // Start het afspelen als de audio geladen is
        audioPlayer.addEventListener('canplay', () => {
            audioPlayer.play();
        }, { once: true });
    }
    
    // Functie om bestand te downloaden
    function downloadFile(filePath, fileType) {
        if (!filePath) {
            showNotification(`Geen ${fileType} bestand beschikbaar om te downloaden.`, 'warning');
            return;
        }
        
        const link = document.createElement('a');
        link.href = filePath;
        link.download = filePath.split('/').pop();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification(`${fileType.charAt(0).toUpperCase() + fileType.slice(1)} is gedownload`, 'success');
    }
    
    // Functie om een geüpload audiobestand te verwerken
    function handleFileUpload(event) {
        const files = event.target.files;
        if (!files || files.length === 0) {
            transcribeUploadBtn.disabled = true;
            return;
        }
        
        // Voor meerdere bestanden, gebruik de wachtrij
        if (files.length > 1) {
            for (let i = 0; i < files.length; i++) {
                addToQueue(files[i]);
            }
            
            uploadAudio.value = ''; // Reset het upload veld
            showNotification(`${files.length} bestanden toegevoegd aan de wachtrij`, 'info');
            queueModal.show();
            return;
        }
        
        const file = files[0];
        
        // Controleer of het formaat wordt ondersteund
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        if (!supportedFormats.includes(fileExt) && supportedFormats.length > 0) {
            showNotification(`Niet-ondersteund bestandsformaat: ${fileExt}. Ondersteunde formaten: ${supportedFormats.join(', ')}`, 'warning');
            transcribeUploadBtn.disabled = true;
            uploadAudio.value = '';
            return;
        }
        
        transcribeUploadBtn.disabled = false;
        showNotification(`Bestand "${file.name}" geselecteerd (${Math.round(file.size / 1024)} KB)`, 'info');
    }
    
    // Event listeners
    startRecordingBtn.addEventListener('click', startRecording);
    stopRecordingBtn.addEventListener('click', stopRecording);
    
    transcribeRecordingBtn.addEventListener('click', function() {
        if (currentAudioFile) {
            transcribeAudio(currentAudioFile);
        } else {
            showNotification('Geen opname beschikbaar om te transcriberen.', 'warning');
        }
    });
    
    uploadAudio.addEventListener('change', handleFileUpload);
    
    transcribeUploadBtn.addEventListener('click', function() {
        if (uploadAudio.files.length > 0) {
            uploadAudioFile(uploadAudio.files[0]);
        } else {
            showNotification('Selecteer eerst een audiobestand om te uploaden.', 'warning');
        }
    });
    
    downloadAudioBtn.addEventListener('click', function() {
        downloadFile(currentAudioFile, 'audio');
    });
    
    downloadTranscriptionBtn.addEventListener('click', function() {
        downloadFile(currentTranscription, 'tekst');
    });
    
    previewAudioBtn.addEventListener('click', function() {
        if (currentAudioFile) {
            // Bepaal bestandsnaam uit het pad
            const fileName = currentAudioFile.split('/').pop();
            playAudio(currentAudioFile, fileName);
        } else {
            showNotification('Geen audiobestand beschikbaar om af te spelen.', 'warning');
        }
    });
    
    processAllQueueBtn.addEventListener('click', processAllQueueItems);
    
    // Audiospeler event
    audioPlayer.addEventListener('ended', function() {
        showNotification('Audio afspelen voltooid', 'info');
    });
    
    // Validatie op form inputs
    microphoneSelect.addEventListener('change', function() {
        if (this.value) {
            startRecordingBtn.disabled = false;
        } else {
            startRecordingBtn.disabled = true;
        }
    });
    
    // Initialisatie
    loadMicrophones();
    loadLanguages();
    loadAudioFormats();
    
    // Initiële UI state
    startRecordingBtn.disabled = true;
    stopRecordingBtn.disabled = true;
    transcribeRecordingBtn.disabled = true;
    transcribeUploadBtn.disabled = true;
    downloadAudioBtn.disabled = true;
    downloadTranscriptionBtn.disabled = true;
    previewAudioBtn.disabled = true;
});
