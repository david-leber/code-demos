// App state
let sessionId = null;
let currentLessonId = null;
let currentPhase = 'Introduction';

// DOM elements
const lessonsListEl = document.getElementById('lessons-list');
const chatMessagesEl = document.getElementById('chat-messages');
const chatInputEl = document.getElementById('chat-input');
const codeEditorEl = document.getElementById('code-editor');
const outputContentEl = document.getElementById('output-content');
const phaseIndicatorEl = document.getElementById('phase-indicator');

const sendMessageBtn = document.getElementById('send-message-btn');
const requestHintBtn = document.getElementById('request-hint-btn');
const requestWalkthroughBtn = document.getElementById('request-walkthrough-btn');
const runCodeBtn = document.getElementById('run-code-btn');
const submitCodeBtn = document.getElementById('submit-code-btn');

// Initialize
async function init() {
    // Generate session ID
    sessionId = generateUUID();

    await loadLessons();
    setupEventListeners();
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Load lessons
async function loadLessons() {
    try {
        const response = await fetch('/api/lessons');
        const data = await response.json();

        if (data.lessons.length === 0) {
            lessonsListEl.innerHTML = '<p>No lessons available yet.</p>';
            return;
        }

        lessonsListEl.innerHTML = '';
        data.lessons.forEach(lesson => {
            const lessonEl = createLessonElement(lesson);
            lessonsListEl.appendChild(lessonEl);
        });
    } catch (error) {
        console.error('Failed to load lessons:', error);
        lessonsListEl.innerHTML = '<p>Failed to load lessons.</p>';
    }
}

function createLessonElement(lesson) {
    const div = document.createElement('div');
    div.className = 'lesson-item';
    div.innerHTML = `
        <h3>${lesson.title}</h3>
        <p>${lesson.description}</p>
    `;
    div.addEventListener('click', () => startLesson(lesson.id));
    return div;
}

// Start a lesson
async function startLesson(lessonId) {
    currentLessonId = lessonId;

    // Update UI
    document.querySelectorAll('.lesson-item').forEach(el => el.classList.remove('active'));
    event.target.closest('.lesson-item')?.classList.add('active');

    // Clear chat
    chatMessagesEl.innerHTML = '';

    // Clear code editor
    codeEditorEl.value = '';
    outputContentEl.textContent = 'Run your code to see output here...';
    outputContentEl.className = 'output-content';

    // Enable controls
    enableControls(false); // Disable until we get response

    // Send start lesson request
    const response = await sendTutorRequest({
        session_id: sessionId,
        lesson_id: lessonId,
        message: null,
        code: null,
        request_type: 'StartLesson'
    });

    if (response) {
        addMessageToChat('tutor', response.message);
        updatePhase(response.phase);
        enableControls(true);
    }
}

// Send a message to the tutor
async function sendMessage() {
    const message = chatInputEl.value.trim();
    if (!message) return;

    // Add student message to chat
    addMessageToChat('student', message);
    chatInputEl.value = '';

    // Disable controls while waiting
    enableControls(false);

    const response = await sendTutorRequest({
        session_id: sessionId,
        lesson_id: currentLessonId,
        message: message,
        code: null,
        request_type: 'SendMessage'
    });

    if (response) {
        addMessageToChat('tutor', response.message);
        updatePhase(response.phase);
        enableControls(true);
    }
}

// Submit code to tutor
async function submitCode() {
    const code = codeEditorEl.value.trim();
    if (!code) {
        alert('Please write some code first!');
        return;
    }

    // Disable controls
    enableControls(false);

    const response = await sendTutorRequest({
        session_id: sessionId,
        lesson_id: currentLessonId,
        message: null,
        code: code,
        request_type: 'SubmitCode'
    });

    if (response) {
        addMessageToChat('tutor', response.message);
        updatePhase(response.phase);

        if (response.code_result) {
            displayCodeResult(response.code_result);
        }

        if (response.show_new_challenge) {
            addMessageToChat('system', '⚠️ Since you needed a walkthrough, here\'s a new challenge to demonstrate mastery.');
        }

        enableControls(true);
    }
}

// Request a hint
async function requestHint() {
    enableControls(false);

    const response = await sendTutorRequest({
        session_id: sessionId,
        lesson_id: currentLessonId,
        message: null,
        code: null,
        request_type: 'RequestHint'
    });

    if (response) {
        addMessageToChat('tutor', '💡 Hint: ' + response.message);
        updatePhase(response.phase);
        enableControls(true);
    }
}

// Request a walkthrough
async function requestWalkthrough() {
    if (!confirm('Are you sure you want a full walkthrough? You\'ll need to complete a new challenge afterward to demonstrate mastery.')) {
        return;
    }

    enableControls(false);

    const response = await sendTutorRequest({
        session_id: sessionId,
        lesson_id: currentLessonId,
        message: null,
        code: null,
        request_type: 'RequestWalkthrough'
    });

    if (response) {
        addMessageToChat('tutor', '📖 Walkthrough:\n' + response.message);
        updatePhase(response.phase);

        if (response.show_new_challenge) {
            addMessageToChat('system', '⚠️ Since you needed a walkthrough, I\'ll give you a new challenge next to prove your understanding.');
        }

        enableControls(true);
    }
}

// Run code (without submitting to tutor)
async function runCode() {
    const code = codeEditorEl.value.trim();
    if (!code) {
        alert('Please write some code first!');
        return;
    }

    runCodeBtn.disabled = true;
    runCodeBtn.textContent = '⏳ Running...';
    outputContentEl.textContent = 'Executing code...';
    outputContentEl.className = 'output-content';

    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code })
        });

        const result = await response.json();
        displayCodeResult(result);
    } catch (error) {
        outputContentEl.textContent = `Error: ${error.message}`;
        outputContentEl.className = 'output-content error';
    } finally {
        runCodeBtn.disabled = false;
        runCodeBtn.textContent = '▶ Run Code';
    }
}

function displayCodeResult(result) {
    if (result.success) {
        outputContentEl.textContent = result.output || '(No output)';
        outputContentEl.className = 'output-content success';
    } else {
        outputContentEl.textContent = result.error || result.output;
        outputContentEl.className = 'output-content error';
    }

    outputContentEl.textContent += `\n\n--- Execution time: ${result.execution_time_ms}ms ---`;
}

// Send request to tutor API
async function sendTutorRequest(request) {
    try {
        const response = await fetch('/api/tutor/interact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText);
        }

        return await response.json();
    } catch (error) {
        console.error('Tutor request failed:', error);
        addMessageToChat('system', '⚠️ Error communicating with tutor: ' + error.message);
        enableControls(true);
        return null;
    }
}

// Add message to chat
function addMessageToChat(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    let roleName = '';
    switch (role) {
        case 'tutor':
            roleName = '🧠 AI Tutor';
            break;
        case 'student':
            roleName = '👤 You';
            break;
        case 'system':
            roleName = '';
            break;
    }

    if (roleName) {
        const roleDiv = document.createElement('div');
        roleDiv.className = 'message-role';
        roleDiv.textContent = roleName;
        messageDiv.appendChild(roleDiv);
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    messageDiv.appendChild(contentDiv);

    chatMessagesEl.appendChild(messageDiv);

    // Scroll to bottom
    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
}

// Update phase indicator
function updatePhase(phase) {
    currentPhase = phase;

    const phaseText = {
        'Introduction': '👋 Introduction',
        'Teaching': '📚 Learning Concepts',
        'Challenge': '🎯 Coding Challenge',
        'Helping': '🤔 Problem Solving',
        'Walkthrough': '📖 Walkthrough',
        'NewChallenge': '🎯 New Challenge',
        'Mastery': '🎉 Mastery Achieved!'
    };

    phaseIndicatorEl.textContent = phaseText[phase] || phase;

    // Enable/disable controls based on phase
    const canSubmitCode = ['Challenge', 'NewChallenge', 'Helping'].includes(phase);
    submitCodeBtn.disabled = !canSubmitCode;

    const canRequestHelp = ['Challenge', 'NewChallenge'].includes(phase);
    requestHintBtn.disabled = !canRequestHelp;
    requestWalkthroughBtn.disabled = !canRequestHelp;
}

// Enable/disable controls
function enableControls(enabled) {
    chatInputEl.disabled = !enabled;
    sendMessageBtn.disabled = !enabled;
    runCodeBtn.disabled = !enabled;

    if (!enabled) {
        submitCodeBtn.disabled = true;
        requestHintBtn.disabled = true;
        requestWalkthroughBtn.disabled = true;
    } else {
        updatePhase(currentPhase); // Re-apply phase-based enabling
    }
}

// Event listeners
function setupEventListeners() {
    sendMessageBtn.addEventListener('click', sendMessage);
    requestHintBtn.addEventListener('click', requestHint);
    requestWalkthroughBtn.addEventListener('click', requestWalkthrough);
    runCodeBtn.addEventListener('click', runCode);
    submitCodeBtn.addEventListener('click', submitCode);

    chatInputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

// Start the app
init();
