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
    const transcribeUploadBtn = document.getElementById('transcribe-upload');
    const transcriptionResult = document.getElementById('transcription-result');
    const transcriptionProgress = document.getElementById('transcription-progress');
    const downloadAudioBtn = document.getElementById('download-audio');
    const downloadTranscriptionBtn = document.getElementById('download-transcription');
    const notificationArea = document.getElementById('notification-area');
    
    // Status variabelen
    let isRecording = false;
    let currentAudioFile = null;
    let currentTranscription = null;
    let recordingStartTime = null;
    let recordingTimerInterval = null;
    
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
                notificationArea.removeChild(toast);
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
        const file = event.target.files[0];
        if (!file) {
            transcribeUploadBtn.disabled = true;
            return;
        }
        
        // Controleer of het een WAV-bestand is
        if (file.type !== 'audio/wav' && !file.name.toLowerCase().endsWith('.wav')) {
            showNotification('Alleen WAV-bestanden worden ondersteund.', 'warning');
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
            const formData = new FormData();
            formData.append('audio', uploadAudio.files[0]);
            
            // TODO: Implementeer het uploaden en transcriberen van een audiobestand
            showNotification('Upload en transcriptie functionaliteit is nog niet geïmplementeerd.', 'info');
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
    
    // Initiële UI state
    startRecordingBtn.disabled = true;
    stopRecordingBtn.disabled = true;
    transcribeRecordingBtn.disabled = true;
    transcribeUploadBtn.disabled = true;
    downloadAudioBtn.disabled = true;
    downloadTranscriptionBtn.disabled = true;
});
