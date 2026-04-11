// EchoQuest Pro - Enhanced Frontend JavaScript
// Handles quiz logic, animations, API calls, and character integration

// Global variables
let currentQuestion = null;
let score = 0;
let questionsAnswered = 0;
let timeLeft = 20;
let timerInterval = null;
let canAnswer = true;
let quizCharacter = null;
let totalQuestions = 0;
let questionStartTime = null;
let keyboardEnabled = true;

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize character if on quiz page
    if (document.getElementById('question-text')) {
        // Wait for character to be available
        setTimeout(() => {
            if (typeof QuizCharacter !== 'undefined') {
                quizCharacter = new QuizCharacter();
            }
        }, 500);
        
        loadQuestion();
        setupEventListeners();
        setupKeyboardShortcuts();
    }
    
    // Setup form validation on auth pages
    if (document.querySelector('.auth-form')) {
        setupAuthValidation();
    }
    
    // Setup search functionality
    if (document.getElementById('topic-input')) {
        setupSearchAutocomplete();
    }
    
    // Animate elements on scroll
    setupScrollAnimations();
}

// Quiz Functions
function loadQuestion() {
    resetTimer();
    canAnswer = true;
    questionStartTime = Date.now();
    
    // Show loading state
    const questionText = document.getElementById('question-text');
    const optionsContainer = document.getElementById('options-container');
    
    if (questionText) questionText.textContent = 'Loading question...';
    if (optionsContainer) optionsContainer.innerHTML = '<div class="loading-spinner">🌀 Loading...</div>';
    
    // Fetch question from server
    fetch('/get_current_question')
        .then(response => response.json())
        .then(data => {
            if (data.quiz_ended) {
                endQuiz();
                return;
            }
            
            currentQuestion = data;
            displayQuestion(data);
            
            // Update character
            if (quizCharacter) {
                quizCharacter.onNewQuestion(data.question_number, data.total);
                quizCharacter.onQuestionLoad(data.difficulty);
            }
        })
        .catch(error => {
            console.error('Error loading question:', error);
            showError('Failed to load question. Please refresh the page.');
        });
}

function displayQuestion(question) {
    // Update question text
    const questionText = document.getElementById('question-text');
    if (questionText) {
        questionText.textContent = question.text;
        questionText.classList.add('fade-in');
        setTimeout(() => questionText.classList.remove('fade-in'), 500);
    }
    
    // Update question counter
    const qNumElement = document.getElementById('q-num');
    if (qNumElement) {
        qNumElement.textContent = `Question ${question.question_number}/${question.total}`;
    }
    
    // Update progress bar
    const progressFill = document.getElementById('progress-fill');
    if (progressFill) {
        const progressPercent = ((question.question_number - 1) / question.total) * 100;
        progressFill.style.width = `${progressPercent}%`;
    }
    
    // Update difficulty badge
    const difficultyElement = document.getElementById('difficulty');
    if (difficultyElement) {
        difficultyElement.innerHTML = getDifficultyBadge(question.difficulty);
    }
    
    // Create options
    const optionsContainer = document.getElementById('options-container');
    if (optionsContainer) {
        optionsContainer.innerHTML = '';
        const letters = ['A', 'B', 'C', 'D'];
        
        question.options.forEach((option, index) => {
            const button = document.createElement('button');
            button.className = 'option-enhanced fade-in';
            button.innerHTML = `
                <span class="opt-letter">${letters[index]}</span>
                <span class="opt-text">${escapeHtml(option)}</span>
            `;
            button.onclick = () => submitAnswer(letters[index]);
            button.setAttribute('data-opt', letters[index]);
            optionsContainer.appendChild(button);
        });
    }
    
    // Store hint
    window.currentHint = `💡 Hint: Think about ${question.text.substring(0, 50)}...`;
    
    // Enable keyboard shortcuts
    keyboardEnabled = true;
}

function getDifficultyBadge(difficulty) {
    const badges = {
        'easy': '<span class="badge easy">🟢 Easy</span>',
        'medium': '<span class="badge medium">🟡 Medium</span>',
        'hard': '<span class="badge hard">🔴 Hard</span>'
    };
    return badges[difficulty] || badges.medium;
}

function submitAnswer(answer) {
    if (!canAnswer) return;
    
    // Disable further answers
    canAnswer = false;
    keyboardEnabled = false;
    
    // Calculate time taken
    const timeTaken = Math.floor((Date.now() - questionStartTime) / 1000);
    
    // Stop timer
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    
    // Disable all option buttons
    const allOptions = document.querySelectorAll('.option-enhanced');
    allOptions.forEach(btn => {
        btn.style.opacity = '0.6';
        btn.disabled = true;
    });
    
    // Show loading state
    const feedback = document.getElementById('feedback');
    if (feedback) {
        feedback.innerHTML = '<div class="loading">🤔 Checking your answer...</div>';
    }
    
    // Send answer to server
    fetch('/submit_answer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            answer: answer,
            time_taken: timeTaken
        })
    })
    .then(response => response.json())
    .then(data => {
        // Update score display
        score = data.score;
        const scoreElement = document.getElementById('score');
        if (scoreElement) {
            scoreElement.textContent = score;
            scoreElement.classList.add('pulse');
            setTimeout(() => scoreElement.classList.remove('pulse'), 500);
        }
        
        // Update character and show feedback
        if (data.correct) {
            handleCorrectAnswer(data);
        } else {
            handleWrongAnswer(data);
        }
        
        // Update question counter
        questionsAnswered = data.next_q_num - 1;
        
        // Check if quiz ended
        if (data.quiz_ended) {
            setTimeout(() => endQuiz(), 2500);
        } else {
            // Load next question after delay
            setTimeout(() => {
                const feedbackDiv = document.getElementById('feedback');
                if (feedbackDiv) feedbackDiv.innerHTML = '';
                loadQuestion();
            }, 2500);
        }
    })
    .catch(error => {
        console.error('Error submitting answer:', error);
        if (feedback) {
            feedback.innerHTML = '<div class="error">❌ Network error. Please try again.</div>';
        }
        canAnswer = true;
        keyboardEnabled = true;
    });
}

function handleCorrectAnswer(data) {
    const feedback = document.getElementById('feedback');
    const pointsEarned = data.points_earned;
    
    // Create celebration effect
    createConfetti();
    
    // Show feedback
    if (feedback) {
        feedback.innerHTML = `
            <div class="correct-answer slide-in">
                <div class="correct-header">
                    <span class="correct-icon">✅</span>
                    <span class="correct-title">Correct!</span>
                    <span class="points-earned">+${pointsEarned} points</span>
                </div>
                <div class="explanation">${escapeHtml(data.explanation)}</div>
                ${pointsEarned >= 15 ? '<div class="bonus-badge">⚡ Speed Bonus!</div>' : ''}
            </div>
        `;
    }
    
    // Update character
    if (quizCharacter) {
        quizCharacter.onCorrectAnswer(pointsEarned);
        quizCharacter.createConfetti();
    }
    
    // Play success sound (if supported)
    playSound('correct');
    
    // Animate score
    animateScore(pointsEarned);
}

function handleWrongAnswer(data) {
    const feedback = document.getElementById('feedback');
    
    // Show feedback
    if (feedback) {
        feedback.innerHTML = `
            <div class="wrong-answer slide-in">
                <div class="wrong-header">
                    <span class="wrong-icon">❌</span>
                    <span class="wrong-title">Incorrect</span>
                </div>
                <div class="correct-answer-shown">Correct answer: <strong>${data.correct_answer}</strong></div>
                <div class="explanation">${escapeHtml(data.explanation)}</div>
                <div class="encouragement">💪 Don't worry! You'll get it next time!</div>
            </div>
        `;
    }
    
    // Update character
    if (quizCharacter) {
        quizCharacter.onWrongAnswer(data.correct_answer);
    }
    
    // Play error sound
    playSound('wrong');
    
    // Shake effect
    const questionContainer = document.querySelector('.question-container');
    if (questionContainer) {
        questionContainer.classList.add('shake');
        setTimeout(() => questionContainer.classList.remove('shake'), 500);
    }
}

function resetTimer() {
    // Reset time left
    timeLeft = 20;
    
    // Update timer display
    const timerElement = document.getElementById('timer');
    if (timerElement) {
        timerElement.textContent = timeLeft;
        timerElement.style.color = '#333';
        timerElement.style.transform = 'scale(1)';
    }
    
    // Reset progress circle
    const progressCircle = document.getElementById('timer-progress');
    if (progressCircle) {
        const circumference = 2 * Math.PI * 25;
        progressCircle.style.strokeDashoffset = '0';
    }
    
    // Clear existing interval
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    
    // Start new timer
    timerInterval = setInterval(() => {
        if (timeLeft > 0 && canAnswer) {
            timeLeft--;
            
            // Update timer display
            const timerElement = document.getElementById('timer');
            if (timerElement) {
                timerElement.textContent = timeLeft;
                
                // Change color based on time left
                if (timeLeft <= 5) {
                    timerElement.style.color = '#e74c3c';
                    timerElement.style.transform = 'scale(1.1)';
                    
                    // Warn character
                    if (quizCharacter) {
                        quizCharacter.onTimerLow(timeLeft);
                    }
                } else if (timeLeft <= 10) {
                    timerElement.style.color = '#f39c12';
                    timerElement.style.transform = 'scale(1.05)';
                } else {
                    timerElement.style.color = '#2ecc71';
                    timerElement.style.transform = 'scale(1)';
                }
            }
            
            // Update progress circle
            if (progressCircle) {
                const circumference = 2 * Math.PI * 25;
                const offset = circumference * (1 - timeLeft / 20);
                progressCircle.style.strokeDashoffset = offset;
            }
        }
        
        if (timeLeft === 0 && canAnswer) {
            // Time's up
            clearInterval(timerInterval);
            timerInterval = null;
            
            const feedback = document.getElementById('feedback');
            if (feedback) {
                feedback.innerHTML = '<div class="timeout">⏰ Time\'s up! Moving to next question...</div>';
            }
            
            // Update character
            if (quizCharacter) {
                quizCharacter.onTimeOut();
            }
            
            // Auto-submit empty answer (will be marked wrong)
            submitAnswer('');
        }
    }, 1000);
}

function endQuiz() {
    // Show ending animation
    const feedback = document.getElementById('feedback');
    if (feedback) {
        feedback.innerHTML = '<div class="quiz-ending">🎉 Quiz completed! Calculating your results... 🎉</div>';
    }
    
    // Update character
    if (quizCharacter) {
        const totalPossible = totalQuestions * 10;
        const percentage = (score / totalPossible) * 100;
        quizCharacter.onQuizComplete(score, totalQuestions, percentage);
    }
    
    // Send end quiz request
    fetch('/end_quiz', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
    })
    .then(() => {
        // Redirect to results page
        setTimeout(() => {
            window.location.href = '/result';
        }, 2000);
    })
    .catch(error => {
        console.error('Error ending quiz:', error);
        setTimeout(() => {
            window.location.href = '/result';
        }, 2000);
    });
}

// Helper Functions
function createConfetti() {
    const colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a'];
    
    for (let i = 0; i < 100; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.width = Math.random() * 10 + 5 + 'px';
        confetti.style.height = Math.random() * 10 + 5 + 'px';
        confetti.style.animationDelay = Math.random() * 2 + 's';
        confetti.style.animationDuration = Math.random() * 2 + 2 + 's';
        document.body.appendChild(confetti);
        
        setTimeout(() => confetti.remove(), 3000);
    }
}

function animateScore(points) {
    const scoreElement = document.getElementById('score');
    if (!scoreElement) return;
    
    // Create floating points animation
    const floatingPoints = document.createElement('div');
    floatingPoints.className = 'floating-points';
    floatingPoints.textContent = `+${points}`;
    floatingPoints.style.position = 'absolute';
    floatingPoints.style.left = scoreElement.getBoundingClientRect().left + 'px';
    floatingPoints.style.top = scoreElement.getBoundingClientRect().top + 'px';
    floatingPoints.style.color = '#2ecc71';
    floatingPoints.style.fontWeight = 'bold';
    floatingPoints.style.fontSize = '20px';
    floatingPoints.style.pointerEvents = 'none';
    floatingPoints.style.animation = 'floatUp 1s ease-out forwards';
    document.body.appendChild(floatingPoints);
    
    setTimeout(() => floatingPoints.remove(), 1000);
}

function playSound(type) {
    // Simple beep using Web Audio API (no external files needed)
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        if (type === 'correct') {
            oscillator.frequency.value = 880;
            gainNode.gain.value = 0.3;
            oscillator.start();
            gainNode.gain.exponentialRampToValueAtTime(0.00001, audioContext.currentTime + 0.5);
            oscillator.stop(audioContext.currentTime + 0.5);
        } else if (type === 'wrong') {
            oscillator.frequency.value = 440;
            gainNode.gain.value = 0.3;
            oscillator.start();
            gainNode.gain.exponentialRampToValueAtTime(0.00001, audioContext.currentTime + 0.3);
            oscillator.stop(audioContext.currentTime + 0.3);
        }
    } catch(e) {
        // Audio not supported, ignore
        console.log('Audio not supported');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    const feedback = document.getElementById('feedback');
    if (feedback) {
        feedback.innerHTML = `<div class="error-message">❌ ${message}</div>`;
    }
}

// Event Listeners Setup
function setupEventListeners() {
    // Hint button
    const hintBtn = document.getElementById('hint-btn');
    if (hintBtn) {
        hintBtn.addEventListener('click', function() {
            if (window.currentHint && canAnswer) {
                const feedback = document.getElementById('feedback');
                if (feedback) {
                    feedback.innerHTML = `<div class="hint-message slide-in">${window.currentHint}</div>`;
                    
                    if (quizCharacter) {
                        quizCharacter.onHintUsed();
                    }
                    
                    setTimeout(() => {
                        if (feedback.innerHTML.includes('Hint')) {
                            feedback.innerHTML = '';
                        }
                    }, 5000);
                }
                
                // Disable hint button after use
                hintBtn.disabled = true;
                hintBtn.style.opacity = '0.5';
                hintBtn.title = 'Hint already used for this question';
            } else if (!canAnswer) {
                const feedback = document.getElementById('feedback');
                if (feedback) {
                    feedback.innerHTML = '<div class="warning">⏳ Please wait for the next question!</div>';
                    setTimeout(() => {
                        if (feedback.innerHTML.includes('Please wait')) {
                            feedback.innerHTML = '';
                        }
                    }, 2000);
                }
            }
        });
    }
    
    // Refresh character position on resize
    window.addEventListener('resize', () => {
        if (quizCharacter && quizCharacter.characterElement) {
            // Ensure character stays visible
            const rect = quizCharacter.characterElement.getBoundingClientRect();
            if (rect.right > window.innerWidth) {
                quizCharacter.characterElement.style.right = '10px';
            }
        }
    });
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        if (!keyboardEnabled || !canAnswer) return;
        
        const key = event.key.toLowerCase();
        let option = null;
        
        // Number keys or letter keys
        if (key === '1' || key === 'a') option = 'A';
        else if (key === '2' || key === 'b') option = 'B';
        else if (key === '3' || key === 'c') option = 'C';
        else if (key === '4' || key === 'd') option = 'D';
        
        if (option) {
            event.preventDefault();
            
            // Highlight the selected option briefly
            const buttons = document.querySelectorAll('.option-enhanced');
            buttons.forEach(btn => {
                if (btn.getAttribute('data-opt') === option) {
                    btn.style.transform = 'scale(1.05)';
                    btn.style.background = '#667eea';
                    btn.style.color = 'white';
                    setTimeout(() => {
                        btn.style.transform = '';
                        btn.style.background = '';
                        btn.style.color = '';
                    }, 200);
                }
            });
            
            submitAnswer(option);
        }
        
        // H key for hint
        if (key === 'h') {
            const hintBtn = document.getElementById('hint-btn');
            if (hintBtn && !hintBtn.disabled) {
                hintBtn.click();
            }
        }
    });
    
    // Show keyboard shortcuts help
    const helpDiv = document.createElement('div');
    helpDiv.className = 'keyboard-help';
    helpDiv.innerHTML = `
        <div class="help-icon">⌨️</div>
        <div class="help-text">
            <strong>Keyboard Shortcuts:</strong><br>
            1/A, 2/B, 3/C, 4/D - Select answer<br>
            H - Get hint
        </div>
    `;
    helpDiv.style.position = 'fixed';
    helpDiv.style.bottom = '20px';
    helpDiv.style.left = '20px';
    helpDiv.style.background = 'rgba(0,0,0,0.8)';
    helpDiv.style.color = 'white';
    helpDiv.style.padding = '10px 15px';
    helpDiv.style.borderRadius = '10px';
    helpDiv.style.fontSize = '12px';
    helpDiv.style.zIndex = '999';
    helpDiv.style.cursor = 'pointer';
    helpDiv.style.transition = 'all 0.3s';
    
    helpDiv.addEventListener('mouseenter', () => {
        helpDiv.style.transform = 'scale(1.05)';
        const text = helpDiv.querySelector('.help-text');
        if (text) text.style.display = 'block';
    });
    
    helpDiv.addEventListener('mouseleave', () => {
        helpDiv.style.transform = 'scale(1)';
        const text = helpDiv.querySelector('.help-text');
        if (text) text.style.display = 'none';
    });
    
    const helpText = helpDiv.querySelector('.help-text');
    if (helpText) helpText.style.display = 'none';
    
    // Only add if not on mobile
    if (window.innerWidth > 768) {
        document.body.appendChild(helpDiv);
    }
}

// Authentication Validation
function setupAuthValidation() {
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    
    if (confirmPassword) {
        confirmPassword.addEventListener('input', function() {
            if (password.value !== this.value) {
                this.setCustomValidity('Passwords do not match');
            } else {
                this.setCustomValidity('');
            }
        });
    }
    
    const username = document.getElementById('username');
    if (username) {
        username.addEventListener('input', function() {
            const regex = /^[a-zA-Z0-9_]*$/;
            if (!regex.test(this.value)) {
                this.setCustomValidity('Only letters, numbers, and underscore allowed');
            } else if (this.value.length < 3) {
                this.setCustomValidity('Username must be at least 3 characters');
            } else {
                this.setCustomValidity('');
            }
        });
    }
}

// Search Autocomplete
function setupSearchAutocomplete() {
    const searchInput = document.getElementById('topic-input');
    if (!searchInput) return;
    
    // Popular topics for autocomplete
    const popularTopics = [
        'Machine Learning', 'Artificial Intelligence', 'Python Programming',
        'Web Development', 'Data Science', 'Cybersecurity', 'Cloud Computing',
        'Climate Change', 'Renewable Energy', 'Space Exploration', 'History',
        'Geography', 'Mathematics', 'Physics', 'Chemistry', 'Biology',
        'Literature', 'Art History', 'Music Theory', 'Philosophy'
    ];
    
    let currentSuggestions = [];
    
    searchInput.addEventListener('input', function() {
        const value = this.value.toLowerCase();
        if (value.length < 2) {
            hideSuggestions();
            return;
        }
        
        const matches = popularTopics.filter(topic => 
            topic.toLowerCase().includes(value)
        ).slice(0, 5);
        
        showSuggestions(matches);
    });
    
    function showSuggestions(suggestions) {
        hideSuggestions();
        
        const suggestionBox = document.createElement('div');
        suggestionBox.className = 'suggestion-box';
        suggestionBox.style.position = 'absolute';
        suggestionBox.style.background = 'white';
        suggestionBox.style.border = '1px solid #ddd';
        suggestionBox.style.borderRadius = '10px';
        suggestionBox.style.maxWidth = searchInput.offsetWidth + 'px';
        suggestionBox.style.zIndex = '1000';
        suggestionBox.style.boxShadow = '0 5px 15px rgba(0,0,0,0.2)';
        
        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.textContent = suggestion;
            item.style.padding = '10px 15px';
            item.style.cursor = 'pointer';
            item.style.transition = 'background 0.3s';
            
            item.addEventListener('mouseenter', () => {
                item.style.background = '#f0f0f0';
            });
            
            item.addEventListener('mouseleave', () => {
                item.style.background = 'white';
            });
            
            item.addEventListener('click', () => {
                searchInput.value = suggestion;
                hideSuggestions();
            });
            
            suggestionBox.appendChild(item);
        });
        
        const rect = searchInput.getBoundingClientRect();
        suggestionBox.style.top = rect.bottom + window.scrollY + 'px';
        suggestionBox.style.left = rect.left + window.scrollX + 'px';
        
        document.body.appendChild(suggestionBox);
        currentSuggestions = suggestionBox;
    }
    
    function hideSuggestions() {
        if (currentSuggestions) {
            currentSuggestions.remove();
            currentSuggestions = null;
        }
    }
    
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target)) {
            hideSuggestions();
        }
    });
}

// Scroll Animations
function setupScrollAnimations() {
    const animateElements = document.querySelectorAll('.stat-card, .quiz-card, .topic-card, .feature');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    animateElements.forEach(el => {
        el.style.opacity = '0';
        observer.observe(el);
    });
}

// Add CSS animations to document
const animationStyle = document.createElement('style');
animationStyle.textContent = `
    @keyframes floatUp {
        0% {
            opacity: 1;
            transform: translateY(0);
        }
        100% {
            opacity: 0;
            transform: translateY(-50px);
        }
    }
    
    .floating-points {
        position: fixed;
        z-index: 10000;
        font-weight: bold;
        font-size: 20px;
        pointer-events: none;
    }
    
    .pulse {
        animation: pulse 0.3s ease-in-out;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.2); }
    }
    
    .loading-spinner {
        text-align: center;
        padding: 40px;
        font-size: 24px;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .correct-header, .wrong-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
        font-size: 1.2em;
        font-weight: bold;
    }
    
    .points-earned {
        margin-left: auto;
        color: #28a745;
        font-weight: bold;
    }
    
    .bonus-badge {
        margin-top: 10px;
        padding: 5px 10px;
        background: #ffc107;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
        animation: pulse 1s infinite;
    }
    
    .correct-answer-shown {
        margin: 10px 0;
        padding: 8px;
        background: #fff3cd;
        border-radius: 5px;
    }
    
    .encouragement {
        margin-top: 10px;
        font-style: italic;
        color: #856404;
    }
    
    .quiz-ending {
        text-align: center;
        padding: 20px;
        font-size: 1.2em;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 10px;
        animation: pulse 1s infinite;
    }
    
    .suggestion-item:hover {
        background: #f0f0f0 !important;
    }
    
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
    }
    
    .badge.easy {
        background: #d4edda;
        color: #155724;
    }
    
    .badge.medium {
        background: #fff3cd;
        color: #856404;
    }
    
    .badge.hard {
        background: #f8d7da;
        color: #721c24;
    }
    
    .warning {
        background: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
    
    .error {
        background: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
`;

document.head.appendChild(animationStyle);

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        submitAnswer,
        loadQuestion,
        endQuiz,
        createConfetti
    };
}