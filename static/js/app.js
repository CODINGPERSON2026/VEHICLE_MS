/**
 * ============================================================================
 * SMART RFID + ANPR VEHICLE GATE SYSTEM - CLIENT APPLICATION LOGIC
 * ============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
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

  // Restore saved state (no animation on load)
  if (localStorage.getItem('sidebarCollapsed') === 'true') {
    sidebar.classList.add('collapsed');
    sidebar.style.transition = 'none';
    requestAnimationFrame(() => { sidebar.style.transition = ''; });
  }

  toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    const isCollapsed = sidebar.classList.contains('collapsed');
    localStorage.setItem('sidebarCollapsed', isCollapsed);

    // Swap icon: bars ↔ bars-staggered
    const icon = toggleBtn.querySelector('i');
    if (isCollapsed) {
      icon.className = 'fa-solid fa-bars-staggered';
    } else {
      icon.className = 'fa-solid fa-bars';
    }
  });

  // Set correct icon on load
  if (sidebar.classList.contains('collapsed')) {
    const icon = toggleBtn.querySelector('i');
    if (icon) icon.className = 'fa-solid fa-bars-staggered';
  }
}

// ---------------- Live Clock ---------------- //
function initClock() {
  const clockElem = document.getElementById('live-clock');
  if (!clockElem) return;

  function update() {
    const now = new Date();
    clockElem.textContent = now.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
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

    // Check for pending RFID scan awaiting guard confirmation (e.g. from ESP32 hardware reader)
    if (data.pending_scan && data.pending_scan.scan_id) {
      if (currentPendingScanId !== data.pending_scan.scan_id) {
        openScanConfirmationModal(data.pending_scan);
      }
    } else if (!data.pending_scan && currentPendingScanId) {
      const btnIn = document.getElementById('btn-confirm-in');
      if (btnIn && !btnIn.disabled) {
        currentPendingScanId = null;
        currentPendingScan = null;
        closeScanConfirmationModal();
      }
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
    if (titleElem) titleElem.innerHTML = '<i class="fa-solid fa-ban me-2"></i>ACCESS DENIED';
    if (msgElem) msgElem.textContent = `Denied: ${evt.status} (${evt.remarks || ''})`;
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
function playChime(isSuccess) {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();
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
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();
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

// ---------------- RFID Card Enrollment Listener ---------------- //
let enrollmentInterval = null;

function initRFIDEnrollmentListener() {
  const enrollModal = document.getElementById('enrollCardModal');
  if (!enrollModal) return;

  const pollEnrollment = async () => {
    try {
      const res = await fetch('/api/rfid/latest_enrollment');
      if (!res.ok) return;
      const data = await res.json();
      if (data.active && data.data && data.data.uid) {
        const uidInput = document.getElementById('assign-uid-input');
        const statusText = document.getElementById('enroll-listener-status');
        if (uidInput && uidInput.value !== data.data.uid) {
          uidInput.value = data.data.uid;
          uidInput.classList.add('is-valid');
          setTimeout(() => uidInput.classList.remove('is-valid'), 2500);
        }
        if (statusText) {
          statusText.innerHTML = `<span class="text-success fw-bold"><i class="fa-solid fa-circle-check me-1"></i>Tag Captured: ${data.data.uid}</span> <span class="badge bg-secondary-subtle text-secondary ms-1">${data.data.device_id || 'ESP32'}</span>`;
        }
      }
    } catch (err) {}
  };

  enrollModal.addEventListener('shown.bs.modal', () => {
    const statusText = document.getElementById('enroll-listener-status');
    const uidInput = document.getElementById('assign-uid-input');
    if (statusText && (!uidInput || !uidInput.value)) {
      statusText.innerHTML = '<span class="pulse-dot pulse-green me-1"></span>Waiting for card scan on ESP32 reader...';
    }

    // Check immediately, then poll every 1.5s
    pollEnrollment();
    enrollmentInterval = setInterval(pollEnrollment, 1500);
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
        conflictMsg.innerHTML = `<strong>ALREADY INSIDE:</strong> <code>${vehPlate}</code> is already in the depot. <strong>ENTRY (IN) is blocked.</strong> Only EXIT (OUT) is allowed.`;
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
        hintElem.innerHTML = `<span class="text-success fw-semibold"><i class="fa-solid fa-check-circle me-1"></i>Inside Depot &bull; Ready to Dispatch OUT</span>`;
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

// ---------------- Scan Confirmation Modal Logic ---------------- //
function openScanConfirmationModal(scanData) {
  if (!scanData || !scanData.vehicle) return;

  currentPendingScan = scanData;
  currentPendingScanId = scanData.scan_id || scanData.uid;

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
  if (typeElem) typeElem.textContent = scanData.vehicle.vehicle_type || 'N/A';

  const authBadge = document.getElementById('modal-confirm-auth-badge');
  if (authBadge) {
    const isAuth = scanData.vehicle.auth_status === 'AUTHORIZED';
    authBadge.className = isAuth ? 'badge bg-success px-3 py-1 fs-6' : 'badge bg-danger px-3 py-1 fs-6';
    authBadge.textContent = scanData.vehicle.auth_status || 'NOT AUTHORIZED';
  }

  // Current Location Status Pill
  const statusPill = document.getElementById('modal-confirm-status-pill');
  if (statusPill) {
    const isOutside = scanData.current_status === 'OUTSIDE';
    if (isOutside) {
      statusPill.className = 'badge bg-warning text-dark px-3 py-1 fs-6 fw-bold shadow-sm';
      statusPill.innerHTML = '<i class="fa-solid fa-road me-1"></i>CURRENTLY OUTSIDE (Can only Enter IN)';
    } else {
      statusPill.className = 'badge bg-success text-white px-3 py-1 fs-6 fw-bold shadow-sm';
      statusPill.innerHTML = '<i class="fa-solid fa-warehouse me-1"></i>CURRENTLY INSIDE (Can only Exit OUT)';
    }
  }

  // Driver Details
  const driverNameElem = document.getElementById('modal-confirm-driver-name');
  if (driverNameElem) driverNameElem.textContent = scanData.driver.name || 'Registered Driver';

  const driverRankElem = document.getElementById('modal-confirm-driver-rank');
  if (driverRankElem) driverRankElem.textContent = scanData.driver.rank || scanData.driver.designation || 'Staff Driver';

  const driverArmyElem = document.getElementById('modal-confirm-driver-army');
  if (driverArmyElem) driverArmyElem.textContent = scanData.driver.armynumber ? `Army No: ${scanData.driver.armynumber}` : (scanData.driver.designation || '');

  const driverMobileElem = document.getElementById('modal-confirm-driver-mobile');
  if (driverMobileElem) driverMobileElem.textContent = scanData.driver.mobile || 'N/A';

  // Driver Selector
  const driverSelect = document.getElementById('modal-confirm-driver-select');
  if (driverSelect) {
    driverSelect.innerHTML = `<option value="">-- Keep Assigned Driver (${scanData.driver.name}) --</option>`;
    if (scanData.pool_drivers && Array.isArray(scanData.pool_drivers)) {
      scanData.pool_drivers.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.id;
        opt.dataset.driverName = d.name;
        opt.dataset.driverRank = d.rank || '';
        opt.dataset.driverArmy = d.armynumber || '';
        opt.dataset.driverMobile = d.mobile || '';
        opt.textContent = `${d.name} (${d.rank || d.armynumber || 'Driver'})`;
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

  // Reset button states
  const btnIn = document.getElementById('btn-confirm-in');
  if (btnIn) {
    btnIn.disabled = false;
    btnIn.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket fs-4"></i><span>CONFIRM IN (Arrival to Depot)</span>';
  }
  const btnOut = document.getElementById('btn-confirm-out');
  if (btnOut) {
    btnOut.disabled = false;
    btnOut.innerHTML = '<i class="fa-solid fa-arrow-right-from-bracket fs-4"></i><span>CONFIRM OUT (Outbound Dispatch)</span>';
  }

  const remarksInput = document.getElementById('modal-confirm-remarks');
  if (remarksInput) remarksInput.value = '';

  scanConfirmationModalInstance = bootstrap.Modal.getOrCreateInstance(modalElem);
  scanConfirmationModalInstance.show();
  playChime(true);
}

function onConfirmDriverChanged(driverId) {
  if (!currentPendingScan) return;
  const select = document.getElementById('modal-confirm-driver-select');
  const nameElem = document.getElementById('modal-confirm-driver-name');
  const rankElem = document.getElementById('modal-confirm-driver-rank');
  const armyElem = document.getElementById('modal-confirm-driver-army');
  const mobileElem = document.getElementById('modal-confirm-driver-mobile');

  if (!driverId) {
    // Reset to default
    if (nameElem) nameElem.textContent = currentPendingScan.driver.name;
    if (rankElem) rankElem.textContent = currentPendingScan.driver.rank || 'Staff Driver';
    if (armyElem) armyElem.textContent = currentPendingScan.driver.armynumber ? `Army No: ${currentPendingScan.driver.armynumber}` : '';
    if (mobileElem) mobileElem.textContent = currentPendingScan.driver.mobile || 'N/A';
    return;
  }

  const selectedOpt = select.options[select.selectedIndex];
  if (selectedOpt) {
    if (nameElem) nameElem.textContent = selectedOpt.dataset.driverName;
    if (rankElem) rankElem.textContent = selectedOpt.dataset.driverRank || 'Pool Driver';
    if (armyElem) armyElem.textContent = selectedOpt.dataset.driverArmy ? `Army No: ${selectedOpt.dataset.driverArmy}` : '';
    if (mobileElem) mobileElem.textContent = selectedOpt.dataset.driverMobile || 'N/A';
  }
}

async function confirmScan(direction) {
  if (!currentPendingScan) return;

  const isInside = currentPendingScan.current_status === 'INSIDE';
  const vehPlate = (currentPendingScan.vehicle && currentPendingScan.vehicle.registration_number) || 'Vehicle';

  if (isInside && direction === 'ENTRY') {
    alert(`Action Not Allowed: ${vehPlate} is already INSIDE the depot.\nCannot record ENTRY (IN). Only EXIT (OUT) is permitted.`);
    return;
  }
  if (!isInside && direction === 'EXIT') {
    alert(`Action Not Allowed: ${vehPlate} is already OUTSIDE on a trip.\nCannot record EXIT (OUT). Only ENTRY (IN) is permitted.`);
    return;
  }

  const btnIn = document.getElementById('btn-confirm-in');
  const btnOut = document.getElementById('btn-confirm-out');
  const targetBtn = direction === 'ENTRY' ? btnIn : btnOut;

  if (btnIn) btnIn.disabled = true;
  if (btnOut) btnOut.disabled = true;

  if (targetBtn) {
    targetBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Confirming...';
  }

  const driverSelect = document.getElementById('modal-confirm-driver-select');
  let selectedDriverId = null;
  let selectedDriverName = null;

  if (driverSelect && driverSelect.value) {
    selectedDriverId = driverSelect.value;
    const selectedOpt = driverSelect.options[driverSelect.selectedIndex];
    selectedDriverName = selectedOpt ? selectedOpt.dataset.driverName : null;
  } else {
    selectedDriverName = currentPendingScan.driver.name;
    selectedDriverId = currentPendingScan.driver.id;
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

    // Success: Hide confirmation modal
    closeScanConfirmationModal();

    const result = data.data;

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
        if (titleElem) titleElem.innerHTML = '<i class="fa-solid fa-circle-check me-2"></i>ENTRY ALLOWED - RETURNED TO DEPOT';
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

    // Play triumph chime
    playChime(true);

    // Reset back to standby after auto close delay + 2.5s
    if (decisionResetTimer) clearTimeout(decisionResetTimer);
    decisionResetTimer = setTimeout(() => {
      resetGateDecisionToStandby();
    }, (autoCloseSec + 2.5) * 1000);

    currentPendingScan = null;
    currentPendingScanId = null;

    // Trigger poll update
    pollGateFeed();

  } catch (err) {
    console.error('Error confirming scan:', err);
    alert('Failed to connect to gate server. Please try again.');
    if (btnIn) btnIn.disabled = false;
    if (btnOut) btnOut.disabled = false;
  }
}

async function cancelPendingScan() {
  try {
    await fetch('/api/rfid/cancel_pending_scan', { method: 'POST' });
  } catch (e) {}
  currentPendingScan = null;
  currentPendingScanId = null;
  closeScanConfirmationModal();
}

function closeScanConfirmationModal() {
  const modalElem = document.getElementById('scanConfirmationModal');
  if (modalElem) {
    const modal = bootstrap.Modal.getInstance(modalElem);
    if (modal) modal.hide();
  }
}
