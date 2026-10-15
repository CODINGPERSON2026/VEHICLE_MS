/**
 * ============================================================================
 * SMART RFID + ANPR VEHICLE GATE SYSTEM - CLIENT APPLICATION LOGIC
 * ============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
  stopAllAudio();
  initClock();
  initAutoDismissAlerts();
  initSidebarToggle();
  initGateControlLivePolling();
  initRFIDEnrollmentListener();
  initDriverModalListeners();
  initDirectionSwitcher();
});

function initDirectionSwitcher() {
  const form = document.getElementById('gate-direction-form');
  const btnEntry = document.getElementById('btn-nav-dir-entry');
  const btnExit = document.getElementById('btn-nav-dir-exit');
  if (!form || !btnEntry || !btnExit) return;

  const handleDirSwitch = async (e, dirVal) => {
    e.preventDefault();
    try {
      const formData = new FormData(form);
      formData.set('direction', dirVal);
      await fetch(form.action, {
        method: 'POST',
        body: formData
      });

      if (dirVal === 'ENTRY') {
        btnEntry.className = 'btn btn-success fw-bold text-white';
        btnExit.className = 'btn btn-outline-secondary';
      } else {
        btnExit.className = 'btn btn-info fw-bold text-white';
        btnEntry.className = 'btn btn-outline-secondary';
      }

      currentModalDirection = dirVal;
      if (typeof renderModalDirectionButton === 'function') {
        renderModalDirectionButton();
      }

      const dirText = document.querySelector('#gate-decision-container strong.text-primary');
      if (dirText) dirText.textContent = dirVal === 'ENTRY' ? 'ENTRY_ONLY' : 'EXIT_ONLY';
    } catch (err) {
      console.error('Failed to set direction asynchronously:', err);
      form.submit();
    }
  };

  btnEntry.addEventListener('click', (e) => handleDirSwitch(e, 'ENTRY'));
  btnExit.addEventListener('click', (e) => handleDirSwitch(e, 'EXIT'));
}

// ---------------- Sidebar Toggle ---------------- //
function initSidebarToggle() {
  const sidebar  = document.getElementById('app-sidebar');
  const toggleBtn = document.getElementById('sidebar-toggle');
  if (!sidebar || !toggleBtn) return;

  // By default, the sidebar is closed/collapsed unless explicitly opened by user
  const isExplicitlyOpen = localStorage.getItem('sidebarCollapsed') === 'false';
  if (isExplicitlyOpen) {
    sidebar.classList.remove('collapsed');
  } else {
    sidebar.classList.add('collapsed');
  }

  // Set correct icon on load
  const icon = toggleBtn.querySelector('i');
  if (icon) {
    icon.className = sidebar.classList.contains('collapsed') ? 'fa-solid fa-bars-staggered' : 'fa-solid fa-bars';
  }

  // Enable animation after initial page layout so initial paint or tab switching never flickers
  requestAnimationFrame(() => {
    setTimeout(() => {
      sidebar.classList.add('transition-ready');
    }, 60);
  });

  toggleBtn.addEventListener('click', () => {
    sidebar.classList.add('transition-ready');
    sidebar.classList.toggle('collapsed');
    const isCollapsed = sidebar.classList.contains('collapsed');
    localStorage.setItem('sidebarCollapsed', isCollapsed ? 'true' : 'false');

    // Swap icon: bars ↔ bars-staggered
    if (icon) {
      icon.className = isCollapsed ? 'fa-solid fa-bars-staggered' : 'fa-solid fa-bars';
    }
  });
}

// ---------------- Live Server Date & Clock Synchronization ---------------- //
let serverTimeOffsetMs = 0;
let hasServerTimeSync = false;

function syncServerTime(serverTimeIso) {
  if (!serverTimeIso) return;
  try {
    const sDate = new Date(serverTimeIso);
    if (!isNaN(sDate.getTime())) {
      serverTimeOffsetMs = sDate.getTime() - Date.now();
      hasServerTimeSync = true;
    }
  } catch (e) {}
}

function initClock() {
  const clockElem = document.getElementById('live-clock');
  const dateElem = document.getElementById('live-date');
  if (!clockElem && !dateElem) return;

  // Query server time immediately on boot to calibrate exact server offset
  fetch('/api/dashboard/stats')
    .then(res => res.json())
    .then(data => {
      if (data && data.server_time_iso) {
        syncServerTime(data.server_time_iso);
      }
    })
    .catch(() => {});

  function update() {
    const now = new Date(Date.now() + serverTimeOffsetMs);
    if (clockElem) {
      clockElem.textContent = now.toLocaleTimeString('en-GB', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
    if (dateElem) {
      dateElem.textContent = now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    }
  }
  update();
  setInterval(update, 1000);
}

// ---------------- Auto Dismiss Flash Alerts ---------------- //
function initAutoDismissAlerts() {
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(alert => {
    setTimeout(() => {
      try {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      } catch (e) {}
    }, 6000);
  });
}

// ---------------- Gate Control Live Polling & State Management ---------------- //
let lastKnownEventKey = null;
let currentEvent = null;
let currentMovementId = null;
let isSelectingDriver = false;
let decisionResetTimer = null;
let barrierTimer = null;
let isFirstPoll = true;
let currentPendingScan = null;
let currentPendingScanId = null;
let scanConfirmationModalInstance = null;
let lastHandledAlcoholScanId = null;
let isConfirmationSuccessPending = false;

function initGateControlLivePolling() {
  const isAuth = !!document.getElementById('app-sidebar') || !!document.querySelector('.top-navbar') || !!document.getElementById('gate-decision-container');
  if (!isAuth) return;

  const pollInterval = 1200; // Poll every 1.2s for rapid response
  setInterval(pollGateFeed, pollInterval);
}

async function pollGateFeed() {
  try {
    const res = await fetch('/api/movements/live_feed');
    if (!res.ok) return;
    const data = await res.json();

    if (data && data.server_time_iso) {
      syncServerTime(data.server_time_iso);
    }

    const insideCounter = document.getElementById('live-inside-count');
    if (insideCounter && data.inside_count !== undefined) {
      insideCounter.textContent = data.inside_count;
    }
    const outsideCounter = document.getElementById('live-outside-count');
    if (outsideCounter && data.outside_count !== undefined) {
      outsideCounter.textContent = data.outside_count;
    }

    // Update Dashboard big counters if present (e.g. on http://192.168.1.39:5000/)
    const dashOutside = document.getElementById('stat-vehicles-outside');
    if (dashOutside && data.outside_count !== undefined) {
      dashOutside.textContent = data.outside_count;
    }
    const dashInside = document.getElementById('stat-vehicles-inside');
    if (dashInside && data.inside_count !== undefined) {
      dashInside.textContent = data.inside_count;
    }

    // Update Live MQ-3 Sensor Readout on Gate Control top bar
    const navMq3Val = document.getElementById('nav-mq3-val');
    const navMq3Pill = document.getElementById('nav-mq3-pill');
    if (navMq3Val && data.latest_alcohol_reading && data.latest_alcohol_reading.value !== undefined) {
      const liveVal = Math.round(Number(data.latest_alcohol_reading.value));
      if (liveVal > 600) {
        navMq3Val.textContent = `${liveVal} (ALCOHOL ALERT)`;
        if (navMq3Pill) navMq3Pill.className = 'badge bg-danger text-white border border-danger px-2 py-2 align-self-center shadow-sm';
      } else {
        navMq3Val.textContent = `${liveVal} (Normal)`;
        if (navMq3Pill) navMq3Pill.className = 'badge bg-light text-dark border px-2 py-2 align-self-center shadow-sm';
      }
    }

    // Real-time pending scan & breathalyzer synchronization
    const modalElem = document.getElementById('scanConfirmationModal');
    const isModalVisible = modalElem && (modalElem.classList.contains('show') || modalElem.style.display === 'block');

    if (data.pending_scan && data.pending_scan.scan_id) {
      if (currentPendingScanId !== data.pending_scan.scan_id || !isModalVisible) {
        // New pending scan or modal not yet open: show confirmation modal
        openScanConfirmationModal(data.pending_scan);
      } else {
        // Prioritize the real-time live sensor reading coming from hardware (data.latest_alcohol_reading)
        let liveVal = null;
        if (data.latest_alcohol_reading && data.latest_alcohol_reading.value !== undefined && data.latest_alcohol_reading.value !== null) {
          liveVal = Math.round(Number(data.latest_alcohol_reading.value));
        } else if (data.pending_scan.alcohol_value !== null && data.pending_scan.alcohol_value !== undefined) {
          liveVal = Math.round(Number(data.pending_scan.alcohol_value));
        }

        const pStatus = data.pending_scan.sobriety_status;
        let derivedStatus = pStatus || currentSobrietyState || 'AWAITING';
        if (liveVal !== null && !isNaN(liveVal) && liveVal > 600) {
          derivedStatus = 'FAILED';
        }

        // Always update live sensor reading directly on confirmation modal elements
        const valElem = document.getElementById('modal-mq3-current-val');
        const pillElem = document.getElementById('modal-mq3-status-pill');
        if (valElem && liveVal !== null) {
          valElem.textContent = liveVal;
          valElem.className = liveVal > 600 
            ? 'badge bg-danger text-white border border-danger font-monospace fs-6 px-2 py-1 shadow-sm'
            : 'badge bg-white text-dark border font-monospace fs-6 px-2 py-1 shadow-sm';
        }
        if (pillElem && liveVal !== null && derivedStatus !== 'FAILED') {
          pillElem.className = 'badge bg-light text-dark border px-2 py-1 fw-semibold shadow-sm';
          pillElem.innerHTML = `<i class="fa-solid fa-circle-dot text-success me-1 fa-fade"></i>Live: ${liveVal} (Normal &le; 600 - Awaiting Blow)`;
        }

        if (derivedStatus && (derivedStatus !== currentSobrietyState || (liveVal !== null && liveVal !== lastSobrietyReadingValue))) {
          handleSobrietyUpdate(derivedStatus, liveVal, data.pending_scan.driver ? data.pending_scan.driver.name : null);
        }
      }
    } else if (!data.pending_scan && currentPendingScanId && !isAlcoholLockoutActive && !isConfirmationSuccessPending) {
      currentPendingScanId = null;
      currentPendingScan = null;
      closeScanConfirmationModal();
    }

    if (!data.last_event) {
      if (!isSelectingDriver && lastKnownEventKey !== null && lastKnownEventKey !== 'STANDBY') {
        lastKnownEventKey = 'STANDBY';
        resetGateDecisionToStandby();
      }
      isFirstPoll = false;
      return;
    }

    const evt = data.last_event;
    const eventKey = `${evt.movement_id || evt.time}-${evt.vehicle_number}-${evt.decision}`;

    // On initial page load or after mode switch: record current state without triggering false popups
    if (isFirstPoll) {
      isFirstPoll = false;
      lastKnownEventKey = eventKey;
      return;
    }

    if (lastKnownEventKey !== eventKey) {
      lastKnownEventKey = eventKey;
      handleIncomingGateScan(evt);
    }
  } catch (err) {
    console.error('Error polling gate feed:', err);
  }
}

function resetGateDecisionToStandby() {
  const decisionBox = document.getElementById('gate-decision-box');
  const titleElem = document.getElementById('decision-title');
  const plateElem = document.getElementById('decision-plate');
  const typeElem = document.getElementById('decision-type');
  const driverElem = document.getElementById('decision-driver');
  const uidElem = document.getElementById('decision-uid');
  const msgElem = document.getElementById('decision-message');
  const timeElem = document.getElementById('decision-time');
  const changeDrvBtn = document.getElementById('btn-change-driver');

  if (!decisionBox) return;

  currentMovementId = null;
  currentEvent = null;
  isSelectingDriver = false;

  if (decisionResetTimer) {
    clearTimeout(decisionResetTimer);
    decisionResetTimer = null;
  }

  decisionBox.className = 'gate-decision-box STANDBY';
  if (titleElem) titleElem.innerHTML = 'SYSTEM STANDBY';
  if (plateElem) plateElem.textContent = 'NO ACTIVE SCAN';
  if (msgElem) msgElem.textContent = 'Present RFID Card at ESP32 Reader to Operate Gate';
  if (typeElem) typeElem.textContent = '-';
  if (driverElem) driverElem.textContent = '-';
  if (uidElem) uidElem.textContent = '-';
  if (timeElem) timeElem.textContent = '-';
  if (changeDrvBtn) changeDrvBtn.style.display = 'none';
}

function handleIncomingGateScan(evt) {
  const decisionBox = document.getElementById('gate-decision-box');
  const titleElem = document.getElementById('decision-title');
  const plateElem = document.getElementById('decision-plate');
  const typeElem = document.getElementById('decision-type');
  const driverElem = document.getElementById('decision-driver');
  const uidElem = document.getElementById('decision-uid');
  const msgElem = document.getElementById('decision-message');
  const timeElem = document.getElementById('decision-time');
  const changeDrvBtn = document.getElementById('btn-change-driver');

  if (!decisionBox) return;

  currentEvent = evt;
  currentMovementId = evt.movement_id || null;

  // Clear any existing reset timer
  if (decisionResetTimer) {
    clearTimeout(decisionResetTimer);
    decisionResetTimer = null;
  }

  // Update telemetry details
  if (plateElem) plateElem.textContent = evt.vehicle_number || 'UNKNOWN';
  if (typeElem) typeElem.textContent = evt.vehicle_type || 'N/A';
  if (uidElem) uidElem.textContent = evt.rfid_uid || 'N/A';
  if (timeElem) timeElem.textContent = evt.time || '';

  if (evt.decision === 'ENTRY_ALLOWED' || evt.decision === 'EXIT_RECORDED') {
    isSelectingDriver = false;
    closeDriverModal();

    const defName = evt.driver_name || evt.owner_driver || 'Registered Driver';
    const isOutEvt = (evt.decision === 'EXIT_RECORDED' || evt.status === 'OUTSIDE') && evt.decision !== 'ENTRY_ALLOWED' && evt.direction !== 'ENTRY';
    if (Date.now() >= _suppressGateFeedSpeechUntil) {
      speakVehicleDetection(evt.vehicle_number, defName, isOutEvt ? 'OUT' : 'IN', false, true);
    }

    // Pre-fill modal data in case operator voluntarily clicks "Select Driver"
    const modalPlate = document.getElementById('modal-vehicle-plate');
    const modalDefaultDrv = document.getElementById('modal-default-driver');
    const defaultDrvCard = document.getElementById('default-driver-card-name');
    if (modalPlate) modalPlate.textContent = evt.vehicle_number || '-';
    if (modalDefaultDrv) modalDefaultDrv.textContent = defName;
    if (defaultDrvCard) defaultDrvCard.textContent = defName;

    const searchInput = document.getElementById('driver-search-input');
    if (searchInput) {
      searchInput.value = '';
      filterDriverModalList();
    }

    if (changeDrvBtn) {
      changeDrvBtn.style.display = 'inline-block';
      changeDrvBtn.innerHTML = '<i class="fa-solid fa-user-pen me-1"></i>Select Driver';
    }

    // Automatically grant access and operate gate without interrupting operator with a modal
    finalizeAccessGrant(defName);

  } else {
    // Denied / Exception Attempt
    isSelectingDriver = false;
    closeDriverModal();
    decisionBox.className = 'gate-decision-box DENIED';
    if (evt.status === 'ALCOHOL_DETECTED') {
      if (titleElem) titleElem.innerHTML = '<i class="fa-solid fa-wine-bottle text-warning me-2"></i>ALCOHOL DETECTED! ACCESS BLOCKED';
      if (msgElem) msgElem.textContent = `🚨 CRITICAL SOBRIETY ALERT: Driver intoxicated! ${evt.remarks || 'Gate barrier locked'}`;
      speakVehicleDetection(evt.vehicle_number, evt.driver_name, 'ALCOHOL_ALERT');
    } else {
      if (titleElem) titleElem.innerHTML = '<i class="fa-solid fa-ban me-2"></i>ACCESS DENIED';
      if (msgElem) msgElem.textContent = `Denied: ${evt.status} (${evt.remarks || ''})`;
    }
    if (driverElem) driverElem.textContent = evt.driver_name || '-';
    if (changeDrvBtn) changeDrvBtn.style.display = 'none';
    playChime(false);

    // Auto reset back to Standby after 6s for denied scans
    decisionResetTimer = setTimeout(() => {
      resetGateDecisionToStandby();
    }, 6000);
  }
}

// ---------------- Driver Modal & Selection Logic ---------------- //
function initDriverModalListeners() {
  const modalElem = document.getElementById('quickDriverModal');
  if (!modalElem) return;

  modalElem.addEventListener('hidden.bs.modal', () => {
    // If operator closed the popup without picking a pool driver, auto-confirm with default driver
    if (isSelectingDriver && currentMovementId) {
      const defName = document.getElementById('modal-default-driver')?.textContent || 'Registered Driver';
      selectTripDriver(null, defName);
    }
  });
}

function openQuickDriverModal() {
  const modalElem = document.getElementById('quickDriverModal');
  if (!modalElem) return;
  const modal = bootstrap.Modal.getOrCreateInstance(modalElem);
  modal.show();
}

function closeDriverModal() {
  const modalElem = document.getElementById('quickDriverModal');
  if (!modalElem) return;
  const modal = bootstrap.Modal.getInstance(modalElem);
  if (modal) modal.hide();
}

function filterDriverModalList() {
  const query = document.getElementById('driver-search-input')?.value.toLowerCase().trim() || '';
  const cards = document.querySelectorAll('.driver-item-card');
  cards.forEach(card => {
    const text = card.getAttribute('data-search-text') || '';
    if (!query || text.includes(query)) {
      card.style.display = '';
    } else {
      card.style.display = 'none';
    }
  });
}

async function selectTripDriver(driverId, driverName) {
  isSelectingDriver = false;
  closeDriverModal();

  const chosenDriverName = driverName || 'Registered Driver';

  if (currentMovementId) {
    try {
      await fetch(`/api/movements/${currentMovementId}/assign_driver`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          driver_id: driverId,
          driver_name: chosenDriverName
        })
      });
    } catch (err) {
      console.error('Error assigning trip driver:', err);
    }
  }

  // Announce newly selected driver
  const vehPlate = (currentEvent && currentEvent.vehicle_number) || '';
  speakVehicleDetection(vehPlate, chosenDriverName, 'DRIVER_CHANGE');

  // Grant Access & Open Barrier Gate
  finalizeAccessGrant(chosenDriverName);
}

function finalizeAccessGrant(driverName) {
  const decisionBox = document.getElementById('gate-decision-box');
  const titleElem = document.getElementById('decision-title');
  const msgElem = document.getElementById('decision-message');
  const driverElem = document.getElementById('decision-driver');
  const changeDrvBtn = document.getElementById('btn-change-driver');

  if (!decisionBox) return;

  if (driverElem) {
    driverElem.innerHTML = `<span class="badge bg-success px-2 py-1"><i class="fa-solid fa-user-check me-1"></i>${driverName}</span>`;
  }

  const isExit = currentEvent && currentEvent.decision === 'EXIT_RECORDED';
  if (isExit) {
    decisionBox.className = 'gate-decision-box EXIT';
    if (titleElem) titleElem.innerHTML = '<i class="fa-solid fa-arrow-right-from-bracket me-2"></i>EXIT RECORDED - OUTBOUND DISPATCH';
    if (msgElem) msgElem.textContent = `Vehicle Dispatched (OUTSIDE) with Driver: ${driverName}! Barrier Opening...`;
  } else {
    decisionBox.className = 'gate-decision-box ALLOWED';
    if (titleElem) titleElem.innerHTML = '<i class="fa-solid fa-circle-check me-2"></i>ACCESS GRANTED';
    if (msgElem) msgElem.textContent = `Access Permitted for ${driverName}! Barrier Opening...`;
  }

  if (changeDrvBtn) changeDrvBtn.style.display = 'none';

  // Get configured auto close delay in seconds (default: 4-5)
  const delayElem = document.getElementById('barrier-auto-delay');
  const autoCloseSec = delayElem ? (parseInt(delayElem.textContent, 10) || 4) : 4;

  // Open barrier arm actuator
  triggerBarrierOpen(autoCloseSec);

  // Play triumph / success chime
  playChime(true);

  // Reset back to SYSTEM STANDBY after vehicle passes (autoCloseSec + 2.5s)
  if (decisionResetTimer) clearTimeout(decisionResetTimer);
  const totalDisplayMs = (autoCloseSec + 2.5) * 1000;
  decisionResetTimer = setTimeout(() => {
    resetGateDecisionToStandby();
  }, totalDisplayMs);
}

// ---------------- Barrier Actuator Simulation ---------------- //
function triggerBarrierOpen(delaySec = 4) {
  const arm = document.getElementById('barrier-arm');
  const status = document.getElementById('barrier-status-text');
  const timerBadge = document.getElementById('barrier-timer-badge');

  if (!arm) return;

  arm.classList.remove('closed');
  arm.classList.add('open');
  if (status) status.innerHTML = '<span class="text-success font-weight-bold">OPEN (PASSING)</span>';

  if (barrierTimer) clearInterval(barrierTimer);
  let remaining = delaySec;

  if (timerBadge) {
    timerBadge.classList.remove('d-none');
    timerBadge.textContent = `Auto-closing in ${remaining}s...`;
  }

  barrierTimer = setInterval(() => {
    remaining--;
    if (timerBadge) timerBadge.textContent = `Auto-closing in ${remaining}s...`;
    if (remaining <= 0) {
      clearInterval(barrierTimer);
      barrierTimer = null;
      arm.classList.remove('open');
      arm.classList.add('closed');
      if (status) status.innerHTML = '<span class="text-secondary font-weight-bold">CLOSED</span>';
      if (timerBadge) timerBadge.classList.add('d-none');
    }
  }, 1000);
}

// ---------------- Audio Feedback (Web Audio API Synthesizer) ---------------- //
let _sharedAudioCtx = null;
function getAudioContext() {
  try {
    const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtxClass) return null;
    if (!_sharedAudioCtx) {
      _sharedAudioCtx = new AudioCtxClass();
    }
    if (_sharedAudioCtx.state === 'suspended') {
      _sharedAudioCtx.resume().catch(() => {});
    }
    return _sharedAudioCtx;
  } catch (e) {
    return null;
  }
}

function initAudioAutoplayUnlock() {
  const unlock = () => {
    try {
      const ctx = getAudioContext();
      if (ctx && ctx.state === 'suspended') {
        ctx.resume().catch(() => {});
      }
      if ('speechSynthesis' in window) {
        const silent = new SpeechSynthesisUtterance(' ');
        silent.volume = 0;
        window.speechSynthesis.speak(silent);
      }
    } catch (e) {}
    window.removeEventListener('click', unlock);
    window.removeEventListener('keydown', unlock);
    window.removeEventListener('pointerdown', unlock);
    window.removeEventListener('touchstart', unlock);
  };
  window.addEventListener('click', unlock, { once: true, passive: true });
  window.addEventListener('keydown', unlock, { once: true, passive: true });
  window.addEventListener('pointerdown', unlock, { once: true, passive: true });
  window.addEventListener('touchstart', unlock, { once: true, passive: true });
}
initAudioAutoplayUnlock();

function playChime(isSuccess) {
  if (!voiceAnnouncementsEnabled) return;
  try {
    const ctx = getAudioContext();
    if (!ctx || ctx.state === 'suspended') return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.connect(gain);
    gain.connect(ctx.destination);

    if (isSuccess) {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
      osc.frequency.setValueAtTime(880, ctx.currentTime + 0.12); // A5
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc.start();
      osc.stop(ctx.currentTime + 0.4);
    } else {
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(220, ctx.currentTime); // A3
      gain.gain.setValueAtTime(0.25, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.45);
      osc.start();
      osc.stop(ctx.currentTime + 0.45);
    }
  } catch (e) {}
}

function playAttentionSound() {
  if (!voiceAnnouncementsEnabled) return;
  try {
    const ctx = getAudioContext();
    if (!ctx || ctx.state === 'suspended') return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(659.25, ctx.currentTime); // E5
    osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.09); // G5
    gain.gain.setValueAtTime(0.18, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.28);
    osc.start();
    osc.stop(ctx.currentTime + 0.28);
  } catch (e) {}
}

// ============================================================
// GOOGLE EN-IN / NEERJA VOICE (en-IN / Neerja)
// Uses Microsoft Neerja (Online Natural) / Google English (India)
// 100% Authentic Indian Girl voice requested by user
// ============================================================
let voiceAnnouncementsEnabled = localStorage.getItem('voice_announcements_enabled') !== '0';
let _activeGateAudio = null;
let _currentSpeechUtterance = null;
let _suppressGateFeedSpeechUntil = 0;
let _voicesCache = null;

// Blacklist of known male voice terms to strictly forbid male voices
const MALE_VOICE_TERMS = [
  'david', 'mark', 'george', 'richard', 'james', 'prabhat', 'madhur', 
  'ravi', 'male', 'guy', 'stefan', 'paul', 'tom', 'alex', 'fred',
  'brian', 'daniel', 'oliver', 'thomas', 'sean', 'hemant', 'kalpesh'
];

function isMaleVoiceName(name) {
  if (!name) return false;
  const n = name.toLowerCase();
  return MALE_VOICE_TERMS.some(term => n.includes(term));
}

function getAvailableVoices() {
  if (!('speechSynthesis' in window)) return [];
  const list = window.speechSynthesis.getVoices();
  if (list && list.length > 0) {
    _voicesCache = list;
    return list;
  }
  return _voicesCache || [];
}

// Strictly find Microsoft Neerja (or Google English India / English (India) female voice) ONLY.
// Zero foreign/US fallbacks. If no Indian female voice is found, returns null and stays completely silent.
function getNeerjaGoogleVoice() {
  const voices = getAvailableVoices();
  if (!voices || !voices.length) return null;

  // 1. Direct Neerja match (e.g. "Microsoft Neerja (Natural) - English (India)", "Microsoft Neerja", etc.)
  const neerja = voices.find(v => {
    const n = v.name.toLowerCase();
    return n.includes('neerja') && !isMaleVoiceName(n);
  });
  if (neerja) return neerja;

  // 2. Google English (India) or Microsoft English (India) female voice installed with English (India) pack
  const inFemale = voices.find(v => {
    const n = v.name.toLowerCase();
    const isIndian = (v.lang === 'en-IN' || v.lang === 'en_IN' || n.includes('india') || n.includes('heera') || n.includes('swara'));
    return isIndian && !isMaleVoiceName(n);
  });
  if (inFemale) return inFemale;

  return null;
}

if ('speechSynthesis' in window) {
  // Prime speech synthesis voices immediately on load
  try {
    const initial = window.speechSynthesis.getVoices();
    if (initial && initial.length > 0) _voicesCache = initial;
  } catch (e) {}

  window.speechSynthesis.onvoiceschanged = () => {
    _voicesCache = window.speechSynthesis.getVoices();
    console.log("VMS Audio Voices loaded in browser:", _voicesCache.map(v => `"${v.name}" [${v.lang}]`));
  };
}

function stopAllAudio() {
  if (_activeGateAudio) {
    try {
      _activeGateAudio.pause();
      _activeGateAudio.currentTime = 0;
      _activeGateAudio.src = '';
    } catch (e) {}
    _activeGateAudio = null;
  }
  if ('speechSynthesis' in window) {
    try {
      window.speechSynthesis.cancel();
    } catch (e) {}
  }
  _currentSpeechUtterance = null;
}

// Speak STRICTLY with Microsoft Neerja female voice.
// Fallback removed: If Neerja is not installed, no other voice will ever play!
async function speakWithNeerjaGoogleVoice(text, onEndedCallback) {
  if (!voiceAnnouncementsEnabled || !text) {
    if (onEndedCallback) onEndedCallback();
    return;
  }

  // Cross-tab deduplication: prevent two open tabs on the same computer from speaking simultaneously
  const now = Date.now();
  const lastSpoken = parseInt(localStorage.getItem('vms_last_spoken_ts') || '0', 10);
  const lastText = localStorage.getItem('vms_last_spoken_txt') || '';
  if (now - lastSpoken < 2500 && lastText === text) {
    console.log("Suppressing duplicate announcement from secondary tab:", text);
    if (onEndedCallback) onEndedCallback();
    return;
  }
  localStorage.setItem('vms_last_spoken_ts', now.toString());
  localStorage.setItem('vms_last_spoken_txt', text);

  // 1. Immediately halt all other speech / audio so two voices NEVER overlap
  stopAllAudio();

  if (!('speechSynthesis' in window)) {
    if (onEndedCallback) onEndedCallback();
    return;
  }

  let voices = getAvailableVoices();
  if (!voices || voices.length === 0) {
    await new Promise(resolve => {
      let resolved = false;
      const done = () => {
        if (!resolved) {
          resolved = true;
          resolve();
        }
      };
      const timer = setTimeout(done, 400);
      window.speechSynthesis.onvoiceschanged = () => {
        clearTimeout(timer);
        _voicesCache = window.speechSynthesis.getVoices();
        done();
      };
    });
    voices = getAvailableVoices();
  }

  console.log("VMS Audio: Checking voices list (" + voices.length + " found):", voices.map(v => v.name));

  const chosenVoice = getNeerjaGoogleVoice();

  // STRICT REQUIREMENT: If Neerja is not installed, play NOTHING (No fallback!)
  if (!chosenVoice) {
    console.warn("Neerja voice not found. Available voices in this browser are:", voices.map(v => `"${v.name}" (${v.lang})`));
    console.warn("If you recently installed Neerja in Windows, please close and RESTART your browser completely.");
    if (onEndedCallback) onEndedCallback();
    return;
  }

  console.log("VMS Audio: Speaking with voice ->", chosenVoice.name);

  // Tiny delay to let browser audio pipeline clear completely after cancel()
  await new Promise(r => setTimeout(r, 60));

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = chosenVoice.lang || 'en-IN';
  utterance.voice = chosenVoice;
  utterance.rate = 0.90;
  utterance.pitch = 1.05;

  let finished = false;
  const finish = () => {
    if (finished) return;
    finished = true;
    _currentSpeechUtterance = null;
    if (onEndedCallback) onEndedCallback();
  };

  utterance.onend = finish;
  utterance.onerror = (e) => {
    if (e.error === 'not-allowed') {
      console.warn("VMS Audio: Autoplay blocked by browser policy. Click anywhere on the page once to enable sound, or set Media Autoplay to Allow in Edge settings.");
    } else {
      console.warn("SpeechSynthesis error:", e);
    }
    finish();
  };

  const words = text.split(/\s+/).length;
  const maxWaitMs = Math.max(3000, words * 550);
  setTimeout(finish, maxWaitMs);

  _currentSpeechUtterance = utterance;
  window.speechSynthesis.speak(utterance);
}

// Reset audio and cancel pending scan on page refresh / navigate
window.addEventListener('beforeunload', () => {
  stopAllAudio();
  try {
    navigator.sendBeacon('/api/rfid/cancel_pending_scan');
  } catch (e) {}
});

window.addEventListener('pagehide', () => {
  stopAllAudio();
});

function updateVoiceButtons() {
  const btns = document.querySelectorAll('.btn-toggle-voice');
  btns.forEach(btn => {
    if (voiceAnnouncementsEnabled) {
      btn.className = 'btn btn-outline-success btn-sm btn-toggle-voice rounded-pill px-2 px-md-3 py-1 shadow-sm d-inline-flex align-items-center gap-1';
      btn.innerHTML = '<i class="fa-solid fa-volume-high"></i><span class="fw-semibold" style="font-size:0.78rem;">Voice: ON</span>';
      btn.title = 'Audio / Voice is ON (Click to Mute)';
      btn.setAttribute('aria-label', 'Audio / Voice is ON (Click to Mute)');
    } else {
      btn.className = 'btn btn-outline-danger btn-sm btn-toggle-voice rounded-pill px-2 px-md-3 py-1 shadow-sm d-inline-flex align-items-center gap-1';
      btn.innerHTML = '<i class="fa-solid fa-volume-xmark"></i><span class="fw-semibold" style="font-size:0.78rem;">Voice: MUTED</span>';
      btn.title = 'Audio / Voice is MUTED (Click to Enable)';
      btn.setAttribute('aria-label', 'Audio / Voice is MUTED (Click to Enable)');
    }
  });
}

function toggleVoiceAnnouncements() {
  voiceAnnouncementsEnabled = !voiceAnnouncementsEnabled;
  localStorage.setItem('voice_announcements_enabled', voiceAnnouncementsEnabled ? '1' : '0');
  updateVoiceButtons();
  if (voiceAnnouncementsEnabled) {
    playChime(true);
  } else {
    stopAllAudio();
  }
}

function testVoiceAnnouncement() {
  voiceAnnouncementsEnabled = true;
  localStorage.setItem('voice_announcements_enabled', '1');
  updateVoiceButtons();
  speakVehicleDetection('DL01AB1234', 'Dhirendra Singh', 'IN', true);
}

// Format plate characters for crystal-clear en-IN Neerja pronunciation
function formatPlateSpoken(vNum) {
  if (!vNum) return '';
  const digitWord = { '0':'zero','1':'one','2':'two','3':'three','4':'four',
                      '5':'five','6':'six','7':'seven','8':'eight','9':'nine' };
  return vNum.toString().trim().toUpperCase().split('').map(ch => digitWord[ch] || ch).join(' ');
}

// Build the Hindi/Hinglish text to speak (exact script from last GitHub push)
function buildAnnouncementText(vehicleNumber, driverName, direction, isTest, isConfirmed = false) {
  const isOut = ['OUT','EXIT'].includes((direction||'').toUpperCase());

  let vNum = (vehicleNumber || '').toString().trim().toUpperCase();
  let dName = (driverName  || '').toString().trim();

  const skipV = ['UNKNOWN','N/A','-',''];
  const skipD = ['Unassigned','Unknown','Master Driver','Registered Driver','-',''];
  if (skipV.includes(vNum)) vNum = '';
  if (skipD.includes(dName)) dName = '';

  const plateSpoken = formatPlateSpoken(vNum);

  if (direction === 'ALCOHOL_ALERT') {
    return 'Alcohol detect hua hai, aab gadi nhi chala sakte ho.';
  }

  if (direction === 'DRIVER_UNAUTHORIZED') {
    return 'Yeh driver authorized nahi hai. Driver change karo.';
  }

  if (direction === 'DRIVER_CHANGE') {
    const isOutScan = !currentPendingScan || currentPendingScan.current_status === 'INSIDE' || currentPendingScan.recommended_direction === 'EXIT';
    if (!isOutScan) {
      return 'Gaadi MT mein wapas aa rahi hai.';
    }
    if (dName) {
      return `Naya driver ${dName} assign hua hai. Kripya sensor mein foonk maaro.`;
    }
    return 'Naya driver assign hua hai. Kripya sensor mein foonk maaro.';
  }

  if (isTest) {
    return 'Namaste! Gate audio system chalu hai. Gaadi andar aana chahti hai.';
  }

  // After confirmation announcement (IN or OUT)
  if (isConfirmed) {
    return isOut
      ? 'Gaadi ab baahar jaa rahi hai.'
      : 'Gaadi ab andar aa rahi hai.';
  }

  if (!isOut) {
    let inText = plateSpoken ? `Gaadi number ${plateSpoken}. ` : 'Gaadi scan hui. ';
    if (dName) inText += `Driver ${dName}, `;
    inText += 'gaadi MT mein wapas aa rahi hai.';
    return inText;
  }

  let text = plateSpoken ? `Gaadi number ${plateSpoken}. ` : 'Gaadi scan hui. ';
  if (dName) text += `Driver ${dName}, `;
  text += 'kripya sensor mein foonk maaro.';
  return text;
}

// ---- Main speaker: speaks via Google en-IN / Neerja voice ----
function speakVehicleDetection(vehicleNumber, driverName, direction, isTest = false, isConfirmed = false) {
  if (!voiceAnnouncementsEnabled) return;

  if (direction === 'DRIVER_UNAUTHORIZED' || direction === 'ALCOHOL_ALERT') {
    playChime(false);
  } else {
    playChime(true);
  }

  const text = buildAnnouncementText(vehicleNumber, driverName, direction, isTest, isConfirmed);
  if (!text) return;

  stopAllAudio();
  speakWithNeerjaGoogleVoice(text);
}

// ---------------- RFID Card Enrollment Listener ---------------- //
let enrollmentInterval = null;
let lastCapturedEnrollmentUid = null;

function initRFIDEnrollmentListener() {
  const enrollModal = document.getElementById('enrollCardModal');
  if (!enrollModal) return;

  const pollEnrollment = async () => {
    try {
      const res = await fetch('/api/rfid/latest_enrollment');
      if (!res.ok) return;
      const data = await res.json();
      if (data.active && data.data && data.data.uid) {
        const uid = data.data.uid.toUpperCase();
        const uidInput = document.getElementById('assign-uid-input');
        const statusText = document.getElementById('enroll-listener-status');
        const driverSelect = document.getElementById('driverSelect_enroll');

        if (uidInput && uidInput.value !== uid) {
          uidInput.value = uid;
          uidInput.classList.add('is-valid');
          
          // Silent enrollment capture - do NOT trigger vehicle voice announcement
          if (lastCapturedEnrollmentUid !== uid) {
            lastCapturedEnrollmentUid = uid;
            if (typeof playChime === 'function') {
              playChime(true); // Subtle soft chime only, no vehicle voice
            }
          }

          // Auto-focus driver select for fast assignment
          if (driverSelect && !driverSelect.value) {
            driverSelect.focus();
          }
        }

        if (statusText) {
          statusText.innerHTML = `<span class="text-success fw-bold"><i class="fa-solid fa-circle-check me-1"></i>Tag Captured: ${uid}</span> <span class="badge bg-success text-white ms-2"><i class="fa-solid fa-satellite-dish me-1"></i>${data.data.device_id || 'GATE01'}</span>`;
        }
      }
    } catch (err) {}
  };

  enrollModal.addEventListener('shown.bs.modal', () => {
    const statusText = document.getElementById('enroll-listener-status');
    const uidInput = document.getElementById('assign-uid-input');
    lastCapturedEnrollmentUid = null;

    if (statusText && (!uidInput || !uidInput.value)) {
      statusText.innerHTML = '<span class="pulse-dot pulse-green me-1"></span>Waiting for card scan on ESP32 reader...';
    }

    // Check immediately, then poll every 500ms for instant auto-fill
    pollEnrollment();
    enrollmentInterval = setInterval(pollEnrollment, 500);
  });

  enrollModal.addEventListener('hidden.bs.modal', () => {
    if (enrollmentInterval) {
      clearInterval(enrollmentInterval);
      enrollmentInterval = null;
    }
  });
}

// ---------------- Test Scan & Hardware Simulator Helpers ---------------- //
async function triggerTestScan(uid) {
  if (!uid) return;
  try {
    const res = await fetch('/api/rfid/lookup_scan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        uid: uid,
        device_id: 'GATE01'
      })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      openScanConfirmationModal(data);
    } else {
      alert(`Scan Verification Failed: ${data.message || 'Tag not authorized'}`);
      playChime(false);
    }
  } catch (err) {
    console.error('Test scan failed:', err);
    alert('Communication error with gate reader.');
  }
}

function triggerManualTestScan() {
  const input = document.getElementById('manual-scan-uid');
  if (!input || !input.value.trim()) {
    alert('Please enter an RFID Tag UID to test.');
    return;
  }
  const uid = input.value.trim();
  triggerTestScan(uid);
}

let currentModalDirection = 'ENTRY';

function getActiveNavbarDirection() {
  const btnExit = document.getElementById('btn-nav-dir-exit');
  if (btnExit && (btnExit.classList.contains('btn-info') || btnExit.classList.contains('btn-warning') || btnExit.classList.contains('btn-danger') || btnExit.classList.contains('active'))) {
    return 'EXIT';
  }
  const btnEntry = document.getElementById('btn-nav-dir-entry');
  if (btnEntry && (btnEntry.classList.contains('btn-success') || btnEntry.classList.contains('active'))) {
    return 'ENTRY';
  }
  return 'ENTRY';
}

function renderModalDirectionButton() {
  const wrapIn = document.getElementById('wrapper-confirm-in');
  const wrapOut = document.getElementById('wrapper-confirm-out');
  const conflictAlert = document.getElementById('modal-direction-conflict-alert');
  const conflictMsg = document.getElementById('modal-direction-conflict-msg');
  const hintElem = document.getElementById('modal-direction-hint');

  if (!currentPendingScan) return;

  const currentStatus = currentPendingScan.current_status; // "INSIDE" or "OUTSIDE"
  const isInside = currentStatus === 'INSIDE';
  const activeNavbarDir = getActiveNavbarDirection(); // "ENTRY" or "EXIT"
  const vehPlate = (currentPendingScan.vehicle && currentPendingScan.vehicle.registration_number) || 'Vehicle';

  if (isInside) {
    // 🏢 VEHICLE IS CURRENTLY INSIDE THE DEPOT
    // CANNOT DO ENTRY (IN)! Only EXIT (OUT) is permitted.
    if (activeNavbarDir === 'ENTRY') {
      // Guard is on ENTRY tab, but vehicle is ALREADY INSIDE!
      if (conflictAlert) {
        conflictAlert.classList.remove('d-none');
        conflictAlert.classList.add('d-flex');
      }
      if (conflictMsg) {
        conflictMsg.innerHTML = `<strong>ALREADY INSIDE:</strong> <code>${vehPlate}</code> is already in MT Garage. <strong>ENTRY (IN) is blocked.</strong> Only EXIT (OUT) is allowed.`;
      }
      if (hintElem) {
        hintElem.innerHTML = `<span class="text-danger fw-bold"><i class="fa-solid fa-ban me-1"></i>ENTRY Blocked (Already Inside)</span>`;
      }
    } else {
      if (conflictAlert) {
        conflictAlert.classList.add('d-none');
        conflictAlert.classList.remove('d-flex');
      }
      if (hintElem) {
        hintElem.innerHTML = `<span class="text-success fw-semibold"><i class="fa-solid fa-check-circle me-1"></i>Inside MT Garage &bull; Ready to Dispatch OUT</span>`;
      }
    }

    // Since vehicle is INSIDE, only OUT is possible!
    if (wrapIn) wrapIn.style.display = 'none';
    if (wrapOut) wrapOut.style.display = 'block';

  } else {
    // 🚗 VEHICLE IS CURRENTLY OUTSIDE ON A TRIP
    // CANNOT DO EXIT (OUT)! Only ENTRY (IN) is permitted.
    if (activeNavbarDir === 'EXIT') {
      // Guard is on EXIT tab, but vehicle is ALREADY OUTSIDE!
      if (conflictAlert) {
        conflictAlert.classList.remove('d-none');
        conflictAlert.classList.add('d-flex');
      }
      if (conflictMsg) {
        conflictMsg.innerHTML = `<strong>ALREADY OUTSIDE:</strong> <code>${vehPlate}</code> is currently outside on a trip. <strong>EXIT (OUT) is blocked.</strong> Only ENTRY (IN) is allowed.`;
      }
      if (hintElem) {
        hintElem.innerHTML = `<span class="text-danger fw-bold"><i class="fa-solid fa-ban me-1"></i>EXIT Blocked (Already Outside)</span>`;
      }
    } else {
      if (conflictAlert) {
        conflictAlert.classList.add('d-none');
        conflictAlert.classList.remove('d-flex');
      }
      if (hintElem) {
        hintElem.innerHTML = `<span class="text-success fw-semibold"><i class="fa-solid fa-check-circle me-1"></i>On Outside Trip &bull; Ready to Return IN</span>`;
      }
    }

    // Since vehicle is OUTSIDE, only IN is possible!
    if (wrapIn) wrapIn.style.display = 'block';
    if (wrapOut) wrapOut.style.display = 'none';
  }
}

function toggleModalDirection() {
  renderModalDirectionButton();
}

// ---------------- Live Driver Sobriety & MQ-3 State Management ---------------- //
let currentSobrietyState = 'AWAITING_TEST'; // 'AWAITING_TEST' | 'PASSED' | 'FAILED'
let lastSobrietyReadingValue = null;
let lastAnnouncedSobrietyState = null;
let isAlcoholLockoutActive = false;
let isAutoDispatching = false;

function triggerAutoDispatchIfSober() {
  // Disabled: Automatic dispatch is disabled. The operator must confirm dispatch manually.
  return;
}

function applySobrietyUI(state, value, driverName) {
  const bBox = document.getElementById('modal-breathalyzer-status');
  const bBadge = document.getElementById('badge-breathalyzer-status');
  const bIcon = document.getElementById('icon-breathalyzer-status');
  const bTitle = document.getElementById('title-breathalyzer-status');
  const bSub = document.getElementById('sub-breathalyzer-status');
  const valElem = document.getElementById('modal-mq3-current-val');
  const pillElem = document.getElementById('modal-mq3-status-pill');

  const btnIn = document.getElementById('btn-confirm-in');
  const btnOut = document.getElementById('btn-confirm-out');
  const colConfIn = document.getElementById('col-confirm-in');
  const colConfOut = document.getElementById('col-confirm-out');
  const autoAlert = document.getElementById('modal-alcohol-auto-alert');
  const autoMsg = document.getElementById('modal-alcohol-auto-msg');

  const dName = driverName || (currentPendingScan && currentPendingScan.driver ? currentPendingScan.driver.name : 'Driver');
  const displayVal = (value !== null && value !== undefined && !isNaN(value)) ? Math.round(Number(value)) : '--';

  // Always update numeric sensor readout on the confirmation modal
  if (valElem) {
    valElem.textContent = displayVal;
    if (displayVal !== '--') {
      valElem.className = Number(displayVal) > 600 
        ? 'badge bg-danger text-white border border-danger font-monospace fs-6 px-2 py-1 shadow-sm'
        : 'badge bg-white text-dark border font-monospace fs-6 px-2 py-1 shadow-sm';
    }
  }

  // When vehicle is CURRENTLY OUTSIDE (returning for IN): NO ALCOHOL TEST REQUIRED!
  const isVehicleOutside = (currentPendingScan && (currentPendingScan.current_status === 'OUTSIDE' || currentPendingScan.is_outside === true) && currentPendingScan.current_status !== 'INSIDE');
  const simToolbar = document.getElementById('mq3-simulation-toolbar');

  if (isVehicleOutside || state === 'NOT_REQUIRED') {
    if (autoAlert) {
      autoAlert.classList.add('d-none');
      autoAlert.classList.remove('d-flex');
    }
    if (bBox) {
      bBox.className = 'alert alert-info py-2 px-3 rounded-3 mb-2 border border-info shadow-sm bg-info-subtle';
    }
    if (bBadge) {
      bBadge.className = 'badge bg-info text-white px-2 py-1 fs-6';
      bBadge.innerHTML = '<i class="fa-solid fa-car-side me-1"></i>CHECK-IN (NO ALCOHOL TEST)';
    }
    if (pillElem) {
      pillElem.className = 'badge bg-info text-white px-2 py-1 fw-semibold shadow-sm';
      pillElem.innerHTML = '<i class="fa-solid fa-check me-1"></i>Exempt (Return to MT)';
    }
    if (bIcon) bIcon.className = 'fa-solid fa-arrow-right-to-bracket fs-3 text-info';
    if (bTitle) bTitle.textContent = '';
    if (bSub) bSub.textContent = '';
    if (simToolbar) simToolbar.classList.add('d-none');

    if (colConfOut) colConfOut.style.display = 'none';
    if (colConfIn) colConfIn.style.display = '';
    if (btnOut) {
      btnOut.style.display = 'none';
      btnOut.disabled = true;
    }
    if (btnIn) {
      btnIn.style.display = '';
      btnIn.disabled = false;
      btnIn.classList.remove('btn-glow-in');
      btnIn.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket fs-4"></i><span>CONFIRM IN (Arrival to MT Garage)</span>';
    }
    return;
  }

  if (simToolbar) simToolbar.classList.remove('d-none');

  if (state === 'PASSED') {
    // SOBER - PASS (<= 600) -> AUTOMATIC OUT DISPATCH!
    if (autoAlert) {
      autoAlert.classList.add('d-none');
      autoAlert.classList.remove('d-flex');
    }
    if (bBox) {
      bBox.className = 'alert alert-success py-2 px-3 rounded-3 mb-2 border border-success shadow-sm bg-success-subtle';
    }
    if (bBadge) {
      bBadge.className = 'badge bg-success text-white px-2 py-1 fs-6';
      bBadge.innerHTML = `<i class="fa-solid fa-check-circle me-1"></i>PASSED`;
    }
    if (pillElem) {
      pillElem.className = 'badge bg-success text-white px-2 py-1 fw-semibold shadow-sm';
      pillElem.innerHTML = `<i class="fa-solid fa-check me-1"></i>Normal &amp; Safe (${displayVal} &le; 600)`;
    }
    if (bIcon) bIcon.className = 'fa-solid fa-shield-halved fs-3 text-success';
    if (bTitle) bTitle.textContent = '';
    if (bSub) bSub.textContent = '';

    // Standard operator confirmation buttons
    const isOutside = (currentPendingScan && (currentPendingScan.current_status === 'OUTSIDE' || currentPendingScan.recommended_direction === 'ENTRY'));
    if (colConfOut) colConfOut.style.display = isOutside ? 'none' : '';
    if (colConfIn) colConfIn.style.display = isOutside ? '' : 'none';
    if (btnOut) {
      btnOut.style.display = isOutside ? 'none' : '';
      btnOut.disabled = false;
      btnOut.classList.remove('btn-glow-out');
      btnOut.innerHTML = '<i class="fa-solid fa-arrow-right-from-bracket fs-4"></i><span>CONFIRM OUT (Outbound Dispatch)</span>';
    }
    if (btnIn) {
      btnIn.style.display = isOutside ? '' : 'none';
      btnIn.disabled = false;
      btnIn.classList.remove('btn-glow-in');
      btnIn.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket fs-4"></i><span>CONFIRM IN (Arrival to MT Garage)</span>';
    }

  } else if (state === 'FAILED') {
    // INTOXICATED - FAIL (> 600)
    const valText = (displayVal !== '--') ? `(${displayVal} > 600)` : '(> 600)';
    if (bBox) {
      bBox.className = 'alert alert-danger py-2 px-3 rounded-3 mb-2 border border-danger shadow-sm bg-danger-subtle';
    }
    if (bBadge) {
      bBadge.className = 'badge bg-danger text-white px-2 py-1 fs-6';
      bBadge.innerHTML = `<i class="fa-solid fa-triangle-exclamation me-1"></i>FAILED ${valText}`;
    }
    if (pillElem) {
      pillElem.className = 'badge bg-danger text-white px-2 py-1 fw-bold shadow-sm';
      pillElem.innerHTML = `<i class="fa-solid fa-triangle-exclamation me-1"></i>ALCOHOL DETECTED (${displayVal} &gt; 600)`;
    }
    if (bIcon) bIcon.className = 'fa-solid fa-wine-bottle fs-3 text-danger';
    if (bTitle) bTitle.textContent = '';
    if (bSub) bSub.textContent = '';

    if (autoAlert) {
      autoAlert.classList.remove('d-none');
      autoAlert.classList.add('d-flex');
    }
    if (autoMsg) {
      autoMsg.innerHTML = `<strong>CRITICAL SOBRIETY ALERT:</strong> Driver <u>${dName}</u> — Alcohol detect hua hai, aab gadi nhi chala sakte ho.`;
    }

    // CONFIRM BUTTONS ARE COMPLETELY HIDDEN ON SENSOR FAIL (> 600)
    if (colConfOut) colConfOut.style.display = 'none';
    if (colConfIn) colConfIn.style.display = 'none';
    if (btnOut) {
      btnOut.style.display = 'none';
      btnOut.disabled = true;
      btnOut.classList.remove('btn-glow-out');
    }
    if (btnIn) {
      btnIn.style.display = 'none';
      btnIn.disabled = true;
      btnIn.classList.remove('btn-glow-in');
    }

  } else {
    // AWAITING TEST
    if (autoAlert) {
      autoAlert.classList.add('d-none');
      autoAlert.classList.remove('d-flex');
    }
    if (bBox) {
      bBox.className = 'alert alert-secondary py-2 px-3 rounded-3 mb-2 border shadow-sm';
    }
    if (bBadge) {
      bBadge.className = 'badge bg-primary text-white px-2 py-1';
      bBadge.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i>AWAITING';
    }
    if (pillElem) {
      if (displayVal !== '--') {
        pillElem.className = 'badge bg-light text-dark border px-2 py-1 fw-semibold shadow-sm';
        pillElem.innerHTML = `<i class="fa-solid fa-circle-dot text-success me-1 fa-fade"></i>Live: ${displayVal} (Normal &le; 600 - Awaiting Blow)`;
      } else {
        pillElem.className = 'badge bg-info-subtle text-info-emphasis border border-info-subtle px-2 py-1 fw-semibold';
        pillElem.innerHTML = '<i class="fa-solid fa-wind me-1"></i>Awaiting Blow';
      }
    }
    if (bIcon) bIcon.className = 'fa-solid fa-wind fs-4 text-primary';
    if (bTitle) bTitle.textContent = '';
    if (bSub) bSub.textContent = '';

    // Confirm buttons are available for operator verification (Only hidden if alcohol alert is FAILED)
    const isOutside = (currentPendingScan && (currentPendingScan.current_status === 'OUTSIDE' || currentPendingScan.recommended_direction === 'ENTRY'));
    if (colConfOut) colConfOut.style.display = isOutside ? 'none' : '';
    if (colConfIn) colConfIn.style.display = isOutside ? '' : 'none';
    if (btnOut) {
      btnOut.style.display = isOutside ? 'none' : '';
      btnOut.disabled = false;
      btnOut.classList.remove('btn-glow-out');
      btnOut.innerHTML = '<i class="fa-solid fa-arrow-right-from-bracket fs-4"></i><span>CONFIRM OUT (Outbound Dispatch)</span>';
    }
    if (btnIn) {
      btnIn.style.display = isOutside ? '' : 'none';
      btnIn.disabled = false;
      btnIn.classList.remove('btn-glow-in');
      btnIn.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket fs-4"></i><span>CONFIRM IN (Arrival to MT Garage)</span>';
    }
  }
}

function handleSobrietyUpdate(status, val, driverName) {
  const isVehicleOutside = (currentPendingScan && (currentPendingScan.current_status === 'OUTSIDE' || currentPendingScan.is_outside === true) && currentPendingScan.current_status !== 'INSIDE');
  if (isVehicleOutside) {
    // Vehicle is currently outside returning for IN: No alcohol check!
    return;
  }

  currentSobrietyState = status;
  lastSobrietyReadingValue = val;

  const dName = driverName || (currentPendingScan && currentPendingScan.driver ? currentPendingScan.driver.name : 'Driver');

  if (currentPendingScan) {
    currentPendingScan.sobriety_status = status;
    currentPendingScan.alcohol_value = val;
    currentPendingScan.sobriety_passed = (status === 'PASSED');
    currentPendingScan.alcohol_detected = (status === 'FAILED');
  }

  applySobrietyUI(status, val, dName);

  if (status === 'FAILED') {
    isAlcoholLockoutActive = true;
    if (lastAnnouncedSobrietyState !== 'FAILED') {
      lastAnnouncedSobrietyState = 'FAILED';
      playChime(false);
      speakVehicleDetection(
        (currentPendingScan && currentPendingScan.vehicle && currentPendingScan.vehicle.registration_number) || '',
        dName,
        'ALCOHOL_ALERT'
      );
    }

    // Automatically expand the driver select collapse so MT NCO can immediately reassign driver
    const collapseEl = document.getElementById('collapseDriverSelect');
    if (collapseEl && !collapseEl.classList.contains('show')) {
      const bsCollapse = bootstrap.Collapse.getOrCreateInstance(collapseEl);
      bsCollapse.show();
    }

    // Update Gate decision banner on dashboard
    const decisionBox = document.getElementById('gate-decision-box');
    const titleElem = document.getElementById('decision-title');
    const msgElem = document.getElementById('decision-message');
    const driverElem = document.getElementById('decision-driver');
    if (decisionBox) {
      decisionBox.className = 'gate-decision-box DENIED ALCOHOL_ALERT';
      if (titleElem) titleElem.innerHTML = '<i class="fa-solid fa-wine-bottle text-warning me-2"></i>LIQUOR DETECTED! ACCESS BLOCKED';
      if (msgElem) msgElem.textContent = `🚨 AUTOMATIC SENSOR ALERT: Driver '${dName}' intoxicated (${val || '> 600'})! Change driver to proceed.`;
      if (driverElem) driverElem.innerHTML = `<span class="badge bg-danger px-2 py-1"><i class="fa-solid fa-triangle-exclamation me-1"></i>${dName} (INTOXICATED)</span>`;
    }

  } else if (status === 'PASSED') {
    isAlcoholLockoutActive = false;
    if (lastAnnouncedSobrietyState !== 'PASSED') {
      lastAnnouncedSobrietyState = 'PASSED';
      playChime(true);
    }
  }
}

async function simulateSobrietyTest(val) {
  const dName = (currentPendingScan && currentPendingScan.driver ? currentPendingScan.driver.name : null);
  const status = (val <= 600) ? 'PASSED' : 'FAILED';
  handleSobrietyUpdate(status, val, dName);

  try {
    await fetch('/api/device/sobriety_reading', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        alcohol_value: val,
        device_id: (currentPendingScan && currentPendingScan.device_id) || 'GATE01'
      })
    });
  } catch (err) {
    console.warn('Sobriety reading sync warning:', err);
  }
}

// ---------------- Driver Vehicle Authorization Helper Logic ---------------- //
function checkDriverAuthorizedForVehicle(authTypesStr, vehType, authStatus) {
  if (authStatus && authStatus.trim().toUpperCase() === 'NOT AUTHORIZED') {
    return false;
  }
  if (!vehType) return false;
  if (!authTypesStr) return false;
  const types = authTypesStr.split(',').map(t => t.trim().toUpperCase()).filter(Boolean);
  return types.includes(vehType.trim().toUpperCase());
}

function updateDriverVehicleAuthUI(isDriverAuth, authTypesStr, driverName, vehType, isVehicleAuth) {
  const driverAuthBadge = document.getElementById('modal-confirm-driver-auth-badge');
  const authBadge = document.getElementById('modal-confirm-auth-badge');
  const authTypesElem = document.getElementById('modal-confirm-driver-authtypes');
  const alertEl = document.getElementById('modal-driver-auth-alert');
  const alertTitle = document.getElementById('modal-driver-auth-title');
  const alertMsg = document.getElementById('modal-driver-auth-msg');

  if (authTypesElem) {
    authTypesElem.textContent = authTypesStr ? authTypesStr : 'None';
  }

  if (driverAuthBadge) {
    if (isDriverAuth) {
      driverAuthBadge.className = 'badge bg-success-subtle text-success border border-success-subtle px-2 py-1 fw-semibold';
      driverAuthBadge.innerHTML = '<i class="fa-solid fa-circle-check me-1"></i>AUTHORIZED';
    } else {
      driverAuthBadge.className = 'badge bg-danger text-white border border-danger px-2 py-1 fw-bold';
      driverAuthBadge.innerHTML = '<i class="fa-solid fa-triangle-exclamation me-1"></i>NOT AUTHORIZED';
    }
  }

  // Under vehicle plate: NOT AUTHORIZED if either vehicle is not authorized OR driver is not authorized for vehicle
  if (authBadge) {
    const overallAuth = (isVehicleAuth !== false) && isDriverAuth;
    if (overallAuth) {
      authBadge.className = 'badge bg-success-subtle text-success border border-success-subtle px-3 py-1 fs-6 fw-semibold';
      authBadge.textContent = 'AUTHORIZED';
    } else {
      authBadge.className = 'badge bg-danger text-white border border-danger px-3 py-1 fs-6 fw-bold';
      authBadge.innerHTML = '<i class="fa-solid fa-triangle-exclamation me-1"></i>NOT AUTHORIZED';
    }
  }

  // Warning alert banner in modal
  if (alertEl) {
    if (!isDriverAuth) {
      alertEl.classList.remove('d-none');
      alertEl.classList.add('d-flex');
      if (alertTitle) alertTitle.textContent = `DRIVER NOT AUTHORIZED FOR ${vehType ? vehType.toUpperCase() : 'THIS VEHICLE'}!`;
      if (alertMsg) {
        alertMsg.innerHTML = `Driver <strong>${driverName || 'Selected Driver'}</strong> is <strong>NOT AUTHORIZED</strong> to operate vehicle type <strong>${vehType || 'N/A'}</strong>.<br><span class="opacity-75">Driver's authorized vehicle types: ${authTypesStr || 'None'}</span>`;
      }
    } else {
      alertEl.classList.add('d-none');
      alertEl.classList.remove('d-flex');
    }
  }
}

// ---------------- Scan Confirmation Modal Logic ---------------- //
function openScanConfirmationModal(scanData) {
  if (!scanData || !scanData.vehicle) return;

  currentPendingScan = scanData;
  currentPendingScanId = scanData.scan_id || scanData.uid;

  // Automatic Voice Announcement: Speak Vehicle Number and Driver Name immediately on detection
  const detectedPlate = scanData.vehicle ? scanData.vehicle.registration_number : '';
  const detectedDriver = scanData.driver ? scanData.driver.name : '';
  let scanDir = 'IN';
  if (scanData.current_status === 'OUTSIDE' || scanData.recommended_direction === 'ENTRY' || scanData.is_outside === true) {
    scanDir = 'IN';
  } else if (scanData.current_status === 'INSIDE' || scanData.recommended_direction === 'EXIT') {
    scanDir = 'OUT';
  } else {
    scanDir = (getActiveNavbarDirection() === 'EXIT') ? 'OUT' : 'IN';
  }

  const vehType = (scanData.vehicle && scanData.vehicle.vehicle_type) || '';
  const initAuthTypes = (scanData.driver && scanData.driver.authorized_vehicle_types) || '';
  const initAuthStatus = (scanData.driver && scanData.driver.auth_status) || 'AUTHORIZED';
  const isInitialDriverAuth = scanData.driver && scanData.driver.is_authorized_for_vehicle !== undefined
    ? scanData.driver.is_authorized_for_vehicle
    : checkDriverAuthorizedForVehicle(initAuthTypes, vehType, initAuthStatus);

  if (!isInitialDriverAuth) {
    speakVehicleDetection(detectedPlate, detectedDriver, 'DRIVER_UNAUTHORIZED');
  } else {
    speakVehicleDetection(detectedPlate, detectedDriver, scanDir);
  }

  const modalElem = document.getElementById('scanConfirmationModal');
  if (!modalElem) return;

  // Sync with active navbar direction tab (ENTRY vs EXIT)
  currentModalDirection = getActiveNavbarDirection();
  renderModalDirectionButton();

  // Telemetry: UID
  const uidElem = document.getElementById('modal-confirm-uid');
  if (uidElem) uidElem.textContent = `UID: ${scanData.uid}`;

  // Vehicle Details
  const plateElem = document.getElementById('modal-confirm-plate');
  if (plateElem) plateElem.textContent = scanData.vehicle.registration_number || 'UNKNOWN';

  const typeElem = document.getElementById('modal-confirm-type');
  if (typeElem) typeElem.textContent = vehType || 'N/A';

  const isVehAuth = scanData.vehicle ? (scanData.vehicle.auth_status === 'AUTHORIZED') : true;

  // Current Location Status Pill - Harmonized Clean Style
  const statusPill = document.getElementById('modal-confirm-status-pill');
  if (statusPill) {
    const isOutside = scanData.current_status === 'OUTSIDE';
    if (isOutside) {
      statusPill.className = 'badge bg-white text-dark border border-secondary-subtle px-3 py-2 fs-6 fw-semibold w-100 text-wrap shadow-none';
      statusPill.innerHTML = '<i class="fa-solid fa-road me-1 text-primary"></i>CURRENTLY OUTSIDE &bull; Ready for IN';
    } else {
      statusPill.className = 'badge bg-white text-dark border border-secondary-subtle px-3 py-2 fs-6 fw-semibold w-100 text-wrap shadow-none';
      statusPill.innerHTML = '<i class="fa-solid fa-warehouse me-1 text-primary"></i>CURRENTLY INSIDE &bull; Ready for OUT';
    }
  }

  // Driver Details & Authorization verification
  scanData.initial_driver = Object.assign({}, scanData.driver || {});
  const driverNameElem = document.getElementById('modal-confirm-driver-name');
  if (driverNameElem) driverNameElem.textContent = scanData.driver.name || 'Registered Driver';

  const driverRankElem = document.getElementById('modal-confirm-driver-rank');
  if (driverRankElem) driverRankElem.textContent = scanData.driver.rank || scanData.driver.designation || 'Staff Driver';

  const driverArmyElem = document.getElementById('modal-confirm-driver-army');
  if (driverArmyElem) driverArmyElem.textContent = scanData.driver.armynumber ? `Army No: ${scanData.driver.armynumber}` : (scanData.driver.designation || '');

  const driverMobileElem = document.getElementById('modal-confirm-driver-mobile');
  if (driverMobileElem) driverMobileElem.textContent = scanData.driver.mobile || 'N/A';

  updateDriverVehicleAuthUI(isInitialDriverAuth, initAuthTypes, scanData.driver ? scanData.driver.name : '', vehType, isVehAuth);

  // Driver Selector with Authorization tagging
  const driverSelect = document.getElementById('modal-confirm-driver-select');
  if (driverSelect) {
    const keepTag = isInitialDriverAuth ? '' : ' - [NOT AUTHORIZED]';
    driverSelect.innerHTML = `<option value="">-- Keep Assigned Driver (${scanData.driver.name})${keepTag} --</option>`;
    if (scanData.pool_drivers && Array.isArray(scanData.pool_drivers)) {
      scanData.pool_drivers.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.id;
        opt.dataset.driverName = d.name;
        opt.dataset.driverRank = d.rank || '';
        opt.dataset.driverArmy = d.armynumber || '';
        opt.dataset.driverMobile = d.mobile || '';
        opt.dataset.authTypes = d.authorized_vehicle_types || '';
        opt.dataset.authStatus = d.auth_status || 'AUTHORIZED';

        const isDrvAuth = d.is_authorized_for_vehicle !== undefined
          ? d.is_authorized_for_vehicle
          : checkDriverAuthorizedForVehicle(d.authorized_vehicle_types, vehType, d.auth_status);
        opt.dataset.isAuthorized = isDrvAuth ? 'true' : 'false';

        const statusLabel = isDrvAuth ? '• AUTHORIZED' : '• ⚠️ NOT AUTHORIZED';
        opt.textContent = `${d.name} (${d.rank || d.armynumber || 'Driver'}) ${statusLabel}`;
        if (!isDrvAuth) {
          opt.style.color = '#dc2626';
          opt.style.fontWeight = '600';
        }
        driverSelect.appendChild(opt);
      });
    }
  }

  // Close driver change collapse if open
  const collapseEl = document.getElementById('collapseDriverSelect');
  if (collapseEl && collapseEl.classList.contains('show')) {
    const bsCollapse = bootstrap.Collapse.getInstance(collapseEl);
    if (bsCollapse) bsCollapse.hide();
  }

  // Reset success banner and button layout
  isConfirmationSuccessPending = false;
  const successBanner = document.getElementById('modal-confirm-success-banner');
  if (successBanner) {
    successBanner.classList.add('d-none');
    successBanner.classList.remove('d-flex');
  }

  const colConfIn = document.getElementById('col-confirm-in');
  const colConfOut = document.getElementById('col-confirm-out');
  const colLiqIn = document.getElementById('col-liquor-in');
  const colLiqOut = document.getElementById('col-liquor-out');

  const btnInReset = document.getElementById('btn-confirm-in');
  const btnOutReset = document.getElementById('btn-confirm-out');
  if (btnInReset) {
    btnInReset.disabled = false;
    btnInReset.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket fs-4"></i><span>CONFIRM IN (Arrival to MT Garage)</span>';
  }
  if (btnOutReset) {
    btnOutReset.disabled = false;
    btnOutReset.innerHTML = '<i class="fa-solid fa-arrow-right-from-bracket fs-4"></i><span>CONFIRM OUT (Outbound Dispatch)</span>';
  }

  if (colConfIn) {
    colConfIn.style.display = '';
    colConfIn.className = 'col-12';
  }
  if (colConfOut) {
    colConfOut.style.display = '';
    colConfOut.className = 'col-12';
  }
  if (colLiqIn) {
    colLiqIn.style.display = 'none';
    colLiqIn.className = 'col-12 d-none';
  }
  if (colLiqOut) {
    colLiqOut.style.display = 'none';
    colLiqOut.className = 'col-12 d-none';
  }

  const remarksInput = document.getElementById('modal-confirm-remarks');
  if (remarksInput) remarksInput.value = '';

  // Determine initial sobriety state (Bypass alcohol test only if vehicle is actually outside / returning IN)
  const isVehicleOutside = (scanData.current_status === 'OUTSIDE' || scanData.is_outside === true) && scanData.current_status !== 'INSIDE';
  const scanAlcVal = scanData && scanData.alcohol_value !== undefined && scanData.alcohol_value !== null ? Number(scanData.alcohol_value) : null;

  if (isVehicleOutside || scanData.sobriety_status === 'NOT_REQUIRED') {
    currentSobrietyState = 'NOT_REQUIRED';
    lastSobrietyReadingValue = null;
  } else if (scanData && (scanData.sobriety_status === 'FAILED' || scanData.alcohol_detected || (scanAlcVal !== null && !isNaN(scanAlcVal) && scanAlcVal > 600))) {
    currentSobrietyState = 'FAILED';
    lastSobrietyReadingValue = scanAlcVal;
  } else if (scanData && scanData.sobriety_status === 'PASSED') {
    currentSobrietyState = 'PASSED';
    lastSobrietyReadingValue = scanAlcVal;
  } else {
    currentSobrietyState = 'AWAITING';
    lastSobrietyReadingValue = scanAlcVal;
  }

  lastAnnouncedSobrietyState = null;
  isAlcoholLockoutActive = (currentSobrietyState === 'FAILED');
  isAutoDispatching = false;

  // Apply UI: Show check-in UI if outside, confirm button for manual operator click, lock if > 600
  applySobrietyUI(currentSobrietyState, lastSobrietyReadingValue, scanData.driver ? scanData.driver.name : null);

  scanConfirmationModalInstance = bootstrap.Modal.getOrCreateInstance(modalElem);
  scanConfirmationModalInstance.show();
  updateVoiceButtons();
  playChime(true);

  if (!isVehicleOutside) {
    if (currentSobrietyState === 'FAILED') {
      handleSobrietyUpdate('FAILED', scanAlcVal, scanData.driver ? scanData.driver.name : null);
    }
  }
}

async function onConfirmDriverChanged(driverId) {
  if (!currentPendingScan) return;
  const select = document.getElementById('modal-confirm-driver-select');
  const nameElem = document.getElementById('modal-confirm-driver-name');
  const rankElem = document.getElementById('modal-confirm-driver-rank');
  const armyElem = document.getElementById('modal-confirm-driver-army');
  const mobileElem = document.getElementById('modal-confirm-driver-mobile');

  let newDriverName = (currentPendingScan.driver && currentPendingScan.driver.name) || 'Assigned Driver';
  const vehType = (currentPendingScan.vehicle && currentPendingScan.vehicle.vehicle_type) || '';
  const isVehAuth = currentPendingScan.vehicle ? (currentPendingScan.vehicle.auth_status === 'AUTHORIZED') : true;

  let authTypes = '';
  let authStatus = 'AUTHORIZED';
  let isDrvAuth = false;

  if (!driverId) {
    // Reset to initial driver
    const initDrv = currentPendingScan.initial_driver || currentPendingScan.driver;
    if (initDrv) {
      newDriverName = initDrv.name;
      authTypes = initDrv.authorized_vehicle_types || '';
      authStatus = initDrv.auth_status || 'AUTHORIZED';
      isDrvAuth = checkDriverAuthorizedForVehicle(authTypes, vehType, authStatus);
      if (nameElem) nameElem.textContent = initDrv.name;
      if (rankElem) rankElem.textContent = initDrv.rank || 'Staff Driver';
      if (armyElem) armyElem.textContent = initDrv.armynumber ? `Army No: ${initDrv.armynumber}` : '';
      if (mobileElem) mobileElem.textContent = initDrv.mobile || 'N/A';
    }
  } else {
    const selectedOpt = select.options[select.selectedIndex];
    if (selectedOpt) {
      newDriverName = selectedOpt.dataset.driverName || selectedOpt.getAttribute('data-driver-name') || selectedOpt.text.split('(')[0].trim();
      authTypes = selectedOpt.dataset.authTypes || '';
      authStatus = selectedOpt.dataset.authStatus || 'AUTHORIZED';
      isDrvAuth = selectedOpt.dataset.isAuthorized === 'true' || checkDriverAuthorizedForVehicle(authTypes, vehType, authStatus);
      if (nameElem) nameElem.textContent = newDriverName;
      if (rankElem) rankElem.textContent = selectedOpt.dataset.driverRank || 'Pool Driver';
      if (armyElem) armyElem.textContent = selectedOpt.dataset.driverArmy ? `Army No: ${selectedOpt.dataset.driverArmy}` : '';
      if (mobileElem) mobileElem.textContent = selectedOpt.dataset.driverMobile || 'N/A';
    }
    console.log("VMS: New driver selected ->", newDriverName, "Authorized for vehicle?", isDrvAuth);
  }

  // Update Authorization Badges & Alert immediately
  updateDriverVehicleAuthUI(isDrvAuth, authTypes, newDriverName, vehType, isVehAuth);

  // Critical requirement: Reset sobriety state to AWAITING_TEST for the replacement driver!
  currentSobrietyState = 'AWAITING_TEST';
  lastSobrietyReadingValue = null;
  lastAnnouncedSobrietyState = null;
  isAlcoholLockoutActive = false;

  if (currentPendingScan) {
    currentPendingScan.sobriety_status = 'AWAITING_TEST';
    currentPendingScan.sobriety_passed = false;
    currentPendingScan.alcohol_value = null;
    currentPendingScan.alcohol_detected = false;
    if (driverId) {
      currentPendingScan.driver = currentPendingScan.driver || {};
      currentPendingScan.driver.id = driverId;
      currentPendingScan.driver.name = newDriverName;
      currentPendingScan.driver.authorized_vehicle_types = authTypes;
      currentPendingScan.driver.auth_status = authStatus;
      currentPendingScan.driver.is_authorized_for_vehicle = isDrvAuth;
    }
  }

  // Lock confirm buttons, remove glow, reset status box to AWAITING TEST
  applySobrietyUI('AWAITING_TEST', null, newDriverName);

  // Reset auto-dispatching flag
  isAutoDispatching = false;

  // Prompt the replacement driver via voice (or speak unauthorized alert if driver is not authorized)
  const vehPlate = (currentPendingScan && currentPendingScan.vehicle && currentPendingScan.vehicle.registration_number) || '';
  if (!isDrvAuth) {
    speakVehicleDetection(vehPlate, newDriverName, 'DRIVER_UNAUTHORIZED');
  } else {
    speakVehicleDetection(vehPlate, newDriverName, 'DRIVER_CHANGE');
  }

  // Notify backend to update the pending scan's driver and reset sobriety test
  try {
    const resp = await fetch('/api/rfid/update_pending_driver', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        driver_id: driverId || null,
        driver_name: newDriverName
      })
    });
    const resData = await resp.json();
    if (resData.success && resData.pending_scan) {
      const savedInit = currentPendingScan.initial_driver;
      currentPendingScan = resData.pending_scan;
      currentPendingScan.initial_driver = savedInit;
      if (resData.pending_scan.driver && resData.pending_scan.driver.is_authorized_for_vehicle !== undefined) {
        updateDriverVehicleAuthUI(resData.pending_scan.driver.is_authorized_for_vehicle, resData.pending_scan.driver.authorized_vehicle_types, newDriverName, vehType, isVehAuth);
      }
    }
  } catch (err) {
    console.warn('Failed to update driver on backend:', err);
  }
}

async function confirmScan(direction) {
  if (!currentPendingScan) return;

  const isVehicleOutside = (currentPendingScan.current_status === 'OUTSIDE' || currentPendingScan.recommended_direction === 'ENTRY' || currentPendingScan.is_outside === true || direction === 'ENTRY');

  // Strict Breathalyzer Sobriety Enforcement: Only block for OUTBOUND dispatch when alcohol is detected
  if (!isVehicleOutside && (currentSobrietyState === 'FAILED' || isAlcoholLockoutActive)) {
    alert('Action Prohibited: Liquor has been detected on this driver! Outbound dispatch is strictly blocked.\nPlease assign a replacement driver.');
    return;
  }

  const isInside = currentPendingScan.current_status === 'INSIDE';
  const vehPlate = (currentPendingScan.vehicle && currentPendingScan.vehicle.registration_number) || 'Vehicle';

  if (isInside && direction === 'ENTRY') {
    alert(`Action Not Allowed: ${vehPlate} is already INSIDE MT Garage.\nCannot record ENTRY (IN). Only EXIT (OUT) is permitted.`);
    return;
  }
  if (!isInside && direction === 'EXIT') {
    alert(`Action Not Allowed: ${vehPlate} is already OUTSIDE on a trip.\nCannot record EXIT (OUT). Only ENTRY (IN) is permitted.`);
    return;
  }

  const driverSelect = document.getElementById('modal-confirm-driver-select');
  let selectedDriverId = null;
  let selectedDriverName = null;
  let isDriverAuthorized = true;

  if (driverSelect && driverSelect.value) {
    selectedDriverId = driverSelect.value;
    const selectedOpt = driverSelect.options[driverSelect.selectedIndex];
    selectedDriverName = selectedOpt ? selectedOpt.dataset.driverName : null;
    isDriverAuthorized = selectedOpt ? (selectedOpt.dataset.isAuthorized === 'true') : true;
  } else {
    selectedDriverName = currentPendingScan.driver.name;
    selectedDriverId = currentPendingScan.driver.id;
    isDriverAuthorized = currentPendingScan.driver && currentPendingScan.driver.is_authorized_for_vehicle !== false;
  }

  if (!isDriverAuthorized) {
    const vehType = (currentPendingScan.vehicle && currentPendingScan.vehicle.vehicle_type) || 'Vehicle';
    const proceed = confirm(`⚠️ UNAUTHORIZED WARNING: Driver ${selectedDriverName || 'Selected Driver'} is NOT AUTHORIZED to operate vehicle type '${vehType}'.\n\nDo you want to proceed under manual supervisor override?`);
    if (!proceed) {
      return;
    }
  }

  const btnIn = document.getElementById('btn-confirm-in');
  const btnOut = document.getElementById('btn-confirm-out');
  const targetBtn = direction === 'ENTRY' ? btnIn : btnOut;

  if (btnIn) btnIn.disabled = true;
  if (btnOut) btnOut.disabled = true;

  if (targetBtn) {
    targetBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Confirming...';
  }

  const remarksInput = document.getElementById('modal-confirm-remarks');
  const remarks = remarksInput ? remarksInput.value.trim() : '';

  try {
    const res = await fetch('/api/movements/confirm_scan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        uid: currentPendingScan.uid,
        vehicle_id: (currentPendingScan.vehicle && currentPendingScan.vehicle.id) || null,
        direction: direction,
        driver_id: selectedDriverId,
        driver_name: selectedDriverName,
        remarks: remarks,
        device_id: currentPendingScan.device_id || 'GATE01'
      })
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      alert(`Confirmation Failed: ${data.message || 'Unknown error'}`);
      if (btnIn) btnIn.disabled = false;
      if (btnOut) btnOut.disabled = false;
      return;
    }

    const result = data.data;

    // Show SUCCESS STATUS inside the confirmation modal
    isConfirmationSuccessPending = true;

    const successBanner = document.getElementById('modal-confirm-success-banner');
    const successTitle = document.getElementById('modal-confirm-success-title');
    const successBadge = document.getElementById('modal-confirm-success-badge');
    const successMsg = document.getElementById('modal-confirm-success-msg');
    const audioStatus = document.getElementById('modal-confirm-audio-status');
    const wrapIn = document.getElementById('wrapper-confirm-in');
    const wrapOut = document.getElementById('wrapper-confirm-out');

    const isOut = (direction === 'EXIT' || result.direction === 'EXIT' || result.decision === 'EXIT_RECORDED');
    const hindiScript = isOut 
      ? 'Gaadi ab baahar jaa rahi hai.'
      : 'Gaadi ab andar aa rahi hai.';

    if (successBanner) {
      successBanner.classList.remove('d-none');
      successBanner.classList.add('d-flex');
    }
    if (successTitle) {
      successTitle.textContent = isOut ? '✅ OUTBOUND DISPATCH CONFIRMED' : '✅ MT ARRIVAL CONFIRMED';
    }
    if (successBadge) {
      successBadge.textContent = 'GATE OPENING';
    }
    if (successMsg) {
      successMsg.textContent = hindiScript;
    }
    if (audioStatus) {
      audioStatus.innerHTML = '<span class="spinner-grow spinner-grow-sm text-light me-1" role="status"></span>Announcing... Modal will close automatically.';
    }

    // Hide confirm button wrappers while success banner is displayed
    if (wrapIn) wrapIn.style.display = 'none';
    if (wrapOut) wrapOut.style.display = 'none';

    // Update inside & outside counters immediately (Gate Control)
    const insideCounter = document.getElementById('live-inside-count');
    if (insideCounter && result.inside_count !== undefined) {
      insideCounter.textContent = result.inside_count;
    }
    const outsideCounter = document.getElementById('live-outside-count');
    if (outsideCounter && result.outside_count !== undefined) {
      outsideCounter.textContent = result.outside_count;
    }

    // Update Dashboard big counters immediately (e.g. on http://192.168.1.39:5000/)
    const dashOutside = document.getElementById('stat-vehicles-outside');
    if (dashOutside && result.outside_count !== undefined) {
      dashOutside.textContent = result.outside_count;
    }
    const dashInside = document.getElementById('stat-vehicles-inside');
    if (dashInside && result.inside_count !== undefined) {
      dashInside.textContent = result.inside_count;
    }

    // Update Main Gate Decision Banner
    const decisionBox = document.getElementById('gate-decision-box');
    const titleElem = document.getElementById('decision-title');
    const plateElem = document.getElementById('decision-plate');
    const typeElem = document.getElementById('decision-type');
    const driverElem = document.getElementById('decision-driver');
    const uidElem = document.getElementById('decision-uid');
    const msgElem = document.getElementById('decision-message');
    const timeElem = document.getElementById('decision-time');

    if (decisionBox) {
      if (result.direction === 'EXIT') {
        decisionBox.className = 'gate-decision-box EXIT';
        if (titleElem) titleElem.innerHTML = '<i class="fa-solid fa-arrow-right-from-bracket me-2"></i>EXIT RECORDED - OUTBOUND DISPATCH';
        if (msgElem) msgElem.textContent = `Vehicle Dispatched (OUTSIDE) with Driver: ${result.driver_name}! Barrier Opening...`;
      } else {
        decisionBox.className = 'gate-decision-box ALLOWED';
        if (titleElem) titleElem.innerHTML = '<i class="fa-solid fa-circle-check me-2"></i>ENTRY ALLOWED - RETURNED TO MT GARAGE';
        if (msgElem) msgElem.textContent = `Arrival Confirmed for ${result.driver_name} (Duration: ${result.duration || 'N/A'})! Barrier Opening...`;
      }

      if (plateElem) plateElem.textContent = result.vehicle_number;
      if (typeElem) typeElem.textContent = result.vehicle_type;
      if (driverElem) driverElem.innerHTML = `<span class="badge bg-success px-2 py-1"><i class="fa-solid fa-user-check me-1"></i>${result.driver_name}</span>`;
      if (uidElem) uidElem.textContent = currentPendingScan ? currentPendingScan.uid : '-';
      if (timeElem) timeElem.textContent = result.timestamp || '';
    }

    // Open barrier actuator
    const delayElem = document.getElementById('barrier-auto-delay');
    const autoCloseSec = delayElem ? (parseInt(delayElem.textContent, 10) || 4) : 4;
    triggerBarrierOpen(autoCloseSec);

    // Suppress duplicate interrupted speech from upcoming poll
    lastKnownEventKey = `${result.movement_id || ''}-${result.vehicle_number}-${result.decision}`;
    _suppressGateFeedSpeechUntil = Date.now() + 8000;

    // Reset back to standby after auto close delay + 2.5s
    if (decisionResetTimer) clearTimeout(decisionResetTimer);
    decisionResetTimer = setTimeout(() => {
      resetGateDecisionToStandby();
    }, (autoCloseSec + 2.5) * 1000);

    currentPendingScan = null;
    currentPendingScanId = null;

    // Trigger poll update
    pollGateFeed();

    // Speak Hindi announcement and only auto complete / close modal when speech finishes!
    speakConfirmationAndCloseModal(hindiScript);

  } catch (err) {
    console.error('Error confirming scan:', err);
    alert('Failed to connect to gate server. Please try again.');
    if (btnIn) btnIn.disabled = false;
    if (btnOut) btnOut.disabled = false;
  }
}

async function reportLiquorDetected(direction) {
  if (!currentPendingScan) return;

  const vehPlate = (currentPendingScan.vehicle && currentPendingScan.vehicle.registration_number) || 'Vehicle';
  const driverSelect = document.getElementById('modal-confirm-driver-select');
  let selectedDriverName = null;
  let selectedDriverId = null;

  if (driverSelect && driverSelect.value) {
    selectedDriverId = driverSelect.value;
    const selectedOpt = driverSelect.options[driverSelect.selectedIndex];
    selectedDriverName = selectedOpt ? selectedOpt.dataset.driverName : null;
  } else {
    selectedDriverName = (currentPendingScan.driver && currentPendingScan.driver.name) || 'Assigned Driver';
    selectedDriverId = currentPendingScan.driver ? currentPendingScan.driver.id : null;
  }

  const dirLabel = direction === 'EXIT' ? 'OUTBOUND DISPATCH (OUT)' : 'ENTRY RETURN (IN)';
  // Directly flag violation without blocking window.confirm popup
  const btnIn = document.getElementById('btn-confirm-in');
  const btnOut = document.getElementById('btn-confirm-out');
  const btnLiqIn = document.getElementById('btn-liquor-in');
  const btnLiqOut = document.getElementById('btn-liquor-out');
  const activeLiqBtn = direction === 'ENTRY' ? btnLiqIn : btnLiqOut;

  if (btnIn) btnIn.disabled = true;
  if (btnOut) btnOut.disabled = true;
  if (btnLiqIn) btnLiqIn.disabled = true;
  if (btnLiqOut) btnLiqOut.disabled = true;

  if (activeLiqBtn) {
    activeLiqBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Flagging...';
  }

  try {
    const res = await fetch('/api/movements/report_alcohol', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        uid: currentPendingScan.uid,
        vehicle_id: (currentPendingScan.vehicle && currentPendingScan.vehicle.id) || null,
        direction: direction,
        driver_id: selectedDriverId,
        driver_name: selectedDriverName,
        device_id: currentPendingScan.device_id || 'GATE01',
        remarks: `Guard Manual Sobriety Check: Driver '${selectedDriverName}' tested positive for Liquor. ${direction} blocked.`
      })
    });

    const data = await res.json();
    if (!res.ok || !data.success) {
      alert(`Failed to record violation: ${data.message || 'Unknown error'}`);
      if (btnIn) btnIn.disabled = false;
      if (btnOut) btnOut.disabled = false;
      if (btnLiqIn) btnLiqIn.disabled = false;
      if (btnLiqOut) btnLiqOut.disabled = false;
      return;
    }

    // Success: Hide confirmation modal
    closeScanConfirmationModal(false);

    const result = data.data;

    // Update Gate Decision Banner on Dashboard / Gate Control
    const decisionBox = document.getElementById('gate-decision-box');
    const titleElem = document.getElementById('decision-title');
    const plateElem = document.getElementById('decision-plate');
    const typeElem = document.getElementById('decision-type');
    const driverElem = document.getElementById('decision-driver');
    const uidElem = document.getElementById('decision-uid');
    const msgElem = document.getElementById('decision-message');
    const timeElem = document.getElementById('decision-time');

    if (decisionBox) {
      decisionBox.className = 'gate-decision-box DENIED ALCOHOL_ALERT';
      if (titleElem) titleElem.innerHTML = '<i class="fa-solid fa-wine-bottle text-warning me-2"></i>LIQUOR DETECTED! ACCESS BLOCKED';
      if (msgElem) msgElem.textContent = `🚨 CRITICAL SOBRIETY ALERT: Driver '${result.driver_name}' intoxicated! Gate locked.`;
      if (plateElem) plateElem.textContent = result.vehicle_number;
      if (typeElem) typeElem.textContent = result.vehicle_type || 'Vehicle';
      if (driverElem) driverElem.innerHTML = `<span class="badge bg-danger px-2 py-1"><i class="fa-solid fa-triangle-exclamation me-1"></i>${result.driver_name} (INTOXICATED)</span>`;
      if (uidElem) uidElem.textContent = currentPendingScan ? currentPendingScan.uid : '-';
      if (timeElem) timeElem.textContent = result.timestamp || '';
    }

    // Play error sound and speak alert
    playChime(false);
    speakVehicleDetection(result.vehicle_number, result.driver_name, 'ALCOHOL_ALERT');

    // Reset decision banner after 8s
    if (decisionResetTimer) clearTimeout(decisionResetTimer);
    decisionResetTimer = setTimeout(() => {
      resetGateDecisionToStandby();
    }, 8000);

    currentPendingScan = null;
    currentPendingScanId = null;

    // Refresh gate feed
    pollGateFeed();

  } catch (err) {
    console.error('Error reporting liquor detection:', err);
    alert('Failed to connect to gate server.');
    if (btnIn) btnIn.disabled = false;
    if (btnOut) btnOut.disabled = false;
    if (btnLiqIn) btnLiqIn.disabled = false;
    if (btnLiqOut) btnLiqOut.disabled = false;
  }
}

function triggerModalAlcoholLockout(evtOrScan) {
  const dName = (evtOrScan && evtOrScan.driver && evtOrScan.driver.name) || (evtOrScan && evtOrScan.driver_name) || (currentPendingScan && currentPendingScan.driver && currentPendingScan.driver.name) || 'Driver';
  const rawAlc = (evtOrScan && evtOrScan.alcohol_value) || (currentPendingScan && currentPendingScan.alcohol_value) || 850;
  handleSobrietyUpdate('FAILED', Number(rawAlc) || 850, dName);
}

async function cancelPendingScan() {
  stopAllAudio();
  try {
    await fetch('/api/rfid/cancel_pending_scan', { method: 'POST' });
  } catch (e) {}
  currentPendingScan = null;
  currentPendingScanId = null;
  closeScanConfirmationModal(true);
}

function closeScanConfirmationModal(cancelSpeech = true) {
  if (cancelSpeech) {
    stopAllAudio();
  }
  const modalElem = document.getElementById('scanConfirmationModal');
  if (modalElem) {
    const modal = bootstrap.Modal.getInstance(modalElem);
    if (modal) modal.hide();
  }
}


// ---------------- Google en-IN / Neerja Voice — Modal Speak Button ---------------- //
function speakVehicleDetailsHindi() {
  if (!voiceAnnouncementsEnabled) return;
  if (!currentPendingScan || !currentPendingScan.vehicle) return;

  const veh    = currentPendingScan.vehicle;
  const driver = currentPendingScan.driver || {};
  const plate  = (veh.registration_number || '').trim().toUpperCase();
  const isOutside = currentPendingScan.current_status === 'OUTSIDE';

  const plateSpoken = formatPlateSpoken(plate);

  let text = plateSpoken ? `Gaadi number ${plateSpoken}. ` : 'Gaadi scan hui. ';
  if (driver && driver.name) text += `Driver ${driver.name}, `;
  text += isOutside ? 'gaadi andar aana chahti hai.' : 'gaadi baahar jaana chahti hai.';

  // Visual feedback on button
  const btn = document.getElementById('btn-speak-hindi');
  const origHtml = btn ? btn.innerHTML : '';
  if (btn) {
    btn.classList.add('btn-primary', 'text-white');
    btn.classList.remove('btn-outline-primary');
    btn.innerHTML = '<i class="fa-solid fa-volume-high fa-beat me-1"></i><span class="small fw-bold" style="font-size:0.72rem;">बोल रहा है...</span>';
  }
  const resetBtn = () => {
    if (btn) {
      btn.classList.remove('btn-primary','text-white');
      btn.classList.add('btn-outline-primary');
      btn.innerHTML = origHtml;
    }
  };

  stopAllAudio();
  speakWithNeerjaGoogleVoice(text, resetBtn);
}

function speakConfirmationAndCloseModal(text) {
  let hasCompleted = false;
  const finishAndClose = () => {
    if (hasCompleted) return;
    hasCompleted = true;
    isConfirmationSuccessPending = false;
    closeScanConfirmationModal(false);
  };

  if (!voiceAnnouncementsEnabled) {
    setTimeout(finishAndClose, 1800);
    return;
  }

  playChime(true);
  stopAllAudio();
  speakWithNeerjaGoogleVoice(text, finishAndClose);
}

// Sync buttons and modal lifecycle listeners on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  updateVoiceButtons();

  const modalElem = document.getElementById('scanConfirmationModal');
  if (modalElem) {
    modalElem.addEventListener('hide.bs.modal', () => {
      // IF MODAL IS CLOSED BEFORE THE SPEAK IS COMPLETE, THE SPEAK SHOULD ALSO STOP
      stopAllAudio();
      isConfirmationSuccessPending = false;
    });
    modalElem.addEventListener('hidden.bs.modal', () => {
      stopAllAudio();
      isConfirmationSuccessPending = false;
      const successBanner = document.getElementById('modal-confirm-success-banner');
      if (successBanner) {
        successBanner.classList.add('d-none');
        successBanner.classList.remove('d-flex');
      }
    });
  }
});
