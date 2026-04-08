// Çalışma/Toplantı mod yönetimi
let currentMode = 'work'; // 'work' veya 'meeting'
let meetingRecords = [];
let workTimerPaused = false;

// Function to update button states based on current activity
function updateButtonStates() {
    const workBtn = document.getElementById('workModeBtn');
    const meetingBtn = document.getElementById('meetingModeBtn');
    const startBtn = document.getElementById('startBtn');
    const resetBtn = document.getElementById('resetBtn');
    const logoutBtn = document.getElementById('logout'); //  Add logout button reference

    // If work timer is running, disable both work and meeting buttons
    if (isTimerRunning && currentMode === 'work') {
        if (workBtn) {
            workBtn.disabled = true;
            workBtn.style.opacity = '0.5';
            workBtn.style.cursor = 'not-allowed';
            workBtn.style.pointerEvents = 'none'; //  Block all click events
        }
        if (meetingBtn) {
            meetingBtn.disabled = true;
            meetingBtn.style.opacity = '0.5';
            meetingBtn.style.cursor = 'not-allowed';
            meetingBtn.style.pointerEvents = 'none'; //  Block all click events
        }
    }
    // If meeting timer is running, disable both work and meeting buttons
    else if (isMeetingTimerRunning && currentMode === 'meeting') {
        if (workBtn) {
            workBtn.disabled = true;
            workBtn.style.opacity = '0.5';
            workBtn.style.cursor = 'not-allowed';
            workBtn.style.pointerEvents = 'none'; //  Block all click events
        }
        if (meetingBtn) {
            meetingBtn.disabled = true;
            meetingBtn.style.opacity = '0.5';
            meetingBtn.style.cursor = 'not-allowed';
            meetingBtn.style.pointerEvents = 'none'; //  Block all click events
        }
    }
    // If nothing is running, enable both mode buttons
    else {
        if (workBtn) {
            workBtn.disabled = false;
            workBtn.style.opacity = '1';
            workBtn.style.cursor = 'pointer';
            workBtn.style.pointerEvents = 'auto'; //  Allow click events
        }
        if (meetingBtn) {
            meetingBtn.disabled = false;
            meetingBtn.style.opacity = '1';
            meetingBtn.style.cursor = 'pointer';
            meetingBtn.style.pointerEvents = 'auto'; //  Allow click events
        }
    }

    //  Disable START button when any timer is running
    if (startBtn) {
        if (isTimerRunning || isMeetingTimerRunning) {
            startBtn.disabled = true;
            startBtn.style.backgroundColor = 'gray';
            startBtn.style.cursor = 'not-allowed';
            startBtn.style.opacity = '0.6';
            startBtn.style.pointerEvents = 'none'; //  Block all click events
        } else {
            startBtn.disabled = false;
            startBtn.style.backgroundColor = '#006039';
            startBtn.style.cursor = 'pointer';
            startBtn.style.opacity = '1';
            startBtn.style.pointerEvents = 'auto'; //  Allow click events
        }
    }

    //  Handle logout button state
    if (logoutBtn) {
        if (isTimerRunning || isMeetingTimerRunning) {
            // Disable logout button when any timer is running
            logoutBtn.disabled = true;
            logoutBtn.style.opacity = '0.5';
            logoutBtn.style.cursor = 'not-allowed';
            logoutBtn.style.pointerEvents = 'none'; //  Block all click events
            const lang = sessionStorage.getItem('selectedLanguage') || 'en';
            logoutBtn.title = lang === 'tr' ? 
                'Zamanlayıcı çalışırken çıkış yapamazsınız' : 
                'Cannot logout while timer is running';
        } else {
            // Enable logout button when no timers are running
            logoutBtn.disabled = false;
            logoutBtn.style.opacity = '1';
            logoutBtn.style.cursor = 'pointer';
            logoutBtn.style.pointerEvents = 'auto'; //  Allow click events
            logoutBtn.title = '';
        }
    }

    //  Handle finish button state
    if (resetBtn) {
        if (isTimerRunning || isMeetingTimerRunning) {
            // Enable finish button when any timer is running
            resetBtn.disabled = false;
            resetBtn.style.opacity = '1';
            resetBtn.style.cursor = 'pointer';
            resetBtn.style.pointerEvents = 'auto';
        } else {
            // Disable finish button when no timers are running
            resetBtn.disabled = true;
            resetBtn.style.opacity = '0.5';
            resetBtn.style.cursor = 'not-allowed';
            resetBtn.style.pointerEvents = 'none';
        }
    }
}

function setMode(mode) {
    // Prevent switching to work mode if meeting timer is running
    if (isMeetingTimerRunning && mode === 'work') {
        const lang = sessionStorage.getItem('selectedLanguage') || 'en';
        showToast(translations[lang].finishMeetingFirst, "error");
        return;
    }
    
    // Prevent switching to meeting mode if work timer is running
    if (isTimerRunning && mode === 'meeting') {
        const lang = sessionStorage.getItem('selectedLanguage') || 'en';
        const message = lang === 'tr' ? 
            'Toplantıya başlamadan önce lütfen mevcut çalışma oturumunuzu bitirin' : 
            'Please finish your current work session before starting a meeting';
        showToast(message, "error");
        return;
    }

    currentMode = mode;
    const workBtn = document.getElementById('workModeBtn');
    const meetingBtn = document.getElementById('meetingModeBtn');
    
    if (mode === 'work') {
        workBtn.classList.add('active');
        meetingBtn.classList.remove('active');
        setState('work');
        
        stopMeetingTimer();
        if (workTimerPaused) {
            resumeTimer();
            workTimerPaused = false;
        }
    } else { // meeting mode
        meetingBtn.classList.add('active');
        workBtn.classList.remove('active');
        setState('meeting');
        
        // Just pause work timer if running, but don't start meeting timer yet
        if (isTimerRunning) {
            pauseTimer();
            workTimerPaused = true;
        }
        
        // Re-enable START button so user can manually start meeting
        document.getElementById('startBtn').disabled = false;
        document.getElementById('startBtn').style.backgroundColor = '#006039';
    }
    
    // Update button states after mode change
    updateButtonStates();
}

// Custom Dropdown Functions
function initCustomDropdowns() {
    const projectSelect = document.getElementById('project');
    const taskSelect = document.getElementById('task');
    
    if (projectSelect) {
        createCustomDropdown(projectSelect);
    }
    
    if (taskSelect) {
        createCustomDropdown(taskSelect);
    }
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.custom-dropdown')) {
            document.querySelectorAll('.custom-dropdown').forEach(dropdown => {
                dropdown.classList.remove('active');
            });
        }
    });
}

function createCustomDropdown(nativeSelect) {
    const wrapper = nativeSelect.closest('.select-wrapper');
    if (!wrapper) return;
    
    // Check if custom dropdown already exists
    if (wrapper.querySelector('.custom-dropdown')) {
        return; // Already initialized
    }
    
    // Create custom dropdown structure
    const customDropdown = document.createElement('div');
    customDropdown.className = 'custom-dropdown';
    
    const trigger = document.createElement('div');
    trigger.className = 'custom-dropdown-trigger';
    
    const value = document.createElement('div');
    value.className = 'custom-dropdown-value placeholder';
    
    const arrow = document.createElement('div');
    arrow.className = 'custom-dropdown-arrow';
    arrow.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#006039" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>`;
    
    const menu = document.createElement('div');
    menu.className = 'custom-dropdown-menu';
    
    const menuInner = document.createElement('div');
    menuInner.className = 'custom-dropdown-menu-inner';
    
    menu.appendChild(menuInner);
    
    trigger.appendChild(value);
    trigger.appendChild(arrow);
    customDropdown.appendChild(trigger);
    customDropdown.appendChild(menu);
    
    // Insert custom dropdown before native select
    wrapper.insertBefore(customDropdown, nativeSelect);
    
    // Update custom dropdown when native select changes
    nativeSelect.addEventListener('change', function() {
        updateCustomDropdownDisplay(nativeSelect, customDropdown);
    });
    
    // Toggle dropdown on trigger click
    trigger.addEventListener('click', function(e) {
        e.stopPropagation();
        const isActive = customDropdown.classList.contains('active');
        
        // Close all dropdowns
        document.querySelectorAll('.custom-dropdown').forEach(d => d.classList.remove('active'));
        
        if (!isActive) {
            customDropdown.classList.add('active');
            updateCustomDropdownOptions(nativeSelect, menu);
        }
    });
    
    // Initialize display
    updateCustomDropdownDisplay(nativeSelect, customDropdown);
}

function updateCustomDropdownDisplay(nativeSelect, customDropdown) {
    const valueElement = customDropdown.querySelector('.custom-dropdown-value');
    const selectedOption = nativeSelect.options[nativeSelect.selectedIndex];
    
    if (selectedOption && selectedOption.value && !selectedOption.disabled) {
        valueElement.textContent = selectedOption.text;
        valueElement.classList.remove('placeholder');
    } else {
        const lang = sessionStorage.getItem('selectedLanguage') || 'en';
        const placeholderText = nativeSelect.id === 'project' 
            ? (lang === 'tr' ? 'Proje Seçin' : 'Select a Project')
            : (lang === 'tr' ? 'İş Emri Seçin' : 'Select a Task');
        valueElement.textContent = placeholderText;
        valueElement.classList.add('placeholder');
    }
}

function updateCustomDropdownOptions(nativeSelect, menu) {
    const menuInner = menu.querySelector('.custom-dropdown-menu-inner');
    if (!menuInner) return;
    
    menuInner.innerHTML = '';
    
    Array.from(nativeSelect.options).forEach((option, index) => {
        const customOption = document.createElement('div');
        customOption.className = 'custom-option';
        
        if (option.disabled) {
            customOption.classList.add('disabled');
        }
        
        if (option.selected && !option.disabled) {
            customOption.classList.add('selected');
        }
        
        customOption.textContent = option.text;
        customOption.dataset.index = index;
        
        if (!option.disabled) {
            customOption.addEventListener('click', function(e) {
                e.stopPropagation();
                
                // Update native select
                nativeSelect.selectedIndex = parseInt(this.dataset.index);
                
                // Trigger change event
                const changeEvent = new Event('change', { bubbles: true });
                nativeSelect.dispatchEvent(changeEvent);
                
                // Update display
                const customDropdown = nativeSelect.closest('.select-wrapper').querySelector('.custom-dropdown');
                updateCustomDropdownDisplay(nativeSelect, customDropdown);
                
                // Close dropdown
                customDropdown.classList.remove('active');
            });
        }
        
        menuInner.appendChild(customOption);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const workBtn = document.getElementById('workModeBtn');
    const meetingBtn = document.getElementById('meetingModeBtn');
    if (workBtn && meetingBtn) {
        workBtn.addEventListener('click', () => setMode('work'));
        meetingBtn.addEventListener('click', () => setMode('meeting'));
    }

    // Initialize button states
    updateButtonStates();

    // Initialize custom dropdowns
    initCustomDropdowns();

    // Screenshot interval fetch
    fetchScreenshotInterval();
});

// Screenshot interval fetch and display
function fetchScreenshotInterval() {
    const intervalDiv = document.getElementById('screenshotInterval');
    if (!user || !intervalDiv) return;
    
        let payload = {};
        if (user.staffid) {
            payload.staff_id = user.staffid;
        } else if (user.email) {
            payload.email = user.email;
        }
        fetch('/get_screenshot_time_interval', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
    .then(res => res.json())
    .then(data => {
        if (data && typeof data.screenshot_interval !== 'undefined') {
            const lang = sessionStorage.getItem('selectedLanguage') || 'en';
            let minuteLabel;
            if (lang === 'en') {
                minuteLabel = data.screenshot_interval === 1 ? translations[lang].minute : translations[lang].minutes;
            } else if (lang === 'tr') {
                minuteLabel = translations[lang].dakika;
            } else {
                // Diğer diller için varsayılan olarak İngilizce kullan
                minuteLabel = data.screenshot_interval === 1 ? translations['en'].minute : translations['en'].minutes;
            }
            intervalDiv.textContent = `${data.screenshot_interval} ${minuteLabel}`;
        } else {
            intervalDiv.textContent = 'N/A';
        }
    })
    .catch(() => {
        intervalDiv.textContent = 'N/A';
    });
}

let isStartInProgress = false;
let isSubmitInProgress = false;
let isResetInProgress = false;
let idleTriggerTime = 0;
let idleTimeout = 5;

//  DDS Styling API Integration for Client Page
const translations = {
    en: {
        welcome: "Welcome...",
        logging: "Logging",
        total: "Total Time Count",
        loadingTasks: "Loading tasks...",
        idleTitle: "You're Idle",
        idleDesc: "You've been inactive. Timer is paused.",
        idle: "IDLE",
        workInfo: "Work Information",
        sessionStats: "Session Stats",
        close: "Close",
        idleDetection: "Idle Detection",
        yes: "YES",
        no: "NO",
        enabled: "Enabled",
        disabled: "Disabled",
        apiDisabled: "API Disabled",
        min: "min", 
        minute: "minute",
        minutes: "minutes",
        today: "Today",
        work: "WORK",
        meeting: "MEETING",
        start: "START",
        finish: "Finish",
        hrs: "HRS",
        min: "MIN",
        sec: "SEC",
        modalTitle: "Task Completion",
        meetingModalTitle: "Meeting Completion",
        modalDesc: "Please describe what you have completed for this task",
        meetingModalDesc: "Please describe what was discussed in this meeting",
        submit: "Submit",
        selectTask: "-- Select a Task --",
        loadingProjects: "Loading projects...",
        user: "User",
        projectLabel: "Project",
        taskLabel: "Task",
        client: "Staff",
        modalPlaceholder: "Type your task details here...",
        meetingModalPlaceholder: "Topics covered during this meeting included:\n\nSearch engine optimization initiatives\n\nBackend architecture and development updates\n\nUI/UX enhancement strategies\n\n…additional items as discussed.",
        selectProject: "Select a Project",
        minWorkWarning: "You must work at least 10 seconds to finish a task.",
        logout: "Logout",
        logoutTitle: "Confirm Logout",
        logoutDesc: "Are you sure you want to log out from DDS-FocusPro?",
        logoutConfirm: "Logout",
        logoutCancel: "Cancel",
        feedbackTitle: "Share Your Feedback",
        feedbackDesc: "We'd love to hear your thoughts about DDSFocusPro:",
        feedbackPlaceholder: "Type your feedback here...",
        feedbackSubmit: "Submit Review",
        navDashboard: "DASHBOARD",
        navHelp: "HELP",
        navSettings: "SETTINGS",
        statusText: {
            work: " ",
            break: "You are on a BREAK – Relax and recharge ",
            idle: " ",
            meeting: "In a MEETING – Stay connected and engaged "
        },
        navFeedback: "FEEDBACK",
        rememberMe: "Remember Me",
        selectMode: "Select Mode",
        workMode: "Work Mode",
        meetingMode: "Meeting Mode",
        totalLogged: "Total Time Logged",
        workTime: "Work Time",
        meetingTime: "Meeting Time",
        screenRecording: "Screen Recording",
        screenshotInterval: "Screenshot Interval",
        finishMeetingFirst: "Please finish the meeting first.",
        selectTaskFirst: "⚠️ Please select a task before starting the timer!",
        enterDetails: "Please enter details!",
        savingMeetingDetails: "Saving meeting details...",
        meetingDetailsSaved: " Meeting details saved!",
        savingDetails: " Saving details...",
        detailsSaved: " Task details saved!",
        failedSaveMeeting: " Failed to save meeting details",
        failedSave: " Failed to save details",
        errorSavingMeeting: " Error saving meeting details",
        errorSaving: " Error saving details",
        timesheetSent: " Timesheet sent!",
        emailSent: " Email sent for timesheet.",
        errorSendingTimesheet: " Error sending timesheet or email:",
        syncingTimesheets: " Syncing timesheets...Please wait",
        failedUpload: " Failed: ",
        unexpectedErrorUpload: " Unexpected error during log upload",
        selectTaskWarning: " Please select a task!",
        cannotLogoutRunning: "⛔ You cannot logout while the timer is running. Please finish your task first.",
        missingReviewInfo: "❗ Missing review or user info.",
        feedbackSent: " Feedback sent successfully!",
        feedbackError: " Feedback error occurred.",
        countdownCanceled: " Countdown canceled. Back to work!",
        loading: "Loading...",
        meetingSession: "Meeting Session",
        currentlyInMeeting: "Currently in a meeting",
        noTaskSelected: "No Task Selected",
        meeting: "Meeting",
        meetingInProgress: "Meeting in progress",
        unnamedProject: "Unnamed Project",
        unnamedTask: "Unnamed Task",
        errorLoadingProjects: " Error loading projects",
        errorLoadingTasks: "Error loading tasks",
        autoSavedAppExit: "Auto-saved due to app exit.",
        workingOn: "Working on:",
        currentTask: "Current task:",
        meetingNotesSavedTemporarily: " Meeting notes saved temporarily!"
    },
    tr: {
        welcome: "Hoş geldin...",
        logging: "Ekran Kaydı",
        total: "Toplam Süre",
        minWorkWarning: " Bir görevi bitirmek için en az 1 dakika çalışmalısınız.",
        idle: "BOŞTA",
        workInfo: "Çalışma Bilgileri",
        sessionStats: "Oturum İstatistikleri",
        close: "Kapat",
        idleDetection: "Boşta Algılama",
        yes: "EVET",
        no: "HAYIR",
        enabled: "Etkin",
        disabled: "Devre Dışı",
        apiDisabled: "API Devre Dışı",
        break: "MOLA",
        min: "dk",
        dakika: "dakika",
        meeting: "TOPLANTI",
        today: "Tarih",
        work: "ÇALIŞMA",
        start: "BAŞLAT",
        finish: "Bitir",
        hrs: "SA",
        min: "DK",
        sec: "SN",
        modalTitle: " İş Tamamlandı",
        meetingModalTitle: " Toplantı Tamamlandı",
        modalDesc: "Bu İş Emri için ne yaptığınızı açıklayın:",
        meetingModalDesc: "Bu toplantıda neler konuşulduğunu açıklayın:",
        submit: "Gönder",
        selectTask: "-- İş Emri Seçin --",
        loadingProjects: "Projeler yükleniyor...",
        user: "Kullanıcı",
        projectLabel: "Proje",
        taskLabel: "İş Emri",
        client: "Personel",
        modalPlaceholder: "İş Emri detaylarını buraya yazın...",
        meetingModalPlaceholder: "Bu toplantıda ele alınan konular:\n\nArama motoru optimizasyonu girişimleri\n\nBackend mimari ve geliştirme güncellemeleri\n\nUI/UX iyileştirme stratejileri\n\n…görüşülen diğer konular.",
        selectProject: "Proje Seçin",
        logout: "Çıkış Yap",
        logoutTitle: " Çıkış Onayı",
        logoutDesc: "DDS-FocusPro'dan çıkmak istediğinize emin misiniz?",
        logoutConfirm: "Çıkış Yap",
        logoutCancel: "İptal",
        feedbackTitle: "Geri Bildirim Gönder",
        feedbackDesc: "DDSFocusPro hakkında görüşlerinizi duymak isteriz:",
        feedbackPlaceholder: "Geri bildiriminizi buraya yazın...",
        feedbackSubmit: "Gönder",
        navDashboard: "PANO",
        navHelp: "YARDIM",
        navSettings: "AYARLAR",
        navFeedback: "GERİ BİLDİRİM",
        statusText: {
            work: " ",
            break: "Şu anda MOLA'dasınız – Rahatlayın ve enerji toplayın ",
            idle: " ",
            meeting: "Şu anda TOPLANTIDASINIZ – İletişimde ve odaklı kalın "
        },
        rememberMe: "Beni Hatırla",
        selectMode: "Mod Seçin",
        workMode: "Çalışma Modu",
        meetingMode: "Toplantı Modu",
        totalLogged: "Toplam Oturum Süresi",
        workTime: "Çalışma Süresi",
        meetingTime: "Toplantı Süresi",
        screenRecording: "Ekran Kaydı",
        screenshotInterval: "Ekran Görüntüsü Aralığı",
        finishMeetingFirst: "⛔ Lütfen önce toplantıyı bitirin.",
        selectTaskFirst: "⚠️ Lütfen zamanlayıcıyı başlatmadan önce bir görev seçin!",
        enterDetails: " Lütfen detayları girin!",
        savingMeetingDetails: " Toplantı detayları kaydediliyor...",
        meetingDetailsSaved: " Toplantı detayları kaydedildi!",
        savingDetails: " Detaylar kaydediliyor...",
        detailsSaved: " Görev detayları kaydedildi!",
        failedSaveMeeting: " Toplantı detayları kaydedilemedi",
        failedSave: " Detaylar kaydedilemedi",
        errorSavingMeeting: " Toplantı detayları kaydedilirken hata",
        errorSaving: " Detaylar kaydedilirken hata",
        timesheetSent: " Zaman çizelgesi gönderildi!",
        emailSent: " Zaman çizelgesi için e-posta gönderildi.",
        errorSendingTimesheet: " Zaman çizelgesi veya e-posta gönderilirken hata:",
        syncingTimesheets: " Zaman çizelgeleri senkronize ediliyor... Lütfen bekleyin",
        failedUpload: " Başarısız: ",
        unexpectedErrorUpload: " Log yükleme sırasında beklenmeyen hata",
        selectTaskWarning: " Lütfen bir görev seçin!",
        cannotLogoutRunning: "⛔ Zamanlayıcı çalışırken çıkış yapamazsınız. Lütfen önce görevi bitirin.",
        missingReviewInfo: "❗ Geri bildirim veya kullanıcı bilgileri eksik.",
        feedbackSent: " Geri bildirim başarıyla gönderildi!",
        feedbackError: " Geri bildirim hatası oluştu.",
        countdownCanceled: " Geri sayım iptal edildi. Çalışmaya geri dön!",
        autoSavedIdle: " Boşta kalma nedeniyle otomatik kaydedildi",
        loading: "Yükleniyor...",
        meetingSession: "Toplantı Oturumu",
        currentlyInMeeting: "Şu anda toplantıda",
        noTaskSelected: "Görev Seçilmedi",
        meeting: "Toplantı",
        meetingInProgress: "Toplantı devam ediyor",
        unnamedProject: "İsimsiz Proje",
        unnamedTask: "İsimsiz Görev",
        errorLoadingProjects: " Projeler yüklenirken hata",
        errorLoadingTasks: "Görevler yüklenirken hata",
        autoSavedAppExit: "Uygulama çıkış nedeniyle otomatik kaydedildi.",
        workingOn: "Çalışılan:",
        currentTask: "Mevcut görev:",
        meetingNotesSavedTemporarily: " Toplantı notları geçici olarak kaydedildi!"
    }
};

function showToast(message, type = 'success') {
    Toastify({
        text: message,
        duration: 3000,
        gravity: "top",
        position: "right",
        backgroundColor: type === 'error' ? "#e74c3c" : "#27ae60",
        close: true
    }).showToast();
}

function logout() {
    sessionStorage.clear();
    window.location.href = '/';
}

function updateDrawerContent(projectName, taskName, isMeeting = false) {
    const drawerProjectName = document.getElementById('drawerProjectName');
    const drawerProjectDesc = document.getElementById('drawerProjectDesc');
    
    if (drawerProjectName) {
        if (isMeeting) {
            drawerProjectName.textContent = translations[sessionStorage.getItem('selectedLanguage') || 'en'].meetingSession;
            if (drawerProjectDesc) {
                drawerProjectDesc.textContent = translations[sessionStorage.getItem('selectedLanguage') || 'en'].currentlyInMeeting;
            }
        } else {
            drawerProjectName.textContent = projectName || translations[sessionStorage.getItem('selectedLanguage') || 'en'].noProjectSelected;
            if (drawerProjectDesc) {
                drawerProjectDesc.textContent = `${translations[sessionStorage.getItem('selectedLanguage') || 'en'].workingOn} ${projectName || translations[sessionStorage.getItem('selectedLanguage') || 'en'].noProjectSelected}`;
            }
        }
    }
    
    const drawerTaskName = document.getElementById('drawerTaskName');
    const drawerTaskDesc = document.getElementById('drawerTaskDesc');
    
    if (drawerTaskName) {
        if (isMeeting) {
            drawerTaskName.textContent = translations[sessionStorage.getItem('selectedLanguage') || 'en'].meeting;
            if (drawerTaskDesc) {
                drawerTaskDesc.textContent = translations[sessionStorage.getItem('selectedLanguage') || 'en'].meetingInProgress;
            }
        } else {
            drawerTaskName.textContent = taskName || translations[sessionStorage.getItem('selectedLanguage') || 'en'].noTaskSelected;
            if (drawerTaskDesc) {
                drawerTaskDesc.textContent = `${translations[sessionStorage.getItem('selectedLanguage') || 'en'].currentTask} ${taskName || translations[sessionStorage.getItem('selectedLanguage') || 'en'].noTaskSelected}`;
            }
        }
    }
    
    const drawerSessionStart = document.getElementById('drawerSessionStart');
    if (drawerSessionStart) {
        drawerSessionStart.textContent = new Date().toLocaleTimeString();
    }
}

let timerInterval, totalSeconds = 0;
let isTimerRunning = false;
let meetingTimerInterval, meetingTotalSeconds = 0, isMeetingTimerRunning = false;
let meetingStartTime = null; // Track actual meeting start time for accurate duration
let meetingDurationLimit = 3600; // 1 hour = 3600 seconds
let meetingWarningShown = false; // ✅ Track if 5-min warning was shown
let currentTaskId = null, sessionStartTime = null;
let selectedProjectName = '', selectedTaskName = '', user = null;

// ============================
// HEARTBEAT - tells backend the client is still alive
// ============================
let heartbeatInterval = null;

function startHeartbeat() {
    if (heartbeatInterval) return; // already running
    console.log("💓 Heartbeat started (every 60s)");
    // Send first heartbeat immediately
    sendHeartbeat();
    heartbeatInterval = setInterval(sendHeartbeat, 60000); // every 60 seconds
}

function stopHeartbeat() {
    if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
        heartbeatInterval = null;
        console.log("💓 Heartbeat stopped");
    }
}

function sendHeartbeat() {
    fetch('/heartbeat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    }).catch(err => {
        console.warn("💓 Heartbeat failed (offline?):", err.message);
    });
}

// When the window regains focus or becomes visible, immediately send a
// heartbeat.  Chromium throttles setInterval in background tabs/windows
// so the regular 60s heartbeat may not fire.  This ensures the server
// knows we're alive whenever the user switches back to DDS Focus Pro.
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && heartbeatInterval) {
        console.log("💓 Window visible again — sending immediate heartbeat");
        sendHeartbeat();
    }
});
window.addEventListener('focus', () => {
    if (heartbeatInterval) {
        console.log("💓 Window focused — sending immediate heartbeat");
        sendHeartbeat();
    }
});

function startMeetingTimer() {
    if (isMeetingTimerRunning) return;
    
    // Prevent starting meeting if work timer is already running
    if (isTimerRunning) {
        console.warn("⚠️ Cannot start meeting timer while work timer is running");
        return;
    }
    
    // Force stop any leftover work timer state to prevent dual timers
    clearInterval(timerInterval);
    isTimerRunning = false;
    totalSeconds = 0;
    
    //  Use existing sessionStartTime if already set, otherwise create one
    if (!sessionStartTime) {
        sessionStartTime = Math.floor(Date.now() / 1000);
    }
    
    //  Store the actual meeting start time for accurate duration calculation
    meetingStartTime = Math.floor(Date.now() / 1000);
    
    // Start screenshot capture when meeting timer starts
    console.log("🔍 Starting screenshot recording for meeting:", {
        email: user.email,
        project: selectedProjectName,
        task: selectedTaskName
    });
    
    fetch('/start_screen_recording', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: user.email,
            project: selectedProjectName,
            task: selectedTaskName
        })
    })
    .then(res => res.json())
    .then(data => {
        console.log("✅ Screenshot recording response:", data);
    })
    .catch(err => {
        console.error("❌ Screenshot recording error:", err);
    });
    
    //  Call start_task_session for meetings as well
    console.log(" Sending meeting start to /start_task_session:");
    console.log({
        email: user.email,
        staff_id: String(user.staffid),
        task_id: currentTaskId,
        start_time: sessionStartTime
    });

    fetch('/start_task_session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: user.email,
            staff_id: String(user.staffid),
                task_id: currentTaskId,
                start_time: sessionStartTime,
                is_meeting: true
        })
    })
    .then(res => res.json())
    .then(data => {
        console.log(" Sent meeting start time:", sessionStartTime);
        console.log(" Sent task ID   :", currentTaskId);
        console.log(" Sent staff ID  :", user.staffid);
        console.log(" Server response:", data);
    })
    .catch(console.error);
    
    isMeetingTimerRunning = true;
    meetingTimerInterval = setInterval(updateMeetingTimerDisplay, 1000);
    
    // Start heartbeat so backend knows we're alive
    startHeartbeat();
    
    // Enable Finish button when meeting timer starts
    const finishBtn = document.getElementById('resetBtn');
    if (finishBtn) {
        finishBtn.disabled = false;
    }
    
    //  Set screen recording status to YES for meetings too
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    document.getElementById('loggingInput').value = lang === 'tr' ? 'EVET' : 'YES';
    
    updateButtonStates(); // Update button states when meeting starts
}

function stopMeetingTimer() {
    clearInterval(meetingTimerInterval);
    isMeetingTimerRunning = false;
    meetingTotalSeconds = 0;
    meetingStartTime = null; // Clear the start time
    meetingWarningShown = false; // ✅ Reset warning flag for next meeting
    
    // Stop heartbeat when meeting timer stops
    stopHeartbeat();
    
    // Stop screenshot capture when meeting timer stops
    fetch('/stop_screen_recording', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    }).catch(console.error);
    
    //  Use the same timer elements (hours, minutes, seconds) for both work and meeting
    document.getElementById('hours').innerText = '00';
    document.getElementById('minutes').innerText = '00';
    document.getElementById('seconds').innerText = '00';
    
    //  Set screen recording status to NO when meeting stops
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    document.getElementById('loggingInput').value = lang === 'tr' ? 'HAYIR' : 'NO';
    
    // Disable Finish button when meeting stops
    const finishBtn = document.getElementById('resetBtn');
    if (finishBtn) {
        finishBtn.disabled = true;
    }
    
    updateButtonStates(); // Update button states when meeting stops
}

function pauseMeetingTimer() {
    clearInterval(meetingTimerInterval);
    isMeetingTimerRunning = false;
    
    // Stop screenshot capture when meeting timer pauses
    fetch('/stop_screen_recording', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    }).catch(console.error);
    
    //  Set screen recording status to NO when meeting pauses
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    document.getElementById('loggingInput').value = lang === 'tr' ? 'HAYIR' : 'NO';
    
    updateButtonStates(); // Update button states when meeting pauses
}

function updateMeetingTimerDisplay() {
    //  Calculate actual elapsed time based on real timestamps
    if (meetingStartTime) {
        const currentTime = Math.floor(Date.now() / 1000);
        meetingTotalSeconds = currentTime - meetingStartTime;
    } else {
        // Fallback to counter-based approach if start time is missing
        meetingTotalSeconds++;
    }
    
    //  Use the same timer elements (hours, minutes, seconds) for both work and meeting
    document.getElementById('hours').innerText = String(Math.floor(meetingTotalSeconds / 3600)).padStart(2, '0');
    document.getElementById('minutes').innerText = String(Math.floor((meetingTotalSeconds % 3600) / 60)).padStart(2, '0');
    document.getElementById('seconds').innerText = String(meetingTotalSeconds % 60).padStart(2, '0');
    
    // ✅ Show 5-minute warning before 1-hour cutoff
    const warningThreshold = meetingDurationLimit - 300; // 5 minutes before limit
    if (meetingTotalSeconds >= warningThreshold && !meetingWarningShown) {
        meetingWarningShown = true;
        const lang = sessionStorage.getItem('selectedLanguage') || 'en';
        const remainingMins = Math.ceil((meetingDurationLimit - meetingTotalSeconds) / 60);
        const warningMsg = lang === 'tr' 
            ? `⚠️ Toplantınız ${remainingMins} dakika içinde otomatik olarak sona erecektir.`
            : `⚠️ Your meeting will automatically end in ${remainingMins} minutes.`;
        showToast(warningMsg, 'warning');
        console.log(`⚠️ Meeting ${remainingMins}-minute warning shown`);
    }

    // Check if meeting has reached 1 hour (3600 seconds)
    if (meetingTotalSeconds >= meetingDurationLimit) {
        console.log("🕐 Meeting has reached 1 hour limit - triggering session expired");
        triggerMeetingSessionExpired();
    }
}

function resumeTimer() {
    if (!isTimerRunning) {
        isTimerRunning = true;
        timerInterval = setInterval(updateTimerDisplay, 1000);
        startHeartbeat(); // Resume heartbeat when work timer resumes
        document.getElementById('startBtn').disabled = true;
        document.getElementById('startBtn').style.backgroundColor = 'gray';
        updateButtonStates(); // Update button states when work timer resumes
    }
}

// Apply translations when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    console.log('🚀 DOM ready, applying language:', lang);
    
    // Apply immediately
    applyClientLanguage(lang);
    
    // Also apply after a short delay to catch any dynamically loaded elements
    setTimeout(() => {
        applyClientLanguage(lang);
    }, 300);
});

window.onload = function () {
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    
    // Initialize default state to 'work'
    const stateCircle = document.getElementById('stateCircle');
    const workBtn = document.getElementById('workModeBtn');
    const meetingBtn = document.getElementById('meetingModeBtn');
    
    // Set default state to work if not already set
    if (stateCircle && !stateCircle.classList.contains('work') && 
        !stateCircle.classList.contains('meeting') && 
        !stateCircle.classList.contains('break')) {
        setState('work');
        if (workBtn) workBtn.classList.add('active');
        if (meetingBtn) meetingBtn.classList.remove('active');
    }
    
    // Apply language again on window load
    applyClientLanguage(lang);
    
    // Dil değiştirme dropdown'unu dinle
    const langDropdown = document.getElementById('languageDropdown');
    if (langDropdown) {
        langDropdown.addEventListener('change', function() {
            const selectedLang = langDropdown.value;
            sessionStorage.setItem('selectedLanguage', selectedLang);
            applyClientLanguage(selectedLang);
            fetchScreenshotInterval();
        });
    }
    const todayDateField = document.getElementById('todayDate');
    const today = new Date();
    todayDateField.value = today.toLocaleDateString('en-CA');    

    user = JSON.parse(sessionStorage.getItem('user'));
    if (user) {
        document.getElementById('displayUserName').innerText = user.firstName;
        document.getElementById('clientNameInput').value = user.firstName;
        const profileImg = document.getElementById('profileImage');
        const imgUrl = `https://crm.deluxebilisim.com/uploads/staff_profile_images/${user.staffid}/small_${user.profileImage}`;
        profileImg.src = imgUrl;
        profileImg.onerror = function () {
            this.onerror = null;
            this.src = "../static/images/user_placeholder.png";
        };

        // Hide skeleton loader and show actual content
        const skeletonLoader = document.getElementById('headerSkeletonLoader');
        const actualContent = document.getElementById('headerActualContent');
        if (skeletonLoader && actualContent) {
            skeletonLoader.style.display = 'none';
            actualContent.style.display = 'flex';
        }

        fetchAIProjects(user);
        saveUserProjectsToCache(user);
        // Kullanıcı objesi dolduktan hemen sonra intervali çek
        fetchScreenshotInterval();
        
        // Load saved meeting records
        const savedMeetings = localStorage.getItem(`meetingRecords_${user.email}`);
        if (savedMeetings) {
            meetingRecords = JSON.parse(savedMeetings);
            console.log('DEBUG: Loaded saved meeting records:', meetingRecords.length);
        } else {
            console.log('DEBUG: No saved meeting records found');
        }
    }

    setTimeout(() => {
        console.log(' Client.js: Re-applying styling after DOM setup...');
    }, 1000);
};

let idleCountdownInterval;
let idleWarningToast = null;
let idleWarningSeconds = 30;
let idleWarningCountdownInterval = null;
let idleWarningTimer1 = null;
let idleWarningTimer2 = null;
let lastActivityTime = Date.now();

// Track user activity
function resetIdleWarning() {
    const previousTime = lastActivityTime;
    lastActivityTime = Date.now();
    
    // Only log if more than 1 second passed (to avoid spam)
    if (Date.now() - previousTime > 1000) {
        console.log("🖱️ User activity detected - idle timer reset");
    }
    
    // If warning toast is active, cancel it
    if (idleWarningToast) {
        closeIdleWarningToast();
    }
    
    if (idleWarningCountdownInterval) {
        clearInterval(idleWarningCountdownInterval);
        idleWarningCountdownInterval = null;
    }
}

// Close idle warning toast
function closeIdleWarningToast() {
    if (!idleWarningToast) return;
    
    idleWarningToast.classList.remove("active");
    
    setTimeout(() => {
        const progress = idleWarningToast.querySelector(".progress");
        if (progress) {
            progress.classList.remove("active");
        }
    }, 300);
    
    clearTimeout(idleWarningTimer1);
    clearTimeout(idleWarningTimer2);
    
    setTimeout(() => {
        if (idleWarningToast && idleWarningToast.parentNode) {
            idleWarningToast.parentNode.removeChild(idleWarningToast);
        }
        idleWarningToast = null;
    }, 500);
}

// ⚠️ DISABLED: Frontend-only idle detection causes false positives when working in other apps
// The system now relies on backend system-wide idle detection (tracks ALL applications, not just browser)
// Listen for user activity
// document.addEventListener('mousemove', resetIdleWarning);
// document.addEventListener('keydown', resetIdleWarning);
// document.addEventListener('click', resetIdleWarning);
// document.addEventListener('scroll', resetIdleWarning);

// Check for inactivity and show warning toast
// setInterval(() => {
//     // Check if either work timer or meeting timer is running
//     if (!isTimerRunning && !isMeetingTimerRunning) return;
//     
//     const inactiveTime = (Date.now() - lastActivityTime) / 1000; // seconds
//     
//     // Debug logging
//     if (inactiveTime > 5) {
//         console.log(`⏱️ Inactive for ${Math.floor(inactiveTime)} seconds (Warning at 150s)`);
//     }
//     
//     // If user has been inactive for 150 seconds (2.5 minutes), start 30 second warning
//     if (inactiveTime >= 150 && !idleWarningToast) {
//         console.log("⚠️ Starting idle warning countdown!");
//         startIdleWarningCountdown();
//     }
// }, 1000);

function startIdleWarningCountdown() {
    idleWarningSeconds = 30;
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    
    const title = lang === 'tr' ? 'Dikkat!' : 'Warning!';
    const message = lang === 'tr' 
        ? 'Fare veya klavye ile hareket yapın'
        : 'Move mouse or press any key to stay active';
    
    // Create custom toast
    idleWarningToast = document.createElement('div');
    idleWarningToast.className = 'custom-toast';
    idleWarningToast.innerHTML = `
        <div class="toast-content">
            <div class="alert-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                </svg>
            </div>
            <div class="message">
                <span class="text text-1">${title}</span>
                <span class="text text-2">${message}</span>
            </div>
            <div class="countdown" id="idleWarningCountdown">${idleWarningSeconds}</div>
        </div>
        <span class="close" onclick="resetIdleWarning()">✕</span>
        <div class="progress warning"></div>
    `;
    
    document.body.appendChild(idleWarningToast);
    
    // Trigger animation
    setTimeout(() => {
        idleWarningToast.classList.add('active');
        const progress = idleWarningToast.querySelector('.progress');
        if (progress) {
            progress.classList.add('active');
        }
    }, 100);
    
    // Countdown
    idleWarningCountdownInterval = setInterval(() => {
        idleWarningSeconds--;
        
        const counterElement = document.getElementById('idleWarningCountdown');
        if (counterElement) {
            counterElement.textContent = idleWarningSeconds;
        }
        
        // When countdown reaches 0, user becomes idle
        if (idleWarningSeconds <= 0) {
            clearInterval(idleWarningCountdownInterval);
            idleWarningCountdownInterval = null;
            
            closeIdleWarningToast();
            
            // Trigger idle state immediately
            triggerIdleState();
        }
    }, 1000);
}

function triggerIdleState() {
    console.log("🔔 User became idle after warning countdown");
    idleTriggerTime = Date.now();
    
    // Pause the appropriate timer based on current mode
    if (currentMode === 'work' && isTimerRunning) {
        pauseTimer();
        resetTimer();
    } else if (currentMode === 'meeting' && isMeetingTimerRunning) {
        pauseMeetingTimer();
        // Note: We don't reset meeting timer, just pause it
    }
    
    setState('idle');

    // Disable all buttons when idle modal appears
    const startBtn = document.getElementById('startBtn');
    const workModeBtn = document.querySelector('.mode-btn[data-mode="work"]');
    const meetingModeBtn = document.querySelector('.mode-btn[data-mode="meeting"]');
    const finishBtn = document.getElementById('finishBtn');
    
    if (startBtn) {
        startBtn.disabled = true;
        startBtn.style.backgroundColor = 'gray';
        startBtn.style.opacity = '0.5';
    }
    if (workModeBtn) {
        workModeBtn.disabled = true;
        workModeBtn.style.opacity = '0.5';
    }
    if (meetingModeBtn) {
        meetingModeBtn.disabled = true;
        meetingModeBtn.style.opacity = '0.5';
    }
    if (finishBtn) {
        finishBtn.disabled = true;
        finishBtn.style.backgroundColor = 'gray';
        finishBtn.style.opacity = '0.5';
    }

    const idleModal = document.getElementById("idleModal");

    if (idleModal) {
        const idleContent = idleModal.querySelector(".modal-content");
        if (idleContent) {
            // Update modal text based on mode
            const lang = sessionStorage.getItem('selectedLanguage') || 'en';
            const idleModalTitle = document.getElementById('idleModalTitle');
            const idleModalDesc = document.getElementById('idleModalDesc');
            
            if (currentMode === 'meeting') {
                // Session expired text for meetings
                if (idleModalTitle) {
                    idleModalTitle.textContent = lang === 'tr' ? 'Oturum Süresi Doldu' : 'Session Expired';
                }
                if (idleModalDesc) {
                    idleModalDesc.textContent = lang === 'tr' 
                        ? 'Toplantı oturumunuz 3 dakika boyunca hareketsiz kaldığı için otomatik olarak durduruldu.'
                        : 'Your meeting session has been stopped automatically due to 3 minutes of inactivity.';
                }
            } else {
                // Idle text for work mode
                if (idleModalTitle) {
                    idleModalTitle.textContent = lang === 'tr' ? 'Boşta Kaldınız' : 'You Have Been Idle';
                }
                if (idleModalDesc) {
                    idleModalDesc.textContent = lang === 'tr' 
                        ? '3 dakika boyunca boşta kaldığınız için süreniz otomatik olarak durduruldu. Çalışmaya devam etmek istiyorsanız lütfen tekrar başlatın.'
                        : 'You have been idle for 3 minutes so your time has been stopped automatically. If you want to work please again start the work and continue the work.';
                }
            }
            
            idleModal.style.display = 'flex';
            
            // Trigger animation after display is set
            setTimeout(() => {
                idleModal.classList.remove('hide');
                idleModal.classList.add('show');
                idleContent.classList.remove('idle-shake');
                void idleContent.offsetWidth;
                idleContent.classList.add('idle-shake');
            }, 10);

            // Auto-submit after 10 seconds if user doesn't take action
            setTimeout(() => {
                handleAutoIdleSubmit();
            }, 10000);
        }
    }
}

function triggerMeetingSessionExpired() {
    console.log("🕐 Meeting session expired after 1 hour");
    
    // Stop the meeting timer
    clearInterval(meetingTimerInterval);
    isMeetingTimerRunning = false;
    
    // Pause meeting timer
    pauseMeetingTimer();
    
    setState('idle');

    // Disable all buttons when session expired modal appears
    const startBtn = document.getElementById('startBtn');
    const workModeBtn = document.querySelector('.mode-btn[data-mode="work"]');
    const meetingModeBtn = document.querySelector('.mode-btn[data-mode="meeting"]');
    const finishBtn = document.getElementById('finishBtn');
    
    if (startBtn) {
        startBtn.disabled = true;
        startBtn.style.backgroundColor = 'gray';
        startBtn.style.opacity = '0.5';
    }
    if (workModeBtn) {
        workModeBtn.disabled = true;
        workModeBtn.style.opacity = '0.5';
    }
    if (meetingModeBtn) {
        meetingModeBtn.disabled = true;
        meetingModeBtn.style.opacity = '0.5';
    }
    if (finishBtn) {
        finishBtn.disabled = true;
        finishBtn.style.backgroundColor = 'gray';
        finishBtn.style.opacity = '0.5';
    }

    const idleModal = document.getElementById("idleModal");

    if (idleModal) {
        const idleContent = idleModal.querySelector(".modal-content");
        if (idleContent) {
            // Update modal text for session expired
            const lang = sessionStorage.getItem('selectedLanguage') || 'en';
            const idleModalTitle = document.getElementById('idleModalTitle');
            const idleModalDesc = document.getElementById('idleModalDesc');
            
            if (idleModalTitle) {
                idleModalTitle.textContent = lang === 'tr' ? 'Oturum Süresi Doldu' : 'Session Expired';
            }
            if (idleModalDesc) {
                idleModalDesc.textContent = lang === 'tr' 
                    ? 'Toplantı oturumunuz 1 saat sonra otomatik olarak sona erdi.'
                    : 'Your meeting session has ended automatically after 1 hour.';
            }
            
            idleModal.style.display = 'flex';
            
            // Trigger animation after display is set
            setTimeout(() => {
                idleModal.classList.remove('hide');
                idleModal.classList.add('show');
                idleContent.classList.remove('idle-shake');
                void idleContent.offsetWidth;
                idleContent.classList.add('idle-shake');
            }, 10);

            // Auto-submit after 10 seconds if user doesn't take action
            setTimeout(() => {
                handleMeetingSessionExpiredSubmit();
            }, 10000);
        }
    }
}

setInterval(() => {
    // Check if either work timer or meeting timer is running
    if (!isTimerRunning && !isMeetingTimerRunning) return;

    fetch('/check_idle_state')
        .then(res => res.json())
        .then(data => {
            if (data.idle) {
                console.log(" Backend says: User is idle");
                
                // Cancel warning toast if active
                if (idleWarningToast) {
                    closeIdleWarningToast();
                }
                if (idleWarningCountdownInterval) {
                    clearInterval(idleWarningCountdownInterval);
                    idleWarningCountdownInterval = null;
                }
                
                idleTriggerTime = Date.now();
                
                // Pause the appropriate timer based on current mode
                if (currentMode === 'work' && isTimerRunning) {
                    pauseTimer();
                    resetTimer();
                } else if (currentMode === 'meeting' && isMeetingTimerRunning) {
                    pauseMeetingTimer();
                    // Note: We don't reset meeting timer, just pause it
                }
                
                setState('idle');

                const idleModal = document.getElementById("idleModal");

                if (idleModal) {
                    const idleContent = idleModal.querySelector(".modal-content");
                    if (idleContent) {
                        // Update modal text based on mode
                        const lang = sessionStorage.getItem('selectedLanguage') || 'en';
                        const idleModalTitle = document.getElementById('idleModalTitle');
                        const idleModalDesc = document.getElementById('idleModalDesc');
                        
                        if (currentMode === 'meeting') {
                            // Session expired text for meetings
                            if (idleModalTitle) {
                                idleModalTitle.textContent = lang === 'tr' ? 'Oturum Süresi Doldu' : 'Session Expired';
                            }
                            if (idleModalDesc) {
                                idleModalDesc.textContent = lang === 'tr' 
                                    ? 'Toplantı oturumunuz 3 dakika boyunca hareketsiz kaldığı için otomatik olarak durduruldu.'
                                    : 'Your meeting session has been stopped automatically due to 3 minutes of inactivity.';
                            }
                        } else {
                            // Idle text for work mode
                            if (idleModalTitle) {
                                idleModalTitle.textContent = lang === 'tr' ? 'Boşta Kaldınız' : 'You Have Been Idle';
                            }
                            if (idleModalDesc) {
                                idleModalDesc.textContent = lang === 'tr' 
                                    ? '3 dakika boyunca boşta kaldığınız için süreniz otomatik olarak durduruldu. Çalışmaya devam etmek istiyorsanız lütfen tekrar başlatın.'
                                    : 'You have been idle for 3 minutes so your time has been stopped automatically. If you want to work please again start the work and continue the work.';
                            }
                        }
                        
                        idleModal.style.display = 'flex';
                        
                        // Trigger animation after display is set
                        setTimeout(() => {
                            idleModal.classList.remove('hide');
                            idleModal.classList.add('show');
                            idleContent.classList.remove('idle-shake');
                            void idleContent.offsetWidth;
                            idleContent.classList.add('idle-shake');
                        }, 10);

                        // Auto-submit after 10 seconds if user doesn't take action
                        setTimeout(() => {
                            handleAutoIdleSubmit();
                        }, 10000);
                    }
                }
            }
        })
        .catch(console.error);
}, 10000);

async function handleMeetingSessionExpiredSubmit() {
    stopScreenRecording();
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';

    const actualEndTime = Math.floor(Date.now() / 1000);
    
    // Meeting expired message
    const meetingExpiredNote = lang === 'tr' ? 'Oturum 1 saat sonra sona erdi' : 'Session expired after 1 hour';

    console.log("🕐 Auto-submitting meeting after 1 hour...");
    console.log({
        email: user.email,
        task: currentTaskId,
        start: sessionStartTime,
        end: actualEndTime,
        duration: meetingTotalSeconds
    });

    try {
        await fetch('/end_task_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: user.email,
                staff_id: String(user.staffid),
                task_id: currentTaskId,
                end_time: actualEndTime,
                note: '',
                is_meeting: true,
                meetings: [{ duration_seconds: meetingTotalSeconds, notes: meetingExpiredNote }]
            })
        });

        stopMeetingTimer();
        stopScreenRecording();
        stopDailyLogsCapture();
        
        const successMsg = lang === 'tr' ? 'Toplantı 1 saat sonra otomatik olarak kaydedildi' : 'Meeting automatically saved after 1 hour';
        showToast(successMsg, 'success');
        
        closeIdleModal();
    } catch (error) {
        console.error("🕐 Failed to auto-save meeting:", error);
    }
}

async function handleAutoIdleSubmit() {
    stopScreenRecording();
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';

    const totalIdleSeconds = 180;
    const actualEndTime = Math.floor(idleTriggerTime / 1000);
    const adjustedEndTime = actualEndTime - totalIdleSeconds;
    const durationWorked = adjustedEndTime - sessionStartTime;

    const minsWorked = durationWorked >= 60 ? Math.floor(durationWorked / 60) : 0;
    const secsWorked = durationWorked % 60;
    // Check if it's a meeting mode
    const isMeeting = currentMode === 'meeting';
    
    const idleMsg = lang === 'tr'
    ? (minsWorked === 0
        ? `Kullanıcı 1 dakikadan az çalıştı ve ${totalIdleSeconds} saniye boşta kaldı.`
        : `Kullanıcı ${minsWorked} dakika çalıştı ve ${totalIdleSeconds} saniye boşta kaldı.`)
    : (minsWorked === 0
        ? `User worked for less than 1 minute and stayed idle for ${totalIdleSeconds} seconds.`
        : `User worked for ${minsWorked} minutes and stayed idle for ${totalIdleSeconds} seconds.`);

    // For meetings, don't send the main note - only send in meetings array
    // For work mode, send the note normally
    const finalNote = isMeeting ? '' : idleMsg;
    
    // For meeting idle, use "Session expired due to inactivity" message
    const meetingIdleNote = lang === 'tr' ? 'Oturum hareketsizlik nedeniyle sona erdi' : 'Session expired due to inactivity';

    console.log(" Auto-submitting due to idle...");
    console.log({
        email: user.email,
        task: currentTaskId,
        start: sessionStartTime,
        adjustedEndTime,
        idleMsg: finalNote
    });

    try {
        await fetch('/end_task_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: user.email,
                staff_id: String(user.staffid),
                task_id: currentTaskId,
                end_time: adjustedEndTime,
                note: finalNote,
                is_meeting: isMeeting,
                meetings: isMeeting 
                    ? [{ duration_seconds: meetingTotalSeconds, notes: meetingIdleNote }] 
                    : undefined
            })
        });

        resetTimer();
        stopScreenRecording();
        stopDailyLogsCapture();
        showToast(translations[lang].autoSavedIdle, 'success');
    } catch (error) {
        console.error(" Failed to auto-save:", error);
    }
}

document.getElementById('startBtn').addEventListener('click', function () {
    // Check task selection for both work and meeting modes
    const taskSelect = document.getElementById('task');
    const selectedTaskOption = taskSelect.options[taskSelect.selectedIndex];
    const taskId = taskSelect.value;

    if (!taskId || taskId === "" || selectedTaskOption.disabled) {
        const lang = sessionStorage.getItem('selectedLanguage') || 'en';
        showToast(translations[lang].selectTaskFirst, 'error');
        return;
    }

    if (currentMode === 'work') {
        currentTaskId = taskId;
        selectedProjectName = document.getElementById('project').selectedOptions[0]?.textContent || '';
        selectedTaskName = selectedTaskOption.textContent;
    } else {
        // Meeting mode - also requires task selection
        currentTaskId = taskId;
        selectedProjectName = document.getElementById('project').selectedOptions[0]?.textContent || '';
        selectedTaskName = selectedTaskOption.textContent + ' (Meeting)';
    }

    if (!isTimerRunning && !isMeetingTimerRunning) {
        sessionStartTime = Math.floor(Date.now() / 1000);

        updateDrawerContent(selectedProjectName, selectedTaskName, currentMode === 'meeting');

        startDailyLogsCapture();
        
        // Start appropriate timer based on mode
        if (currentMode === 'meeting') {
            startMeetingTimer();
        } else {
            startTimer();
        }
        
        setState(currentMode === 'meeting' ? 'meeting' : 'work');

        // Başlat tuşunu disabled yap
        const startBtn = document.getElementById('startBtn');
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.style.backgroundColor = 'gray';
        }

        setTimeout(() => {
        }, 500);
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const resetBtn = document.getElementById('resetBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (currentMode === 'meeting') {
                // Don't pause timer, just open modal - timer keeps running
                openModal();
            } else {
                if (totalSeconds < 10) {
                    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
                    const message = translations[lang].minWorkWarning;
                    showToast(message, 'error');
                    return;
                }
                openModal();
            }
        });
    } else {
        console.error(' resetBtn element not found!');
    }
});

function startTimer() {
    // Prevent starting work timer if meeting timer is already running
    if (isMeetingTimerRunning) {
        console.warn("⚠️ Cannot start work timer while meeting timer is running");
        return;
    }
    
    // Force stop any leftover meeting timer state to prevent dual timers
    clearInterval(meetingTimerInterval);
    isMeetingTimerRunning = false;
    meetingTotalSeconds = 0;
    meetingStartTime = null;
    
    sessionStartTime = Math.floor(Date.now() / 1000);
    
    // Reset activity time to prevent immediate idle detection
    lastActivityTime = Date.now();
    console.log("✅ Timer started - lastActivityTime reset to:", new Date(lastActivityTime).toLocaleTimeString());
    
    // Clear any existing idle warning toast and timers
    if (idleWarningToast) {
        closeIdleWarningToast();
    }
    if (idleWarningCountdownInterval) {
        clearInterval(idleWarningCountdownInterval);
        idleWarningCountdownInterval = null;
    }
    
    // Start screenshot capture ONLY when timer actually starts
    fetch('/start_screen_recording', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: user.email,
            project: selectedProjectName,
            task: selectedTaskName
        })
    }).catch(console.error);
    
    if (currentMode === 'work') {
        console.log(" Sending to /start_task_session:");
        console.log({
            email: user.email,
            staff_id: String(user.staffid),
            task_id: currentTaskId,
            start_time: sessionStartTime
        });

        fetch('/start_task_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: user.email,
                staff_id: String(user.staffid),
                task_id: currentTaskId,
                start_time: sessionStartTime,
                is_meeting: false
            })
        })
        .then(res => res.json())
        .then(data => {
            console.log(" Sent start time:", sessionStartTime);
            console.log(" Sent task ID   :", currentTaskId);
            console.log(" Sent staff ID  :", user.staffid);
            console.log(" Server response:", data);
        })
        .catch(console.error);
    }

    isTimerRunning = true;
    document.getElementById('startBtn').disabled = true;
    document.getElementById('startBtn').style.backgroundColor = 'gray';
    
    // Start heartbeat so backend knows we're alive
    startHeartbeat();
    
    // Enable Finish button when timer starts
    const finishBtn = document.getElementById('resetBtn');
    if (finishBtn) {
        finishBtn.disabled = false;
    }
    
    // Sadece çalışma modunda dropdown'ları disable et
    if (currentMode === 'work') {
        document.getElementById('project').disabled = true;
        document.getElementById('task').disabled = true;
    }
    
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    document.getElementById('loggingInput').value = lang === 'tr' ? 'EVET' : 'YES';

    timerInterval = setInterval(updateTimerDisplay, 1000);
    updateButtonStates(); // Update button states when work timer starts
}

function pauseTimer() {
    console.log("Timer paused, seconds was:", totalSeconds);
    clearInterval(timerInterval);
    isTimerRunning = false;
    
    // Stop screenshot capture when work timer pauses
    fetch('/stop_screen_recording', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    }).catch(console.error);
    
    document.getElementById('startBtn').disabled = false;
    document.getElementById('startBtn').style.backgroundColor = '#006039';
    updateButtonStates(); // Update button states when work timer pauses
}

function resetTimer() {
    clearInterval(timerInterval);
    totalSeconds = 0;
    isTimerRunning = false;
    sessionStartTime = null; // Reset session start time
    
    // Stop heartbeat when timer resets
    stopHeartbeat();

    // Stop screenshot capture when timer resets
    fetch('/stop_screen_recording', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    }).catch(console.error);

    document.getElementById('hours').innerText = '00';
    document.getElementById('minutes').innerText = '00';
    document.getElementById('seconds').innerText = '00';

    document.getElementById('startBtn').disabled = false;
    document.getElementById('startBtn').style.backgroundColor = '#006039';
    
    // Disable Finish button when timer resets
    const finishBtn = document.getElementById('resetBtn');
    if (finishBtn) {
        finishBtn.disabled = true;
    }
    
    updateButtonStates(); // Update button states when timer resets

    // Sadece çalışma modunda dropdown'ları enable et
    if (currentMode === 'work') {
        const projectSelect = document.getElementById('project');
        const taskSelect = document.getElementById('task');
        projectSelect.disabled = false;
        taskSelect.disabled = false;
    }

    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    document.getElementById('loggingInput').value = lang === 'tr' ? 'HAYIR' : 'NO';
}

function updateTimerDisplay() {
    // ✅ Calculate actual elapsed time based on real timestamps (fixes background timer issue)
    if (sessionStartTime) {
        const currentTime = Math.floor(Date.now() / 1000);
        totalSeconds = currentTime - sessionStartTime;
    } else {
        // Fallback to counter-based approach if start time is missing
        totalSeconds++;
    }

    document.getElementById('hours').innerText = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
    document.getElementById('minutes').innerText = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0');
    document.getElementById('seconds').innerText = String(totalSeconds % 60).padStart(2, '0');
}

function stopScreenRecording() {
    fetch('/stop_screen_recording', { method: 'POST' })
        .then(res => res.json())
        .catch(console.error);
}

let dailyLogsInterval;

function startDailyLogsCapture() {
    console.log(" Starting automatic daily logs capture...");
    
    captureCurrentActivityLog();
    
    dailyLogsInterval = setInterval(() => {
        captureCurrentActivityLog();
    }, 60000);
}

function stopDailyLogsCapture() {
    if (dailyLogsInterval) {
        console.log(" Stopping daily logs capture...");
        clearInterval(dailyLogsInterval);
        dailyLogsInterval = null;
    }
}

function captureCurrentActivityLog() {
    if (!user || !currentTaskId) return;
    
    const currentTime = new Date().toISOString();
    const logData = {
        email: user.email,
        staff_id: user.staffid,
        task_id: currentTaskId,
        project_name: selectedProjectName,
        task_name: selectedTaskName,
        timestamp: currentTime,
        activity_type: isTimerRunning ? (currentMode === 'meeting' ? 'meeting' : 'working') : 'idle',
        timer_seconds: totalSeconds
    };
    
    fetch('/capture_activity_log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(logData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            console.log(" Activity log captured successfully");
        }
    })
    .catch(err => console.error(" Failed to capture activity log:", err));
}

function fetchAIProjects(user) {
    const projectSelect = document.getElementById('project');
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    const t = {
        en: { loadingProjects: "Loading projects..." },
        tr: { loadingProjects: "Projeler yükleniyor..." }
    };
    projectSelect.innerHTML = `<option class="select-option-default" disabled selected>${t[lang].loadingProjects}</option>`;

    fetch('/get_ai_filtered_projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: user.email, username: `${user.firstName} ${user.lastName || ''}` })
    })
        .then(response => response.json())
        .then(data => {
            const projects = data.projects || [];
            projectSelect.innerHTML = '';
            const lang = sessionStorage.getItem('selectedLanguage') || 'en';
            const t = {
                en: { selectProject: "Select a Project" },
                tr: { selectProject: "Proje Seçin" }
            };
            const defaultOption = new Option(t[lang].selectProject, '');
            defaultOption.className = 'select-option-default';
            defaultOption.disabled = true;
            defaultOption.selected = true;
            // Apply inline styles for disabled/placeholder options
            defaultOption.style.color = '#94a3b8';
            defaultOption.style.backgroundColor = '#f8fafc';
            defaultOption.style.fontStyle = 'italic';
            defaultOption.style.fontWeight = '400';
            projectSelect.appendChild(defaultOption);
            
            const uniqueProjects = [];
            const seenKeys = new Set();

            projects.forEach(project => {
                if (!seenKeys.has(project.id)) {
                    seenKeys.add(project.id);
                    uniqueProjects.push(project);
                }
            });

            uniqueProjects.forEach(project => {
                const option = new Option(project.name || project.projectname || translations[lang].unnamedProject, project.id);
                option.className = 'select-option-item';
                // Apply inline styles as fallback for better browser support
                option.style.fontSize = '14px';
                option.style.fontWeight = '500';
                option.style.color = '#1e293b';
                option.style.backgroundColor = '#ffffff';
                option.style.padding = '8px 12px';
                projectSelect.appendChild(option);
            });
            
            // Update custom dropdown display
            const customDropdown = projectSelect.closest('.select-wrapper')?.querySelector('.custom-dropdown');
            if (customDropdown) {
                updateCustomDropdownDisplay(projectSelect, customDropdown);
            }
        })
        .catch(error => {
            console.error(error);
            showToast(translations[lang].errorLoadingProjects, 'error');
        });
}

function loadTasksForProject() {
    const projectId = document.getElementById('project').value;
    const taskSelect = document.getElementById('task');
    const lang = sessionStorage.getItem('selectedLanguage') || 'tr';
    const selectTaskText = lang === 'tr' ? '-- İş Emri Seçin --' : '-- Select a Task --';
    const loadingTasksText = lang === 'tr' ? 'Görevler yükleniyor...' : 'Loading tasks...';
    
    if (!projectId) {
        taskSelect.innerHTML = `<option class="select-option-default" disabled selected>${selectTaskText}</option>`;
        return;
    }

    taskSelect.innerHTML = `<option class="select-option-default" disabled selected>${loadingTasksText}</option>`;

    fetch(`/get_tasks/${projectId}`)
        .then(response => response.json())
        .then(data => {
            taskSelect.innerHTML = '';
            const placeholder = new Option(selectTaskText, '');
            placeholder.className = 'select-option-default';
            placeholder.disabled = true;
            placeholder.selected = true;
            // Apply inline styles for disabled/placeholder options
            placeholder.style.color = '#94a3b8';
            placeholder.style.backgroundColor = '#f8fafc';
            placeholder.style.fontStyle = 'italic';
            placeholder.style.fontWeight = '400';
            taskSelect.appendChild(placeholder);

            const tasks = data.tasks || [];
            tasks.forEach(task => {
                const option = new Option(task.name || task.subject || translations[lang].unnamedTask, task.id);
                option.className = 'select-option-item';
                // Apply inline styles as fallback for better browser support
                option.style.fontSize = '14px';
                option.style.fontWeight = '500';
                option.style.color = '#1e293b';
                option.style.backgroundColor = '#ffffff';
                option.style.padding = '8px 12px';
                taskSelect.appendChild(option);
            });
            
            // Update custom dropdown display
            const customDropdown = taskSelect.closest('.select-wrapper')?.querySelector('.custom-dropdown');
            if (customDropdown) {
                updateCustomDropdownDisplay(taskSelect, customDropdown);
            }

            console.log(` Loaded ${tasks.length} tasks for project ${projectId}:`);
            tasks.forEach(task => {
                console.log(`🧾 [Task] ID: ${task.id} | Name: ${task.name} | Status: ${task.status}`);
            });
        })
        .catch(error => {
            console.error(" Error loading tasks:", error);
            taskSelect.innerHTML = `<option disabled>${translations[lang].errorLoadingTasks}</option>`;
        });
}

function saveUserProjectsToCache(user) {
    fetch('/cache_user_projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: user.email, username: user.firstName, projects: user.projects })
    }).then(response => response.json()).catch(console.error);
}

function fetchLoggedTaskTimes() {
    fetch(`/get_task_time_summary/${user.email}`)
        .then(res => res.json())
        .then(data => {
        })
        .catch(err => console.error(" Error loading task times:", err));
}

function openModal() {
    console.log(' openModal() called');
    const modal = document.getElementById('finishModal');
    console.log(' Modal element:', modal);
    
    if (!modal) {
        console.error(' finishModal not found!');
        return;
    }
    
    // Modal içeriğini moda göre güncelle
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    if (currentMode === 'meeting') {
        document.getElementById('modalTitle').textContent = translations[lang].meetingModalTitle;
        document.getElementById('modalDesc').textContent = translations[lang].meetingModalDesc;
        document.getElementById('taskDetailInput').placeholder = translations[lang].meetingModalPlaceholder;
    } else {
        document.getElementById('modalTitle').textContent = translations[lang].modalTitle;
        document.getElementById('modalDesc').textContent = translations[lang].modalDesc;
        document.getElementById('taskDetailInput').placeholder = translations[lang].modalPlaceholder;
    }
    
    modal.style.display = 'flex';
    console.log(' Modal display set to flex');
    
    setTimeout(() => {
        modal.classList.remove('hide');
        modal.classList.add('show');
        console.log(' Modal animation classes applied');
    }, 10);
    
    const loggingInput = document.getElementById('loggingInput');
    if (loggingInput) {
        loggingInput.value = lang === 'tr' ? 'EVET' : 'YES';
        console.log(' Logging input set to:', loggingInput.value);
    } else {
        console.warn(' loggingInput not found');
    }
}

function closeModal() {
    const modal = document.getElementById('finishModal');
    modal.classList.remove('show');
    modal.classList.add('hide');
    setTimeout(() => {
        modal.style.display = 'none';
        modal.classList.remove('hide');
    }, 300);
}

async function submitTaskDetails() {
    const detailText = document.getElementById('taskDetailInput').value.trim();
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    
    if (!detailText) {
        showToast(translations[lang].enterDetails, 'error');
        return;
    }

    // Check if it's a meeting and validate minimum 50 characters
    if (currentMode === 'meeting' && detailText.length < 50) {
        const errorMsg = lang === 'tr' 
            ? `Toplantı notları en az 50 karakter olmalıdır. Şu anda: ${detailText.length} karakter`
            : `Meeting notes must be at least 50 characters. Current: ${detailText.length} characters`;
        showToast(errorMsg, 'error');
        return;
    }

    console.log('DEBUG: sessionStartTime:', sessionStartTime, 'currentMode:', currentMode, 'totalSeconds:', totalSeconds);

    if (currentMode === 'meeting') {
        if (totalSeconds === 0) {
            // Sadece toplantı: note boş, meetings tek obje
            const end_time_unix = Math.floor(Date.now() / 1000);
            
            //  Debug: Show actual vs counter time
            const actualDurationSeconds = meetingStartTime ? (end_time_unix - meetingStartTime) : meetingTotalSeconds;
            console.log(' Meeting Duration Debug:');
            console.log('   Counter time:', meetingTotalSeconds, 'seconds');
            console.log('   Actual time: ', actualDurationSeconds, 'seconds');
            console.log('   Start time:  ', meetingStartTime);
            console.log('   End time:    ', end_time_unix);
            
            try {
                // Stop meeting timer before closing modal
                stopMeetingTimer();
                
                closeModal();
                resetTimer();
                stopDailyLogsCapture();  // Stop daily logs to prevent duplicate intervals
                
                // Reset to work mode after meeting finishes
                currentMode = 'work';
                const workBtn = document.getElementById('workModeBtn');
                const meetingBtn = document.getElementById('meetingModeBtn');
                if (workBtn) workBtn.classList.add('active');
                if (meetingBtn) meetingBtn.classList.remove('active');
                setState('work');
                
                // Re-enable project/task dropdowns
                const projectSelect = document.getElementById('project');
                const taskSelect = document.getElementById('task');
                if (projectSelect) projectSelect.disabled = false;
                if (taskSelect) taskSelect.disabled = false;
                
                showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].savingMeetingDetails, 'info');
                
                const payload = {
                    email: user.email,
                    staff_id: String(user.staffid),
                    task_id: currentTaskId,
                    end_time: end_time_unix,
                    note: '',
                    meetings: [{ notes: detailText, duration: `${Math.round(meetingTotalSeconds/60)} minutes`, duration_seconds: meetingTotalSeconds }]
                };
                const saveRes = await fetch('/end_task_session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (saveRes.ok) {
                    await new Promise(resolve => setTimeout(resolve, 2500));
                    showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].meetingDetailsSaved);
                } else {
                    const saveJson = await saveRes.json();
                    showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].failedSaveMeeting, 'error');
                    console.error(' Save response:', saveJson);
                }
                // Re-enable start button
                const startBtn = document.getElementById('startBtn');
                if (startBtn) {
                    startBtn.disabled = false;
                    startBtn.style.backgroundColor = '#006039';
                }
            } catch (error) {
                console.error(' Error saving meeting details:', error);
                showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].errorSavingMeeting, 'error');
            }
            return;
        } else {
            // Work devam ederken toplantı: geçici kaydet
            meetingRecords.push({
                notes: detailText,
                duration: `${Math.round(meetingTotalSeconds/60)} minutes`,
                duration_seconds: meetingTotalSeconds,
                timestamp: Date.now()
            });
            if (user) {
                localStorage.setItem(`meetingRecords_${user.email}`, JSON.stringify(meetingRecords));
            }
            stopMeetingTimer();
            closeModal();
            document.getElementById('taskDetailInput').value = '';
            stopDailyLogsCapture();  // Stop daily logs to prevent duplicate intervals
            setMode('work');
            showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].meetingNotesSavedTemporarily);
            return;
        }
    }

    const end_time_unix = Math.floor(Date.now() / 1000);

    // Work modunda: hem iş hem toplantı notlarını gönder
    let meetings = meetingRecords.slice();
    meetingRecords = [];
    if (user) {
        localStorage.removeItem(`meetingRecords_${user.email}`);
    }
    try {
        closeModal();
        resetTimer();
        showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].savingDetails, 'info');
        
        const payload = {
            email: user.email,
            staff_id: String(user.staffid),
            task_id: currentTaskId,
            end_time: end_time_unix,
            note: detailText,
            meetings: meetings
        };
        const saveRes = await fetch('/end_task_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (saveRes.ok) {
            showLoader();
            await Promise.all([
                fetch('/submit_all_data_files', { method: 'POST' }).catch(err => console.warn('Data files error:', err)),
                fetch('/upload_screenshots', { method: 'POST' }).catch(err => console.warn('Screenshots error:', err)),
                uploadUsageLogToS3().catch(err => console.warn('S3 upload error:', err))
            ]);
            hideLoader();
            await new Promise(resolve => setTimeout(resolve, 2500));
            showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].detailsSaved);
        } else {
            const saveJson = await saveRes.json();
            showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].failedSave, 'error');
            console.error(' Save response:', saveJson);
        }
        const startBtn = document.getElementById('startBtn');
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.style.backgroundColor = '#006039';
        }
        totalSeconds = 0;
    } catch (error) {
        console.error(' Error in submitTaskDetails:', error);
        showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].errorSaving, 'error');
        hideLoader();
    }
}

async function sendTimesheetToBackend(meetings = []) {
    const payload =[
        {
            task_id: currentMode === 'meeting' ? 'meeting' : document.getElementById('task').value,
            start_time: "10:00:00",
            end_time: "12:00:00",
            staff_id: String(user.staffid),
            hourly_rate: "5.00",
            note: document.getElementById('taskDetailInput').value.trim(),
            meetings: meetings.length > 0 ? meetings : undefined,
            email: user.email // Add email to payload
        }
    ];
    try {
        console.log("Final payload before sending:", payload, JSON.stringify(payload));
        const res = await fetch('/submit_all_data_files', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        console.log(" Timesheet sent:", result);
        showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].timesheetSent);

        // Send email after timesheet submission
        // await fetch('/send_timesheet_email', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify({ email: user.email, timesheet: payload })
        // });
        console.log(" Email sent for timesheet.");
    } catch (error) {
        console.error(" Error sending timesheet or email:", error);
    }
}

async function sendMeetingToLogoutTime(meetings = []) {
    try {
        const payload = {
            email: user.email,
            staff_id: String(user.staffid),
            total_duration: formatTime(meetingTotalSeconds),
            total_seconds: meetingTotalSeconds,
            meetings: meetings
        };

        const res = await fetch('/api/store_logout_time', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await res.json();
        console.log(" Meeting sent to logout time:", result);
    } catch (error) {
        console.error(" Error sending meeting to logout time:", error);
    }
}

function formatTime(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs}h ${mins}m ${secs}s`;
}

function syncAllUsers() {
    fetch('/submit_all_data_files', {
        method: 'POST'
    })
        .then(res => res.json())
        .then(data => {
            console.log(data);
            showToast(data.message || 'Synced successfully');
        })
        .catch(err => {
            console.error(err);
        });
}

function showLoader() {
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    const messages = {
        en: translations.en.syncingTimesheets,
        tr: translations.tr.syncingTimesheets
    };
    document.getElementById('syncLoader').innerHTML = `
<div style="padding: 20px; background: white; border-radius: 8px; font-weight: bold;">
${messages[lang]}
</div>
`;
    document.getElementById('syncLoader').style.display = 'flex';
}

function hideLoader() {
    document.getElementById('syncLoader').style.display = 'none';
}

window.addEventListener('DOMContentLoaded', () => {
    const animationBox = document.getElementById('work-animation');
    if (animationBox) {
        const gifImg = animationBox.querySelector('img');
        const gifs = [
            "https://media.tenor.com/bnYAs3wmjdYAAAAM/keyboard-type.gif",
            "https://i.gifer.com/embedded/download/11gv.gif",
            "https://www.icegif.com/wp-content/uploads/icegif-1850.gif",
            "https://www.icegif.com/wp-content/uploads/icegif-1852.gif",
            "https://gifdb.com/images/high/jabril-typing-with-toes-y859gmgutpzs3aqj.webp",
            "https://i.gifer.com/embedded/download/Cdm.gif",
            "https://i.gifer.com/embedded/download/So5.gif",
            "https://i.gifer.com/embedded/download/3XJG.gif",
            "https://i.gifer.com/embedded/download/3ev.gif",
            "https://i.gifer.com/embedded/download/Dx.gif",
            "https://i.gifer.com/embedded/download/2IN3.gif"
        ];

        const randomGif = gifs[Math.floor(Math.random() * gifs.length)];
        gifImg.src = randomGif;

        animationBox.classList.add('show');
        animationBox.style.display = 'block';

        setTimeout(() => {
            animationBox.classList.remove('show');
            setTimeout(() => {
                animationBox.style.display = 'none';
            }, 1000);
        }, 20000);
    }
});

function applyClientLanguage(lang) {
    if (!lang || !translations[lang]) {
        lang = 'en';
    }
    const t = translations[lang] || translations['en'];
    
    console.log('🌐 Applying language:', lang);
    
    // Update all elements with data-translatable attribute FIRST
    document.querySelectorAll('[data-translatable]').forEach(element => {
        const key = element.getAttribute('data-translatable');
        if (t[key]) {
            // For labels, preserve child elements (SVG icons) and update text
            if (element.tagName === 'LABEL') {
                // Clone child elements to preserve them
                const children = Array.from(element.children);
                // Clear element
                element.innerHTML = '';
                // Re-add children
                children.forEach(child => element.appendChild(child));
                // Add translation text
                element.appendChild(document.createTextNode(t[key]));
            } else {
                // For other elements (span, div, etc.), replace all content
                element.textContent = t[key];
            }
            console.log(`✅ Translated ${key}: ${t[key]}`);
        } else {
            console.warn(`⚠️ Translation missing for key: ${key}`);
        }
    });
    
    // State circle ve label
    const stateCircle = document.getElementById("stateCircle");
    if (stateCircle) {
        let currentState = "work";
        if (stateCircle.classList.contains("idle")) currentState = "idle";
        else if (stateCircle.classList.contains("break")) currentState = "break";
        else if (stateCircle.classList.contains("meeting")) currentState = "meeting";

        const stateLabel = document.getElementById("stateLabel");
        if (stateLabel) {
            stateLabel.textContent = translations[lang][currentState] || currentState.toUpperCase();
        }
    }

    // Timer labels
    const timerLabels = document.querySelectorAll(".timer-label");
    if (timerLabels.length >= 3) {
        timerLabels[0].textContent = t.hrs;
        timerLabels[1].textContent = t.min;
        timerLabels[2].textContent = t.sec;
    }

    // Buttons
    const startBtn = document.getElementById("startBtn");
    if (startBtn) startBtn.querySelector('span[data-translatable="start"]')?.textContent || (startBtn.textContent = t.start);
    const resetBtn = document.getElementById("resetBtn");
    if (resetBtn) resetBtn.querySelector('span[data-translatable="finish"]')?.textContent || (resetBtn.textContent = t.finish);

    // Mode selection buttons
    const workModeBtn = document.getElementById("workModeBtn");
    if (workModeBtn) workModeBtn.textContent = t.workMode;
    const meetingModeBtn = document.getElementById("meetingModeBtn");
    if (meetingModeBtn) meetingModeBtn.textContent = t.meetingMode;

    // Modal texts
    const idleModalTitle = document.getElementById("idleModalTitle");
    if (idleModalTitle) idleModalTitle.textContent = t.idleTitle;

    const idleModalDesc = document.getElementById("idleModalDesc");
    if (idleModalDesc) idleModalDesc.textContent = t.idleDesc;
    
    // Labels (keep for backward compatibility)
    const labelMap = {
        client: t.client,
        projectLabel: t.projectLabel,
        taskLabel: t.taskLabel,
        today: t.today,
        totalLogged: t.totalLogged,
        workTime: t.workTime,
        meetingTime: t.meetingTime,
        screenRecording: t.screenRecording,
        screenshotInterval: t.screenshotInterval
    };
    
    document.querySelectorAll('label[data-translatable]').forEach(label => {
        const key = label.getAttribute('data-translatable');
        if (labelMap[key]) label.textContent = labelMap[key];
    });

    // Screenshot Interval birimini de güncelle
    fetchScreenshotInterval();

    // Dropdown placeholders
    const projectDropdown = document.getElementById("project");
    if (projectDropdown && projectDropdown.options.length > 0) {
        projectDropdown.options[0].textContent = t.selectProject;
        // Update custom dropdown display
        const projectCustomDropdown = projectDropdown.closest('.select-wrapper')?.querySelector('.custom-dropdown');
        if (projectCustomDropdown) {
            updateCustomDropdownDisplay(projectDropdown, projectCustomDropdown);
        }
    }

    const taskDropdown = document.getElementById("task");
    if (taskDropdown && taskDropdown.options.length > 0) {
        taskDropdown.options[0].textContent = t.selectTask;
        // Update custom dropdown display
        const taskCustomDropdown = taskDropdown.closest('.select-wrapper')?.querySelector('.custom-dropdown');
        if (taskCustomDropdown) {
            updateCustomDropdownDisplay(taskDropdown, taskCustomDropdown);
        }
    }

    // Modal translations
    document.getElementById('modalTitle').textContent = t.modalTitle;
    document.getElementById('modalDesc').textContent = t.modalDesc;
    document.getElementById('modalSubmitBtn').textContent = t.submit;
    document.getElementById('taskDetailInput').placeholder = t.modalPlaceholder;
    
    // Logout modal
    document.getElementById("logout").textContent = t.logout;
    if (document.getElementById("logoutModalTitle"))
        document.getElementById("logoutModalTitle").textContent = t.logoutTitle;
    if (document.getElementById("logoutModalDesc"))
        document.getElementById("logoutModalDesc").textContent = t.logoutDesc;
    if (document.getElementById("logoutConfirmBtn"))
        document.getElementById("logoutConfirmBtn").textContent = t.logoutConfirm;
    if (document.getElementById("logoutCancelBtn"))
        document.getElementById("logoutCancelBtn").textContent = t.logoutCancel;

    // Review modal
    const reviewModalTitle = document.getElementById("reviewModalTitle");
    if (reviewModalTitle) reviewModalTitle.textContent = t.feedbackTitle;
    const reviewModalDesc = document.getElementById("reviewModalDesc");
    if (reviewModalDesc) reviewModalDesc.textContent = t.feedbackDesc;
    const reviewInput = document.getElementById("reviewInput");
    if (reviewInput) reviewInput.placeholder = t.feedbackPlaceholder;
    const reviewSubmitBtn = document.getElementById("reviewSubmitBtn");
    if (reviewSubmitBtn) reviewSubmitBtn.textContent = t.feedbackSubmit;

    // Navigation
    if (document.getElementById("navDashboard"))
        document.getElementById("navDashboard").textContent = t.navDashboard;
    if (document.getElementById("navHelp"))
        document.getElementById("navHelp").textContent = t.navHelp;
    if (document.getElementById("navSettings"))
        document.getElementById("navSettings").textContent = t.navSettings;
    if (document.getElementById("navFeedback"))
        document.getElementById("navFeedback").textContent = t.navFeedback;

    // Remember me
    if (document.getElementById("rememberMeLabel")) {
        document.getElementById("rememberMeLabel").textContent = t.rememberMe;
    }

    // Logging input
    const loggingInput = document.getElementById('loggingInput');
    if (loggingInput) {
        const currentVal = loggingInput.value.toUpperCase();
        if (currentVal === 'YES' || currentVal === 'EVET') {
            loggingInput.value = lang === 'tr' ? 'EVET' : 'YES';
        } else if (currentVal === 'NO' || currentVal === 'HAYIR') {
            loggingInput.value = lang === 'tr' ? 'HAYIR' : 'NO';
        }
    }

    // Update displayUserName if it's still loading
    const displayUserName = document.getElementById('displayUserName');
    if (displayUserName && displayUserName.textContent === 'Loading...') {
        displayUserName.textContent = t.loading;
    }
}

window.addEventListener("load", () => {
    // ✅ FIX: Don't silently kill the timer on page reload.
    // Previously: if isTimerRunning, immediately resetTimer() — causing silent data loss.
    // Now: if a session was active, try to recover it from the backend.
    if (isTimerRunning) {
        console.log("⚠️ App loaded while timer was running — attempting session recovery");
        
        // Try to recover session state from backend
        fetch('/check_session_state')
            .then(res => res.json())
            .then(data => {
                if (data.active) {
                    console.log("✅ Session still active on backend, keeping timer alive");
                    // Session is still alive on backend — don't reset
                } else {
                    console.log("⚠️ No active session on backend, resetting timer");
                    resetTimer();
                    stopScreenRecording();
                    stopDailyLogsCapture();
                }
            })
            .catch(err => {
                console.error("⚠️ Failed to check session state, resetting as safety measure:", err);
                resetTimer();
                stopScreenRecording();
                stopDailyLogsCapture();
            });
    }
});

window.addEventListener("beforeunload", (event) => {
    // ✅ FIX: Use navigator.sendBeacon instead of async fetch.
    // Browsers do NOT guarantee async fetch completion in unload handlers.
    // sendBeacon is designed specifically for this — it queues the request
    // and the browser guarantees delivery even after the page closes.
    if (isTimerRunning || isMeetingTimerRunning) {
        console.log(" App closing: Auto-stopping timer & saving session via sendBeacon");

        const detailText = translations[sessionStorage.getItem('selectedLanguage') || 'en'].autoSavedAppExit;
        const end_time_unix = Math.floor(Date.now() / 1000);

        let payload;
        if (currentMode === 'work') {
            payload = {
                email: user.email,
                staff_id: String(user.staffid),
                task_id: currentTaskId,
                end_time: end_time_unix,
                note: detailText,
                is_meeting: false
            };
        } else {
            const actualMeetingDuration = meetingStartTime ? (end_time_unix - meetingStartTime) : meetingTotalSeconds;
            payload = {
                email: user.email,
                staff_id: String(user.staffid),
                task_id: currentTaskId,
                end_time: end_time_unix,
                note: detailText,
                is_meeting: true,
                meetings: [{ duration_seconds: actualMeetingDuration, notes: detailText }]
            };
        }

        // sendBeacon guarantees delivery even during page unload
        const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
        navigator.sendBeacon('/end_task_session', blob);

        resetTimer();
        stopMeetingTimer();
        stopScreenRecording();
        stopDailyLogsCapture();
    }
});

async function uploadUsageLogToS3() {
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    let taskName = '';
    
    if (currentMode === 'work') {
        const taskSelect = document.getElementById('task');
        taskName = taskSelect.options[taskSelect.selectedIndex]?.textContent;
    } else {
        taskName = 'Meeting Session';
    }

    if (!taskName || !user?.email) {
        showToast(translations[lang].selectTaskWarning, "error");
        return;
    }

    try {
        const res = await fetch('/upload_log_to_s3', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: user.email,
                task_name: taskName
            })
        });

        const data = await res.json();
        if (data.success) {
            console.log(" AI Summary:", data.summary);
        } else {
            showToast(translations[lang].failedUpload + data.message, 'error');
        }
    } catch (err) {
        console.error(" Error uploading usage log:", err);
        showToast(translations[lang].unexpectedErrorUpload, "error");
    }
}

const stateConfig = {
    work: {
        label: 'WORK',
        message: 'Currently in WORK mode - Stay focused and productive! ',
    },
    idle: {
        label: 'IDLE',
        message: 'Taking a moment to breathe - Ready when you are! ',
    },
    break: {
        label: 'BREAK',
        message: 'Break time! Recharge and come back stronger ',
    },
    meeting: {
        label: 'MEETING',
        message: 'In a meeting - Collaborating and connecting! ',
    }
};

function setState(state) {
    const stateCircle = document.getElementById('stateCircle');
    const stateLabel = document.getElementById('stateLabel');
    const statusText = document.getElementById('statusText');
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';

    const config = stateConfig[state];

    if (!stateCircle || !stateLabel) {
        console.warn("⛔ Missing stateCircle or stateLabel in DOM");
        return;
    }

    stateCircle.className = 'state-circle';
    stateCircle.classList.add(state);

    const translatedLabel = translations?.[lang]?.[state] || config.label;
    stateLabel.textContent = translatedLabel;

    if (statusText) {
        const message = translations?.[lang]?.statusText?.[state] || config.message;
        statusText.textContent = message;
    }

    const startBtn = document.getElementById('startBtn');
    const breakBtn = document.getElementById('breakBtn');

    if (state === 'work') {
        startBtn.disabled = false;
        startBtn.style.backgroundColor = '#006039';
        if (breakBtn) {
            breakBtn.disabled = false;
            breakBtn.style.backgroundColor = '#007bff';
        }
    } else if (state === 'break') {
        if (breakBtn) {
            breakBtn.disabled = true;
            breakBtn.style.backgroundColor = 'gray';
        }
        startBtn.disabled = false;
        startBtn.style.backgroundColor = '#006039';
    } else {
        startBtn.disabled = false;
        if (breakBtn) breakBtn.disabled = false;
        startBtn.style.backgroundColor = '#006039';
        if (breakBtn) breakBtn.style.backgroundColor = '#007bff';
    }

    stateCircle.style.transform = 'scale(0.95)';
    setTimeout(() => {
        stateCircle.style.transform = '';
    }, 100);
}


// HTML'e eklenmesi gereken mode selection butonları için CSS
const modeSelectionCSS = `
<style>
.mode-selection {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    justify-content: center;
    padding: 15px;
    border-radius: 15px;
}

.mode-btn {
    padding: 12px 24px;
    border: 2px solid #006039;
    background: white;
    color: #006039;
    border-radius: 10px;
    cursor: pointer;
    font-weight: bold;
    transition: all 0.3s ease;
    position: relative;
    // overflow: hidden;
    min-width: 120px;
    text-align: center;
}



.mode-btn:hover::before {
    left: 100%;
}

.mode-btn:hover:not(.active) {
    background: #f8f9fa;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 96, 57, 0.2);
}

/* Active state for selected button */
.mode-btn.active {
    background: #006039;
    color: white;
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0, 96, 57, 0.4);
    border-color: #006039;
}

.mode-btn.active:hover {
    background: #005530;
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 96, 57, 0.5);
}

/* Add selected indicator */
.mode-btn.active::after {
    content: '✓';
    position: absolute;
    top: -5px;
    right: -5px;
    background: white;
    color: #006039;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}
</style>
`;

// CSS'i document head'e ekle
document.head.insertAdjacentHTML('beforeend', modeSelectionCSS);

console.log(' Enhanced client.js with meeting mode functionality loaded');
let demoInterval;
function startDemo() {
    const states = ['work', 'idle', 'break', 'meeting'];
    let currentIndex = 0;

    demoInterval = setInterval(() => {
        currentIndex = (currentIndex + 1) % states.length;
        setState(states[currentIndex]);
    }, 5000);
}

function stopDemo() {
    if (demoInterval) {
        clearInterval(demoInterval);
    }
}

function handleBreak() {
    pauseTimer();
    setState('break');

    const breakBtn = document.getElementById('breakBtn');
    breakBtn.disabled = true;
    breakBtn.style.backgroundColor = 'gray';
}

function createRipple(event) {
    const button = event.currentTarget;
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');

    button.appendChild(ripple);

    setTimeout(() => {
        ripple.remove();
    }, 600);
}

function handleNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const navItems = document.querySelectorAll('.nav-item');

    navLinks.forEach((link, index) => {
        link.addEventListener('click', (e) => {
            e.preventDefault();

            navItems.forEach(item => item.classList.remove('active'));
            navItems[index].classList.add('active');

            createRipple(e);

            const page = link.dataset.page;
            console.log(`Navigating to: ${page}`);

            link.style.animation = 'none';
            setTimeout(() => {
                link.style.animation = '';
            }, 100);
        });
    });
}

function addAdvancedHoverEffects() {
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        const navText = link.querySelector('.nav-text');
        if (navText && navText.id === 'navFeedback') {
            return;
        }

        link.addEventListener('mouseenter', () => {
            link.style.transform = 'translateY(-5px) scale(1.02)';
        });

        link.addEventListener('mouseleave', () => {
            if (!link.parentElement.classList.contains('active')) {
                link.style.transform = 'translateY(0) scale(1)';
            }
        });

        link.addEventListener('mousemove', (e) => {
            const rect = link.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;

            link.style.transform = `translateY(-5px) scale(1.02) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    handleNavigation();
    addAdvancedHoverEffects();
    
    const feedbackLink = document.querySelector('.nav-link:has(#navFeedback)') || 
                        document.getElementById('navFeedback')?.closest('.nav-link');
    if (feedbackLink) {
        feedbackLink.style.transform = 'none';
        feedbackLink.style.transition = 'none';
    }

    const drawerArrowBtn = document.getElementById('drawerArrowBtn');
    if (drawerArrowBtn) {
        drawerArrowBtn.style.backgroundColor = '';
        drawerArrowBtn.style.borderColor = '';
        drawerArrowBtn.style.borderRadius = '';
        console.log(' Drawer arrow button colors reset to CSS defaults');
    }

    const drawerElements = [
        document.querySelector('.drawer'),
        document.querySelector('.drawer-header'),
        document.querySelector('.drawer-content'),
        ...document.querySelectorAll('.drawer-section'),
        ...document.querySelectorAll('.drawer-section-header'),
        ...document.querySelectorAll('.drawer-item'),
        ...document.querySelectorAll('.project-details'),
        ...document.querySelectorAll('.task-details'),
        ...document.querySelectorAll('.time-details')
    ];

    drawerElements.forEach(element => {
        if (element) {
            element.style.backgroundColor = '';
            element.style.background = '';
            element.style.color = '';
        }
    });
    console.log(' Drawer content background colors reset to CSS defaults');

    if (drawerArrowBtn) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                    const target = mutation.target;
                    
                    if (target.id === 'drawerArrowBtn') {
                        if (target.style.backgroundColor && target.style.backgroundColor !== '') {
                            target.style.backgroundColor = '';
                        }
                        if (target.style.borderColor && target.style.borderColor !== '') {
                            target.style.borderColor = '';
                        }
                        console.log('Prevented color override on drawer arrow button');
                    }
                    
                    if (target.classList.contains('drawer') ||
                        target.classList.contains('drawer-header') || 
                        target.classList.contains('drawer-content') ||
                        target.classList.contains('drawer-section') ||
                        target.classList.contains('drawer-section-header') ||
                        target.classList.contains('drawer-item') ||
                        target.classList.contains('project-details') ||
                        target.classList.contains('task-details') ||
                        target.classList.contains('time-details')) {
                        
                        if (target.style.backgroundColor && target.style.backgroundColor !== '') {
                            target.style.backgroundColor = '';
                        }
                        if (target.style.background && target.style.background !== '') {
                            target.style.background = '';
                        }
                        if (target.style.color && target.style.color !== '') {
                            target.style.color = '';
                        }
                        console.log('Prevented color override on drawer element:', target.className);
                    }
                }
            });
        });
        
        observer.observe(drawerArrowBtn, { 
            attributes: true, 
            attributeFilter: ['style'] 
        });
        
        const allDrawerElements = [
            document.querySelector('.drawer'),
            document.querySelector('.drawer-header'),
            document.querySelector('.drawer-content'),
            ...document.querySelectorAll('.drawer-section'),
            ...document.querySelectorAll('.drawer-section-header'),
            ...document.querySelectorAll('.drawer-item'),
            ...document.querySelectorAll('.project-details'),
            ...document.querySelectorAll('.task-details'),
            ...document.querySelectorAll('.time-details')
        ];
        
        allDrawerElements.forEach(element => {
            if (element) {
                observer.observe(element, { 
                    attributes: true, 
                    attributeFilter: ['style'] 
                });
            }
        });
        
        console.log('Protection set up for all drawer elements');
    }

    const container = document.querySelector('.nav-container');
    setTimeout(() => {
        container.style.transform = 'scale(1)';
        container.style.opacity = '1';
    }, 100);
});

document.addEventListener('keydown', (e) => {
    const activeItem = document.querySelector('.nav-item.active');
    const navItems = Array.from(document.querySelectorAll('.nav-item'));
    const currentIndex = navItems.indexOf(activeItem);

    if (e.key === 'ArrowLeft' && currentIndex > 0) {
        navItems[currentIndex].classList.remove('active');
        navItems[currentIndex - 1].classList.add('active');
        navItems[currentIndex - 1].querySelector('.nav-link').focus();
    } else if (e.key === 'ArrowRight' && currentIndex < navItems.length - 1) {
        navItems[currentIndex].classList.remove('active');
        navItems[currentIndex + 1].classList.add('active');
        navItems[currentIndex + 1].querySelector('.nav-link').focus();
    }
});

function openModalWithAnimation(modalId, callback) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.style.display = "flex";
    setTimeout(() => {
      modal.classList.remove('hide');
      modal.classList.add('show');
      if (callback) callback();
    }, 10);
}

function closeModalWithAnimation(modalId, callback) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.classList.remove('show');
    modal.classList.add('hide');
    
    setTimeout(() => {
      modal.style.display = "none";
      modal.classList.remove('hide');
      if (callback) callback();
    }, 300);
}

function openReviewModal() {
    const modal = document.getElementById("reviewModal");
    modal.style.display = "flex";
    setTimeout(() => {
      modal.classList.remove('hide');
      modal.classList.add('show');
    }, 10);
}

function closeReviewModal() {
    const modal = document.getElementById("reviewModal");
    modal.classList.remove('show');
    modal.classList.add('hide');
    
    setTimeout(() => {
      modal.style.display = "none";
      modal.classList.remove('hide');
    }, 300);
}

function submitUserReview() {
    const reviewText = document.getElementById('reviewInput').value.trim();
    const user = JSON.parse(sessionStorage.getItem('user'));

    if (!reviewText || !user?.email || !user?.firstName) {
        showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].missingReviewInfo, 'error');
        return;
    }

    fetch('/submit-feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: user.email,
            username: `${user.firstName} ${user.lastName || ''}`.trim(),
            message: reviewText
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].feedbackSent);
            closeReviewModal();
            document.getElementById('reviewInput').value = '';
        } else {
        }
    })
    .catch(err => {
        console.error('Feedback error:', err);
        showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].feedbackError, 'error');
    });
}

function openInNewTab(url) {
    try {
        window.open(url, '_blank');
    } catch (err) {
        console.error(" Failed to open new tab:", err);
    }
}

function openLogoutModal() {
  //  Check for both work timer and meeting timer running
  if (isTimerRunning || isMeetingTimerRunning) {
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    showToast(translations[lang].cannotLogoutRunning, "error");
    return;
  }

  const modal = document.getElementById("logoutModal");
  modal.style.display = "flex";
  setTimeout(() => {
    modal.classList.remove('hide');
    modal.classList.add('show');
  }, 10);
}

function closeLogoutModal() {
    const modal = document.getElementById("logoutModal");
    modal.classList.remove('show');
    modal.classList.add('hide');
    
    setTimeout(() => {
      modal.style.display = "none";
      modal.classList.remove('hide');
    }, 300);
}

function closeIdleModal() {
    const idleModal = document.getElementById("idleModal");
    if (idleModal) {
        idleModal.classList.remove('show');
        idleModal.classList.add('hide');
        
        // Hide modal after animation completes
        setTimeout(() => {
            idleModal.style.display = 'none';
            idleModal.classList.remove('hide');
            
            // Re-enable all buttons after 5 seconds
            setTimeout(() => {
                const startBtn = document.getElementById('startBtn');
                const workModeBtn = document.querySelector('.mode-btn[data-mode="work"]');
                const meetingModeBtn = document.querySelector('.mode-btn[data-mode="meeting"]');
                const finishBtn = document.getElementById('finishBtn');
                
                if (startBtn) {
                    startBtn.disabled = false;
                    startBtn.style.backgroundColor = '#006039';
                    startBtn.style.opacity = '1';
                }
                if (workModeBtn) {
                    workModeBtn.disabled = false;
                    workModeBtn.style.opacity = '1';
                }
                if (meetingModeBtn) {
                    meetingModeBtn.disabled = false;
                    meetingModeBtn.style.opacity = '1';
                }
                if (finishBtn) {
                    finishBtn.disabled = false;
                    finishBtn.style.backgroundColor = '#d9534f';
                    finishBtn.style.opacity = '1';
                }
                
                const lang = sessionStorage.getItem('selectedLanguage') || 'en';
                const message = lang === 'tr' ? 'Çalışmaya devam edebilirsiniz.' : 'You can continue working.';
                showToast(message, "success");
            }, 5000);
        }, 300);
    }
}

function restartWork() {
    // Close idle modal
    closeIdleModal();
    
    // Reset session start time
    sessionStartTime = Math.floor(Date.now() / 1000);
    
    // Reset activity time
    lastActivityTime = Date.now();
    
    // Start appropriate timer based on current mode
    if (currentMode === 'work') {
        startTimer();
        setState('work');
    } else if (currentMode === 'meeting') {
        startMeetingTimer();
        setState('meeting');
    }
    
    // Show success message
    const lang = sessionStorage.getItem('selectedLanguage') || 'en';
    const message = currentMode === 'meeting'
        ? (lang === 'tr' ? 'Toplantı yeniden başlatıldı!' : 'Meeting restarted successfully!')
        : (lang === 'tr' ? 'Çalışma yeniden başlatıldı!' : 'Work restarted successfully!');
    showToast(message, "success");
}

function cancelIdleCountdown() {
    clearInterval(idleCountdownInterval);
    closeIdleModal();

    sessionStartTime = Math.floor(Date.now() / 1000);
    
    // Reset activity time to prevent immediate idle detection
    lastActivityTime = Date.now();
    
    // Clear any existing idle warning toast and timers
    if (idleWarningToast) {
        closeIdleWarningToast();
    }
    if (idleWarningCountdownInterval) {
        clearInterval(idleWarningCountdownInterval);
        idleWarningCountdownInterval = null;
    }

    startTimer();
    setState('work');
    showToast(translations[sessionStorage.getItem('selectedLanguage') || 'en'].countdownCanceled, "success");
}

setInterval(() => {
    console.log(' Client.js: Periodic styling refresh...');
}, 5 * 60 * 1000);

window.refreshStyling = function() {
    console.log('🧪 Manual styling refresh triggered...');
};

window.testClientStyling = function() {
    console.log('🧪 Testing client styling integration...');
    
    const buttonSelectors = ['#startBtn', '#resetBtn', '.modal-btn', 'button'];
    buttonSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        console.log(`Found ${elements.length} elements for selector: ${selector}`);
    });
};

window.debugClientColors = function() {
    const root = document.documentElement;
    const style = getComputedStyle(root);
    
    console.log(' Current Client.js CSS Variables:');
    console.log('--primary-color:', style.getPropertyValue('--primary-color').trim());
    console.log('--secondary-color:', style.getPropertyValue('--secondary-color').trim());
    console.log('--background-color:', style.getPropertyValue('--background-color').trim());
    console.log('--button-color:', style.getPropertyValue('--button-color').trim());
    console.log('--text-color:', style.getPropertyValue('--text-color').trim());
    
    console.log(' NEW Color Fields:');
    console.log('--header-color:', style.getPropertyValue('--header-color').trim());
    console.log('--footer-color:', style.getPropertyValue('--footer-color').trim());
    console.log('--button-text-color:', style.getPropertyValue('--button-text-color').trim());
    
    const startBtn = document.getElementById('startBtn');
    if (startBtn) {
        const btnStyle = getComputedStyle(startBtn);
        console.log('Start Button Background:', btnStyle.backgroundColor);
        console.log('Start Button Color (text):', btnStyle.color);
        console.log('Start Button Border:', btnStyle.borderColor);
    }

    const logoutBtn = document.getElementById('logout');
    if (logoutBtn) {
        const logoutStyle = getComputedStyle(logoutBtn);
        console.log(' Logout Button Background:', logoutStyle.backgroundColor);
        console.log(' Logout Button Color:', logoutStyle.color);
        console.log(' Logout Button Border:', logoutStyle.borderColor);
    }

    const languageBtn = document.querySelector('.language-btn');
    if (languageBtn) {
        const langStyle = getComputedStyle(languageBtn);
        console.log('Language Button Background:', langStyle.backgroundColor);
        console.log('Language Button Color:', langStyle.color);
        console.log('Language Button Border:', langStyle.borderColor);
    }

    const headerElements = document.querySelectorAll('header, .header, .window-header');
    headerElements.forEach((header, index) => {
        const headerStyle = getComputedStyle(header);
        console.log(` Header ${index + 1} Background:`, headerStyle.backgroundColor);
    });

    const footerElements = document.querySelectorAll('footer, .footer');
    footerElements.forEach((footer, index) => {
        const footerStyle = getComputedStyle(footer);
        console.log(` Footer ${index + 1} Background:`, footerStyle.backgroundColor);
    });
};

const originalSetState = setState;
setState = function(state) {
    originalSetState(state);
    
    setTimeout(() => {
    }, 100);
};

console.log(' Client.js: DDS Styling API integration completed');
console.log('🧪 Debug functions available: refreshStyling(), testClientStyling(), debugClientColors()');

window.testAllAPIColorFields = async function() {
    console.log('🧪 Testing ALL API Color Fields...');
    
    try {
        const root = document.documentElement;
        const style = getComputedStyle(root);
        
        console.log(' Current CSS Variables:');
        console.log('=======================================');
        console.log('--header-color:', style.getPropertyValue('--header-color').trim());
        console.log('--footer-color:', style.getPropertyValue('--footer-color').trim());
        console.log('--button-text-color:', style.getPropertyValue('--button-text-color').trim());
        console.log('--text-color:', style.getPropertyValue('--text-color').trim());
        console.log('--background-color:', style.getPropertyValue('--background-color').trim());
        console.log('--button-color:', style.getPropertyValue('--button-color').trim());
        
        console.log(' API Color Fields Test Complete!');
        return true;
    } catch (error) {
        console.error(' API Color Fields Test Error:', error);
        return false;
    }
};

console.log('New function available: testAllAPIColorFields()');

window.verifyColorImplementation = function() {
    console.log('Verifying Color Field Implementation...');
    
    const colorTests = [
        {
            name: 'Header Elements',
            selectors: ['header', '.header', '.window-header', '.navbar'],
            property: 'background-color',
            expectedVar: '--header-color'
        },
        {
            name: 'Footer Elements', 
            selectors: ['footer', '.footer', '.bottom-footer'],
            property: 'background-color',
            expectedVar: '--footer-color'
        },
        {
            name: 'Button Text',
            selectors: ['button:not(#logout):not(.language-btn)', '.btn:not(#logout):not(.language-btn)'],
            property: 'color',
            expectedVar: '--button-text-color'
        }
    ];
    
    colorTests.forEach(test => {
        console.log(`\n🧪 Testing ${test.name}:`);
        test.selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            console.log(`  ${selector}: Found ${elements.length} elements`);
            
            elements.forEach((element, index) => {
                const style = getComputedStyle(element);
                const value = style.getPropertyValue(test.property);
                console.log(`    Element ${index + 1}: ${test.property} = ${value}`);
            });
        });
    });
    
    console.log('\n Color Implementation Verification Complete!');
};

console.log('New function available: verifyColorImplementation()');

window.forceWhiteHeaderButtons = function() {
    console.log(' Forcing white header button styling...');
    
    const logoutBtn = document.getElementById('logout');
    if (logoutBtn) {
        logoutBtn.style.setProperty('background-color', 'white', 'important');
        logoutBtn.style.setProperty('color', 'white', 'important');
        logoutBtn.style.setProperty('border-color', 'white', 'important');
        console.log(' Logout button forced to white');
    }

    const languageBtn = document.querySelector('.language-btn');
    if (languageBtn) {
        languageBtn.style.setProperty('background-color', 'white', 'important');
        languageBtn.style.setProperty('color', 'white', 'important');
        languageBtn.style.setProperty('border-color', 'white', 'important');
        console.log(' Language button forced to white');
    }

    console.log(' White header button styling complete');
};

console.log(' Additional function: forceWhiteHeaderButtons()');

function preventNavigationBlackBackgrounds() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                    const style = link.getAttribute('style');
                    if (style && (style.includes('rgb(0, 0, 0)') || style.includes('background-color: black') || style.includes('background: black'))) {
                        const cleanStyle = style
                            .replace(/background-color:\s*rgb\(0,\s*0,\s*0\)\s*!important;?/gi, '')
                            .replace(/background-color:\s*black\s*!important;?/gi, '')
                            .replace(/background:\s*rgb\(0,\s*0,\s*0\)\s*!important;?/gi, '')
                            .replace(/background:\s*black\s*!important;?/gi, '');
                        
                        link.setAttribute('style', cleanStyle);
                        console.log('Prevented black background on navigation link');
                    }
                }
            });
        });
        
        observer.observe(link, { attributes: true, attributeFilter: ['style'] });
    });
}

document.addEventListener('DOMContentLoaded', preventNavigationBlackBackgrounds);

// ✅ Page Visibility API - Sync timer when tab becomes visible again
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        console.log('🔄 Tab is now visible - syncing timer display');
        
        // Immediately update timer display based on timestamp if timer is running
        if (isTimerRunning && sessionStartTime) {
            const currentTime = Math.floor(Date.now() / 1000);
            totalSeconds = currentTime - sessionStartTime;
            
            document.getElementById('hours').innerText = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
            document.getElementById('minutes').innerText = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0');
            document.getElementById('seconds').innerText = String(totalSeconds % 60).padStart(2, '0');
            
            console.log(`✅ Work timer synced: ${Math.floor(totalSeconds / 60)}m ${totalSeconds % 60}s`);
        }
        
        // Sync meeting timer if running
        if (isMeetingTimerRunning && meetingStartTime) {
            const currentTime = Math.floor(Date.now() / 1000);
            meetingTotalSeconds = currentTime - meetingStartTime;
            
            document.getElementById('hours').innerText = String(Math.floor(meetingTotalSeconds / 3600)).padStart(2, '0');
            document.getElementById('minutes').innerText = String(Math.floor((meetingTotalSeconds % 3600) / 60)).padStart(2, '0');
            document.getElementById('seconds').innerText = String(meetingTotalSeconds % 60).padStart(2, '0');
            
            console.log(`✅ Meeting timer synced: ${Math.floor(meetingTotalSeconds / 60)}m ${meetingTotalSeconds % 60}s`);
        }
    }
});

// End of client.js
// Zamanı yerelleştirilmiş formatta güncelleyen fonksiyon ve interval
function updateLoggedTime() {
    const loggedTimeElem = document.getElementById('totalLoggedTime');
    if (!loggedTimeElem) return;
    const now = new Date();
    loggedTimeElem.textContent = now.toLocaleTimeString();
}
setInterval(updateLoggedTime, 1000);