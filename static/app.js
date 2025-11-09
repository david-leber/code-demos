// App state
let currentLesson = null;
let currentExercise = null;

// DOM elements
const lessonsListEl = document.getElementById('lessons-list');
const lessonTitleEl = document.getElementById('lesson-title');
const lessonDescriptionEl = document.getElementById('lesson-description');
const lessonObjectivesEl = document.getElementById('lesson-objectives');
const lessonExercisesEl = document.getElementById('lesson-exercises');
const codeEditorEl = document.getElementById('code-editor');
const runBtnEl = document.getElementById('run-btn');
const reviewBtnEl = document.getElementById('review-btn');
const outputContentEl = document.getElementById('output-content');
const aiContentEl = document.getElementById('ai-content');

// Initialize app
async function init() {
    await loadLessons();
    setupEventListeners();
}

// Load all lessons
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

        // Load first lesson by default
        if (data.lessons.length > 0) {
            loadLesson(data.lessons[0].id);
        }
    } catch (error) {
        console.error('Failed to load lessons:', error);
        lessonsListEl.innerHTML = '<p>Failed to load lessons. Make sure the server is running.</p>';
    }
}

// Create lesson element
function createLessonElement(lesson) {
    const div = document.createElement('div');
    div.className = 'lesson-item';
    div.innerHTML = `
        <h3>${lesson.title}</h3>
        <p>${lesson.description}</p>
    `;
    div.addEventListener('click', () => loadLesson(lesson.id));
    return div;
}

// Load a specific lesson
async function loadLesson(lessonId) {
    try {
        const response = await fetch(`/api/lessons/${lessonId}`);
        const lesson = await response.json();

        currentLesson = lesson;
        currentExercise = lesson.exercises.length > 0 ? lesson.exercises[0] : null;

        // Update UI
        lessonTitleEl.textContent = lesson.title;
        lessonDescriptionEl.textContent = lesson.description;

        // Objectives
        if (lesson.objectives.length > 0) {
            lessonObjectivesEl.innerHTML = `
                <h4>Learning Objectives:</h4>
                <ul>
                    ${lesson.objectives.map(obj => `<li>${obj}</li>`).join('')}
                </ul>
            `;
        } else {
            lessonObjectivesEl.innerHTML = '';
        }

        // Exercises
        if (lesson.exercises.length > 0) {
            lessonExercisesEl.innerHTML = `
                <h4>Exercise:</h4>
                ${lesson.exercises.map((ex, idx) => `
                    <div class="exercise">
                        <p><strong>Task ${idx + 1}:</strong> ${ex.description}</p>
                    </div>
                `).join('')}
            `;
        } else {
            lessonExercisesEl.innerHTML = '';
        }

        // Set starter code
        codeEditorEl.value = lesson.starter_code || '# Write your code here\n';

        // Clear output and AI feedback
        outputContentEl.textContent = 'Run your code to see output here...';
        outputContentEl.className = 'output-content';
        aiContentEl.innerHTML = '<p>Write some code and click "Get AI Review" for feedback!</p>';

        // Update active lesson in sidebar
        document.querySelectorAll('.lesson-item').forEach(el => {
            el.classList.remove('active');
        });
        event.target.closest('.lesson-item')?.classList.add('active');

    } catch (error) {
        console.error('Failed to load lesson:', error);
        alert('Failed to load lesson');
    }
}

// Setup event listeners
function setupEventListeners() {
    runBtnEl.addEventListener('click', runCode);
    reviewBtnEl.addEventListener('click', getAIReview);
}

// Run code
async function runCode() {
    const code = codeEditorEl.value;

    if (!code.trim()) {
        alert('Please write some code first!');
        return;
    }

    runBtnEl.disabled = true;
    runBtnEl.textContent = '⏳ Running...';
    outputContentEl.textContent = 'Executing code...';
    outputContentEl.className = 'output-content';

    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code: code,
                lesson_id: currentLesson?.id,
                exercise_id: currentExercise?.id,
            }),
        });

        const result = await response.json();

        if (result.success) {
            outputContentEl.textContent = result.output || '(No output)';
            outputContentEl.className = 'output-content success';
        } else {
            outputContentEl.textContent = result.error || result.output;
            outputContentEl.className = 'output-content error';
        }

        outputContentEl.textContent += `\n\n--- Execution time: ${result.execution_time_ms}ms ---`;

    } catch (error) {
        console.error('Failed to run code:', error);
        outputContentEl.textContent = `Error: ${error.message}`;
        outputContentEl.className = 'output-content error';
    } finally {
        runBtnEl.disabled = false;
        runBtnEl.textContent = '▶ Run Code';
    }
}

// Get AI review
async function getAIReview() {
    const code = codeEditorEl.value;

    if (!code.trim()) {
        alert('Please write some code first!');
        return;
    }

    if (!currentLesson) {
        alert('Please select a lesson first!');
        return;
    }

    reviewBtnEl.disabled = true;
    reviewBtnEl.textContent = '⏳ Reviewing...';
    aiContentEl.innerHTML = '<p>Getting AI feedback...</p>';

    try {
        const response = await fetch('/api/review', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code: code,
                lesson_id: currentLesson.id,
            }),
        });

        const review = await response.json();

        // Display review
        let qualityClass = review.code_quality.toLowerCase().replace(/ /g, '-');
        let qualityText = review.code_quality.replace(/([A-Z])/g, ' $1').trim();

        let html = `
            <div class="ai-quality ${qualityClass}">${qualityText}</div>
            <p><strong>Feedback:</strong></p>
            <p>${review.feedback}</p>
        `;

        if (review.suggestions.length > 0) {
            html += `
                <p><strong>Suggestions:</strong></p>
                <ul>
                    ${review.suggestions.map(s => `<li>${s}</li>`).join('')}
                </ul>
            `;
        }

        if (review.follows_lesson_objectives) {
            html += `<p style="color: #4ec9b0;">✓ Your code meets the lesson objectives!</p>`;
        } else {
            html += `<p style="color: #f48771;">⚠ Your code doesn't fully meet the lesson objectives yet.</p>`;
        }

        aiContentEl.innerHTML = html;

    } catch (error) {
        console.error('Failed to get AI review:', error);
        aiContentEl.innerHTML = `<p style="color: #f48771;">Error: ${error.message}</p>`;
    } finally {
        reviewBtnEl.disabled = false;
        reviewBtnEl.textContent = '🤖 Get AI Review';
    }
}

// Start the app
init();
