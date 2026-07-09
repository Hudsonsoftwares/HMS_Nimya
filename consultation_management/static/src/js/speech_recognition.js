/** @odoo-module **/

let recognition = null;
let finalTranscript = "";

function getSpeechRecognition() {
    if (recognition) return recognition;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return null;

    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
        let interimTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript + " ";
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }
        
        const textarea = document.querySelector('[name="raw_transcript"] textarea') || document.querySelector('textarea[name="raw_transcript"]');
        if (textarea) {
            textarea.value = finalTranscript + interimTranscript;
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            textarea.dispatchEvent(new Event('change', { bubbles: true }));
        }
    };

    recognition.onspeechstart = () => {
        const statusDiv = document.getElementById('rec_status');
        if (statusDiv) {
            statusDiv.innerHTML = "🔊 Voice detected! Recording...";
            statusDiv.style.color = "#16a34a";
        }
    };

    recognition.onspeechend = () => {
        const statusDiv = document.getElementById('rec_status');
        if (statusDiv) {
            statusDiv.innerHTML = "🎙️ Listening (Speak now)...";
            statusDiv.style.color = "#ea580c";
        }
    };

    recognition.onend = () => {
        const startBtn = document.getElementById('btn_start_rec');
        const stopBtn = document.getElementById('btn_stop_rec');
        const statusDiv = document.getElementById('rec_status');
        
        if (statusDiv) {
            statusDiv.innerHTML = "✅ Finished recording. Review transcript below.";
            statusDiv.style.color = "#16a34a";
        }
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
    };

    recognition.onerror = (event) => {
        console.error("Speech Error:", event.error);
        const startBtn = document.getElementById('btn_start_rec');
        const stopBtn = document.getElementById('btn_stop_rec');
        const statusDiv = document.getElementById('rec_status');
        
        if (statusDiv) {
            if (event.error === 'not-allowed') {
                statusDiv.innerHTML = "❌ Microphone access blocked! Allow microphone access in your browser settings/address bar.";
            } else if (event.error === 'no-speech') {
                statusDiv.innerHTML = "⚠️ No speech detected. Speak louder or check mic.";
            } else {
                statusDiv.innerHTML = "❌ Error: " + event.error;
            }
            statusDiv.style.color = "#dc2626";
        }
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
    };

    return recognition;
}

document.addEventListener('click', function(event) {
    if (event.target && event.target.id === 'btn_start_rec') {
        event.preventDefault();
        
        const startBtn = document.getElementById('btn_start_rec');
        const stopBtn = document.getElementById('btn_stop_rec');
        const statusDiv = document.getElementById('rec_status');
        
        const rec = getSpeechRecognition();
        if (!rec) {
            if (statusDiv) statusDiv.innerHTML = "❌ Error: Speech recognition not supported in this browser.";
            return;
        }

        finalTranscript = "";
        
        const langSelect = document.querySelector('[name="speech_language"] select') || document.querySelector('select[id*="speech_language"]');
        const chosenLang = langSelect ? langSelect.value : 'ar-SA';
        rec.lang = chosenLang;

        try {
            rec.start();
            if (statusDiv) {
                statusDiv.innerHTML = "🎙️ Listening... Please speak clearly in " + (chosenLang.startsWith('ar') ? 'Arabic' : 'English') + ".";
                statusDiv.style.color = "#ea580c";
            }
            if (startBtn) startBtn.disabled = true;
            if (stopBtn) stopBtn.disabled = false;
        } catch (e) {
            if (statusDiv) {
                statusDiv.innerHTML = "❌ Error starting mic: " + e.message;
                statusDiv.style.color = "#dc2626";
            }
        }
    }
    
    if (event.target && event.target.id === 'btn_stop_rec') {
        event.preventDefault();
        
        const startBtn = document.getElementById('btn_start_rec');
        const stopBtn = document.getElementById('btn_stop_rec');
        const statusDiv = document.getElementById('rec_status');
        
        const rec = getSpeechRecognition();
        if (rec) {
            rec.stop();
            if (statusDiv) {
                statusDiv.innerHTML = "Status: Processing transcript...";
                statusDiv.style.color = "#0284c7";
            }
            if (startBtn) startBtn.disabled = false;
            if (stopBtn) stopBtn.disabled = true;
        }
    }
});
