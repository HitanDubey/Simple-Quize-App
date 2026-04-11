// EchoQuest Pro - Advanced Animated Character System
// Interactive running cat character that responds to quiz events

class QuizCharacter {
    constructor() {
        this.characterElement = null;
        self.faceElement = null;
        self.speechBubble = null;
        self.legs = [];
        self.isRunning = false;
        self.isJumping = false;
        self.currentMood = 'happy';
        self.speechTimeout = null;
        self.animationInterval = null;
        
        this.moods = {
            happy: { face: '😺', color: '#FFD700', message: 'You got this! 🎯' },
            excited: { face: '😸✨', color: '#FF6347', message: 'Awesome! Keep going! 🚀' },
            sad: { face: '😿', color: '#87CEEB', message: 'Don\'t worry! Try again! 💪' },
            confused: { face: '😕', color: '#9370DB', message: 'Hmm... Think carefully! 🤔' },
            celebrating: { face: '🎉😺🎉', color: '#FF1493', message: 'Perfect score! Amazing! 🏆' },
            thinking: { face: '🤔', color: '#4169E1', message: 'Take your time... ⏱️' },
            timeout: { face: '😫', color: '#DC143C', message: 'Time\'s up! Faster next time! ⏰' },
            victory: { face: '👑😺👑', color: '#FFD700', message: 'VICTORY! You\'re a champion! 🏆' }
        };
        
        this.init();
    }
    
    init() {
        // Create character element if it doesn't exist
        if (!document.querySelector('.animated-character')) {
            this.createCharacter();
        } else {
            this.characterElement = document.querySelector('.animated-character');
            this.faceElement = document.querySelector('.character-face');
            this.speechBubble = document.querySelector('.speech-bubble');
            this.legs = document.querySelectorAll('.leg');
        }
        
        this.addEventListeners();
        this.startIdleAnimation();
    }
    
    createCharacter() {
        const characterDiv = document.createElement('div');
        characterDiv.className = 'animated-character';
        characterDiv.innerHTML = `
            <div class="character-body">
                <div class="character-face">😺</div>
                <div class="character-legs">
                    <div class="leg leg-left"></div>
                    <div class="leg leg-right"></div>
                </div>
            </div>
            <div class="speech-bubble">Ready to play! 🎮</div>
        `;
        document.body.appendChild(characterDiv);
        
        this.characterElement = characterDiv;
        this.faceElement = characterDiv.querySelector('.character-face');
        this.speechBubble = characterDiv.querySelector('.speech-bubble');
        this.legs = characterDiv.querySelectorAll('.leg');
    }
    
    addEventListeners() {
        // Make character clickable
        this.characterElement.addEventListener('click', () => {
            this.interact();
        });
        
        // Character follows mouse (optional feature)
        document.addEventListener('mousemove', (e) => {
            if (Math.random() < 0.01) { // Only occasionally look at mouse
                this.lookAtMouse(e);
            }
        });
    }
    
    startIdleAnimation() {
        // Idle animation - gentle bouncing
        setInterval(() => {
            if (!this.isRunning && !this.isJumping) {
                this.characterElement.style.transform = 'translateY(0px)';
                setTimeout(() => {
                    this.characterElement.style.transform = 'translateY(-5px)';
                }, 100);
                setTimeout(() => {
                    this.characterElement.style.transform = 'translateY(0px)';
                }, 200);
            }
        }, 3000);
    }
    
    run() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.characterElement.classList.add('running');
        
        // Make legs run faster
        this.legs.forEach(leg => {
            leg.style.animation = 'runCycle 0.2s infinite';
        });
        
        // Move character slightly
        let position = 0;
        let direction = 1;
        
        this.runInterval = setInterval(() => {
            if (this.isRunning) {
                position += direction * 5;
                if (Math.abs(position) > 20) direction *= -1;
                this.characterElement.style.transform = `translateX(${position}px)`;
            }
        }, 50);
        
        // Stop running after 2 seconds
        setTimeout(() => {
            this.stopRunning();
        }, 2000);
    }
    
    stopRunning() {
        this.isRunning = false;
        this.characterElement.classList.remove('running');
        
        this.legs.forEach(leg => {
            leg.style.animation = '';
        });
        
        if (this.runInterval) {
            clearInterval(this.runInterval);
        }
        
        this.characterElement.style.transform = '';
    }
    
    jump() {
        if (this.isJumping) return;
        
        this.isJumping = true;
        this.characterElement.classList.add('jumping');
        
        let jumpHeight = 0;
        let goingUp = true;
        
        const jumpInterval = setInterval(() => {
            if (goingUp) {
                jumpHeight += 10;
                this.characterElement.style.transform = `translateY(-${jumpHeight}px)`;
                if (jumpHeight >= 50) goingUp = false;
            } else {
                jumpHeight -= 10;
                this.characterElement.style.transform = `translateY(-${jumpHeight}px)`;
                if (jumpHeight <= 0) {
                    clearInterval(jumpInterval);
                    this.characterElement.style.transform = '';
                    this.isJumping = false;
                    this.characterElement.classList.remove('jumping');
                }
            }
        }, 30);
    }
    
    setMood(mood, customMessage = null) {
        if (!this.moods[mood]) mood = 'happy';
        
        const moodData = this.moods[mood];
        this.currentMood = mood;
        
        // Update face with animation
        this.faceElement.style.transform = 'scale(1.2)';
        setTimeout(() => {
            this.faceElement.textContent = moodData.face;
            this.faceElement.style.transform = 'scale(1)';
        }, 100);
        
        // Update speech bubble
        const message = customMessage || moodData.message;
        this.speak(message);
        
        // Add mood-specific animations
        if (mood === 'celebrating' || mood === 'victory') {
            this.celebrate();
        } else if (mood === 'sad') {
            this.sadAnimation();
        }
    }
    
    speak(message, duration = 3000) {
        if (this.speechTimeout) {
            clearTimeout(this.speechTimeout);
        }
        
        this.speechBubble.textContent = message;
        this.speechBubble.style.opacity = '1';
        this.speechBubble.style.animation = 'fadeInOut 0.3s ease';
        
        this.speechTimeout = setTimeout(() => {
            this.speechBubble.style.opacity = '0';
        }, duration);
    }
    
    celebrate() {
        // Create celebration particles
        for (let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.className = 'celebration-particle';
            particle.textContent = ['✨', '⭐', '🎉', '🏆', '🌟'][Math.floor(Math.random() * 5)];
            particle.style.position = 'absolute';
            particle.style.left = this.characterElement.offsetLeft + 50 + 'px';
            particle.style.top = this.characterElement.offsetTop + 50 + 'px';
            particle.style.fontSize = '20px';
            particle.style.pointerEvents = 'none';
            particle.style.animation = `particleFloat ${1 + Math.random() * 2}s ease-out forwards`;
            document.body.appendChild(particle);
            
            setTimeout(() => particle.remove(), 2000);
        }
        
        // Jump and run
        this.jump();
        setTimeout(() => this.run(), 300);
    }
    
    sadAnimation() {
        // Slump shoulders effect
        this.characterElement.style.transform = 'rotate(5deg)';
        setTimeout(() => {
            this.characterElement.style.transform = '';
        }, 500);
    }
    
    lookAtMouse(e) {
        const rect = this.characterElement.getBoundingClientRect();
        const characterX = rect.left + rect.width / 2;
        const characterY = rect.top + rect.height / 2;
        
        const angle = Math.atan2(e.clientY - characterY, e.clientX - characterX);
        const rotation = angle * (180 / Math.PI);
        
        // Only rotate slightly
        this.faceElement.style.transform = `rotate(${Math.min(Math.max(rotation, -15), 15)}deg)`;
        setTimeout(() => {
            this.faceElement.style.transform = '';
        }, 500);
    }
    
    interact() {
        this.jump();
        this.speak('Thanks for playing! 🎮', 2000);
        this.setMood('excited');
    }
    
    // Quiz-specific reactions
    onCorrectAnswer(pointsEarned) {
        this.setMood('celebrating', `Correct! +${pointsEarned} points! 🎉`);
        this.jump();
        this.run();
        
        // Special reactions based on points
        if (pointsEarned >= 15) {
            this.setMood('excited', 'Perfect! Speed bonus! ⚡');
        }
    }
    
    onWrongAnswer(correctAnswer) {
        this.setMood('sad', `The answer was ${correctAnswer}. You'll get it next time! 💪`);
        this.sadAnimation();
    }
    
    onTimeOut() {
        this.setMood('timeout', 'Time\'s up! Be quicker next time! ⏰');
        this.sadAnimation();
    }
    
    onQuestionLoad(difficulty) {
        if (difficulty === 'hard') {
            this.setMood('thinking', 'This one is tricky! Think carefully! 🤔');
        } else if (difficulty === 'easy') {
            this.setMood('happy', 'Easy one! You know this! 😺');
        } else {
            this.setMood('happy', 'Let\'s solve this! 🎯');
        }
    }
    
    onScoreUpdate(score, total) {
        const percentage = (score / total) * 100;
        if (percentage >= 80) {
            this.setMood('excited', `Great score! ${score} points! Keep it up! 🌟`);
        } else if (percentage >= 50) {
            this.setMood('happy', `Good job! ${score} points so far! 👍`);
        }
    }
    
    onQuizComplete(score, total, percentage) {
        if (percentage >= 90) {
            this.setMood('victory', `AMAZING! ${score}/${total} points! You're a legend! 👑`);
            this.celebrate();
            for (let i = 0; i < 3; i++) {
                setTimeout(() => this.jump(), i * 500);
            }
        } else if (percentage >= 70) {
            this.setMood('celebrating', `Great work! ${score}/${total} points! 🎉`);
            this.celebrate();
        } else if (percentage >= 50) {
            this.setMood('happy', `Good effort! ${score}/${total} points! Try again to improve! 💪`);
        } else {
            this.setMood('sad', `Keep practicing! You'll do better next time! 📚`);
        }
        
        this.speak(`Final score: ${score}/${total * 10} points!`, 5000);
    }
    
    onHintUsed() {
        this.setMood('thinking', 'Using hints is smart! Learning is the goal! 💡');
        this.speak('Remember to learn from the explanation! 📖', 3000);
    }
    
    onTimerLow(secondsLeft) {
        if (secondsLeft <= 5) {
            this.setMood('thinking', `Hurry! Only ${secondsLeft} seconds left! ⏱️`);
            this.characterElement.style.animation = 'shake 0.3s infinite';
        } else {
            this.characterElement.style.animation = '';
        }
    }
    
    onNewQuestion(questionNumber, totalQuestions) {
        const progress = ((questionNumber - 1) / totalQuestions) * 100;
        
        if (progress >= 75) {
            this.setMood('happy', `Almost there! Question ${questionNumber}/${totalQuestions} 🎯`);
        } else if (progress >= 50) {
            this.setMood('happy', `Halfway! Question ${questionNumber}/${totalQuestions} 👍`);
        } else {
            this.setMood('happy', `Question ${questionNumber}/${totalQuestions}. Let's go! 🚀`);
        }
        
        // Random idle animation
        if (Math.random() < 0.3) {
            this.run();
        }
    }
    
    // Special effects
    createConfetti() {
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.backgroundColor = `hsl(${Math.random() * 360}, 100%, 50%)`;
            confetti.style.animationDelay = Math.random() * 2 + 's';
            document.body.appendChild(confetti);
            setTimeout(() => confetti.remove(), 3000);
        }
    }
    
    // Reset character for new quiz
    reset() {
        this.setMood('happy', 'New quiz! Ready to learn? 🎮');
        this.stopRunning();
        this.characterElement.style.transform = '';
    }
}

// Add particle animation CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes particleFloat {
        0% {
            opacity: 1;
            transform: translate(0, 0) rotate(0deg);
        }
        100% {
            opacity: 0;
            transform: translate(${Math.random() * 100 - 50}px, -100px) rotate(360deg);
        }
    }
    
    .celebration-particle {
        position: fixed;
        pointer-events: none;
        z-index: 10000;
        font-size: 20px;
    }
    
    .running {
        animation: shake 0.1s infinite;
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-2px); }
        75% { transform: translateX(2px); }
    }
`;
document.head.appendChild(style);

// Initialize character when DOM is ready
let quizCharacter = null;

document.addEventListener('DOMContentLoaded', () => {
    quizCharacter = new QuizCharacter();
});

// Export for use in quiz.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QuizCharacter;
}