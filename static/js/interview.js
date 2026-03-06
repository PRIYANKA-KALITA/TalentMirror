/* global window */
(function () {
  // ----------------------------
  // Text-to-Speech (existing)
  // ----------------------------
  function canSpeak() {
    return typeof window !== "undefined" && "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
  }

  function stopTTS() {
    if (!canSpeak()) return;
    window.speechSynthesis.cancel();
  }

  function speak(text) {
    if (!canSpeak()) {
      alert("Text-to-Speech not supported in this browser. Try Chrome/Edge.");
      return;
    }
    stopTTS();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 1.0;
    utter.pitch = 1.0;
    utter.volume = 1.0;
    window.speechSynthesis.speak(utter);
  }

  window.TalentMirrorTTS = { speak, stop: stopTTS };

  // ----------------------------
  // Speech-to-Text (FIXED)
  // ----------------------------
  function getRecognitionCtor() {
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
  }

  let recognition = null;
  let isRecording = false;

  // Stores what was in the textarea before dictation started
  let prefixText = "";

  function getAnswerBox() {
    return (
      document.getElementById("answerBox") ||
      document.querySelector('textarea[name="answer"]') ||
      document.querySelector("textarea")
    );
  }

  function setMicUI(recording, statusText) {
    const micBtn = document.getElementById("micBtn");
    const micStopBtn = document.getElementById("micStopBtn");
    const micStatus = document.getElementById("micStatus");

    if (micBtn) micBtn.disabled = recording;
    if (micStopBtn) micStopBtn.disabled = !recording;
    if (micStatus && statusText) micStatus.textContent = statusText;
  }

  function initSpeechToText() {
    const Ctor = getRecognitionCtor();
    if (!Ctor) {
      setMicUI(false, "Mic dictation not supported in this browser. Try Chrome/Edge over HTTPS.");
      const micBtn = document.getElementById("micBtn");
      const micStopBtn = document.getElementById("micStopBtn");
      if (micBtn) micBtn.disabled = true;
      if (micStopBtn) micStopBtn.disabled = true;
      return;
    }

    recognition = new Ctor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      isRecording = true;
      const answerBox = getAnswerBox();

      // Capture prefix ONCE so we never re-append repeatedly
      prefixText = (answerBox?.value || "").trim();
      setMicUI(true, "🎙️ Listening... Speak clearly. (Stop Mic when done)");
    };

    recognition.onerror = (e) => {
      isRecording = false;
      setMicUI(false, `Mic error: ${e.error}. Allow mic permission and retry.`);
    };

    recognition.onend = () => {
      isRecording = false;

      // Update prefix to whatever is currently in the textarea after dictation ends
      const answerBox = getAnswerBox();
      prefixText = (answerBox?.value || "").trim();

      setMicUI(false, "Mic stopped. You can edit the text or start mic again.");
    };

    recognition.onresult = (event) => {
      const answerBox = getAnswerBox();
      if (!answerBox) return;

      // Reconstruct transcript from ALL results to avoid duplicates
      let finalText = "";
      let interimText = "";

      for (let i = 0; i < event.results.length; i++) {
        const res = event.results[i];
        const txt = res[0].transcript;
        if (res.isFinal) finalText += txt + " ";
        else interimText += txt;
      }

      const spacer = prefixText.length > 0 ? " " : "";
      answerBox.value = (prefixText + spacer + (finalText + interimText).trim()).trim();
      answerBox.focus();
    };
  }

  function startMic() {
    if (!recognition) initSpeechToText();
    if (!recognition) return;
    if (isRecording) return;

    try {
      recognition.start();
    } catch (e) {
      setMicUI(false, "Could not start mic. Try stopping and starting again.");
    }
  }

  function stopMic() {
    if (!recognition || !isRecording) return;
    try {
      recognition.stop();
    } catch (e) {
      // ignore
    }
  }

  // ----------------------------
  // Wire up buttons
  // ----------------------------
  window.addEventListener("load", () => {
    // TTS
    const speakBtn = document.getElementById("speakBtn");
    const stopBtn = document.getElementById("stopBtn");
    const qEl = document.getElementById("questionText");

    if (speakBtn && qEl) speakBtn.addEventListener("click", () => speak(qEl.innerText));
    if (stopBtn) stopBtn.addEventListener("click", stopTTS);

    // Mic
    initSpeechToText();
    const micBtn = document.getElementById("micBtn");
    const micStopBtn = document.getElementById("micStopBtn");

    if (micBtn) micBtn.addEventListener("click", startMic);
    if (micStopBtn) micStopBtn.addEventListener("click", stopMic);
  });
})();