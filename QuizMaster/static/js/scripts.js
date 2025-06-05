let questionCount = 1;

function addQuestion() {
    questionCount++;
    const questionsDiv = document.getElementById('questions');
    const questionDiv = document.createElement('div');
    questionDiv.className = 'card mb-3 question-card';
    questionDiv.innerHTML = `
        <div class="card-body">
            <div class="mb-3">
                <label class="form-label">Question ${questionCount}</label>
                <input type="text" class="form-control" name="question_${questionCount}" required>
            </div>
            ${[1, 2, 3, 4].map(i => `
                <div class="mb-3">
                    <label class="form-label">Option ${i}</label>
                    <input type="text" class="form-control" name="option_${questionCount}_${i}" required>
                </div>
            `).join('')}
            <div class="mb-3">
                <label class="form-label">Correct Option (1-4)</label>
                <input type="number" class="form-control" name="correct_option_${questionCount}" min="1" max="4" required>
            </div>
        </div>
    `;
    questionsDiv.appendChild(questionDiv);
    document.getElementById('question_count').value = questionCount;
}