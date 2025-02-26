/**
 * Record en Transcribe App - Frontend JavaScript
 * 
 * Dit script regelt de interactie met de web interface van de applicatie.
 * Het maakt verbinding met de backend API voor het beheren van opnames en transcripties.
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM elementen ophalen
    const microphoneSelect = document.getElementById('microphone-select');
    const startRecordingBtn = document.getElementById('start-recording');
    const stopRecordingBtn = document.getElementById('stop-recording');
    const recordingStatus = document.getElementById('recording-status');
    const transcribeRecordingBtn = document.getElementById('transcribe-recording');
    const uploadAudio = document.getElementById('upload-audio');
    const transcribeUploadBtn = document.getElementById('transcribe-upload');
    const transcriptionResult = document.getElementById('transcription-result');
    const downloadAudioBtn = document.getElementById('download-audio');
    const downloadTranscriptionBtn = document.getElementById('download-transcription');
    
    // Status variabelen
    let isRecording = false;
    let currentAudioFile = null;
    let currentTranscription = null;
    
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
            }
        } catch (error) {
            console.error('Fout bij het ophalen van microfoons:', error);
            alert('Kon geen microfoons laden. Controleer de console voor details.');
        }
    }
    
    // Functie om opname te starten
    async function startRecording() {
        const deviceId = microphoneSelect.value;
        
        if (!deviceId) {
            alert('Selecteer eerst een microfoon.');
            return;
        }
        
        try {
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
                recordingStatus.style.color = '#ea4335';
                
                startRecordingBtn.disabled = true;
                stopRecordingBtn.disabled = false;
                microphoneSelect.disabled = true;
            } else {
                alert('Kon opname niet starten: ' + (data.error || 'Onbekende fout'));
            }
        } catch (error) {
            console.error('Fout bij het starten van opname:', error);
            alert('Kon opname niet starten. Controleer de console voor details.');
        }
    }
    
    // Functie om opname te stoppen
    async function stopRecording() {
        if (!isRecording) return;
        
        try {
            const response = await fetch('/api/record/stop', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.status === 'stopped') {
                isRecording = false;
                recordingStatus.textContent = 'Opname gestopt.';
                recordingStatus.style.color = '#34a853';
                
                startRecordingBtn.disabled = false;
                stopRecordingBtn.disabled = true;
                microphoneSelect.disabled = false;
                transcribeRecordingBtn.disabled = false;
                
                currentAudioFile = data.file_path;
                downloadAudioBtn.disabled = false;
                
                if (confirm('Wil je de opname transcriberen?')) {
                    transcribeAudio(currentAudioFile);
                }
            } else {
                alert('Kon opname niet stoppen: ' + (data.error || 'Onbekende fout'));
            }
        } catch (error) {
            console.error('Fout bij het stoppen van opname:', error);
            alert('Kon opname niet stoppen. Controleer de console voor details.');
        }
    }
    
    // Functie om audio te transcriberen
    async function transcribeAudio(audioFile) {
        if (!audioFile) return;
        
        try {
            const response = await fetch('/api/transcribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ audio_file: audioFile })
            });
            
            const data = await response.json();
            
            if (data.text) {
                transcriptionResult.innerHTML = `<p>${data.text}</p>`;
                currentTranscription = data.file_path;
                downloadTranscriptionBtn.disabled = false;
            } else {
                alert('Kon audio niet transcriberen: ' + (data.error || 'Onbekende fout'));
            }
        } catch (error) {
            console.error('Fout bij het transcriberen:', error);
            alert('Kon audio niet transcriberen. Controleer de console voor details.');
        }
    }
    
    // Functie om bestand te downloaden
    function downloadFile(filePath, fileType) {
        if (!filePath) return;
        
        const link = document.createElement('a');
        link.href = filePath;
        link.download = filePath.split('/').pop();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    // Event listeners
    startRecordingBtn.addEventListener('click', startRecording);
    stopRecordingBtn.addEventListener('click', stopRecording);
    
    transcribeRecordingBtn.addEventListener('click', function() {
        if (currentAudioFile) {
            transcribeAudio(currentAudioFile);
        } else {
            alert('Geen opname beschikbaar om te transcriberen.');
        }
    });
    
    uploadAudio.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            // TODO: Implementeer het uploaden van een audiobestand
            // Voor nu stellen we een placeholder in
            currentAudioFile = file.name;
            transcribeUploadBtn.disabled = false;
        }
    });
    
    transcribeUploadBtn.addEventListener('click', function() {
        if (uploadAudio.files.length > 0) {
            const formData = new FormData();
            formData.append('audio', uploadAudio.files[0]);
            
            // TODO: Implementeer het uploaden en transcriberen van een audiobestand
            alert('Upload en transcriptie functionaliteit is nog niet geïmplementeerd.');
        } else {
            alert('Selecteer eerst een audiobestand om te uploaden.');
        }
    });
    
    downloadAudioBtn.addEventListener('click', function() {
        downloadFile(currentAudioFile, 'audio');
    });
    
    downloadTranscriptionBtn.addEventListener('click', function() {
        downloadFile(currentTranscription, 'text');
    });
    
    // Laad beschikbare microfoons bij opstart
    loadMicrophones();
});
