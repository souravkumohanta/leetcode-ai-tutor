/**
 * Quiz module for LeetCode AI Tutor
 * Handles weekend spaced-repetition quizzes
 */

import * as storage from './storage.js';
import * as ai from './ai_client.js';

/**
 * Check if a quiz should be conducted today
 * @returns {Promise<boolean>} - True if quiz should be conducted
 */
export async function shouldConductQuiz() {
  const config = await storage.getConfig();
  const now = new Date();
  
  // Check if it's weekend (0 = Sunday, 6 = Saturday)
  const isWeekend = now.getDay() === 0 || now.getDay() === 6;
  
  if (!isWeekend) {
    return false;
  }
  
  // Check if we've already conducted a quiz today
  const quizLogs = await storage.getQuizLogs();
  const todayQuizzes = quizLogs.filter(log => {
    const logDate = new Date(log.timestamp);
    return logDate.toDateString() === now.toDateString();
  });
  
  return todayQuizzes.length === 0;
}

/**
 * Conduct a quiz
 * @returns {Promise<Object>} - Quiz object
 */
export async function conductQuiz() {
  // Get past problem URLs
  const topics = await storage.getPastProblemUrls();
  
  if (topics.length === 0) {
    return {
      error: "No past problems found. Solve some problems first!"
    };
  }
  
  // Generate quiz
  const aiResponse = await ai.generateQuiz(topics);
  
  // Parse quiz
  const quiz = ai.parseQuiz(aiResponse.text);
  
  // Save quiz
  await storage.saveQuizLog(quiz);
  
  return quiz;
}

/**
 * Render quiz in HTML
 * @param {Object} quiz - Quiz object
 * @returns {string} - HTML string
 */
export function renderQuizHTML(quiz) {
  if (quiz.error) {
    return `<div class="quiz-error">${quiz.error}</div>`;
  }
  
  let html = `
    <div class="quiz-container">
      <h2>Weekend Review Quiz</h2>
      <p>Test your understanding of concepts from problems you've solved.</p>
      <form id="quiz-form">
  `;
  
  quiz.questions.forEach((question, qIndex) => {
    html += `
      <div class="question" data-question="${qIndex}">
        <h3>Question ${qIndex + 1}</h3>
        <p>${question.problemStatement}</p>
        <div class="options">
    `;
    
    question.options.forEach((option, oIndex) => {
      const optionId = `q${qIndex}_o${oIndex}`;
      const optionLetter = option.charAt(0);
      html += `
        <div class="option">
          <input type="radio" id="${optionId}" name="q${qIndex}" value="${optionLetter}">
          <label for="${optionId}">${option}</label>
        </div>
      `;
    });
    
    html += `
        </div>
        <div class="explanation" style="display: none;">
          <h4>Explanation:</h4>
          <p>${question.explanation}</p>
        </div>
      </div>
    `;
  });
  
  html += `
      <div class="quiz-controls">
        <button type="button" id="submit-quiz">Submit Answers</button>
      </div>
      </form>
      <div id="quiz-results" style="display: none;">
        <h3>Results</h3>
        <p>You scored <span id="score">0</span> out of ${quiz.questions.length}.</p>
        <button type="button" id="show-explanations">Show Explanations</button>
      </div>
    </div>
  `;
  
  return html;
}

/**
 * Grade quiz
 * @param {Object} quiz - Quiz object
 * @param {Object} answers - User's answers
 * @returns {Object} - Results object
 */
export function gradeQuiz(quiz, answers) {
  let score = 0;
  const results = [];
  
  quiz.questions.forEach((question, index) => {
    const userAnswer = answers[`q${index}`];
    const isCorrect = userAnswer === question.correctAnswer;
    
    if (isCorrect) {
      score++;
    }
    
    results.push({
      questionIndex: index,
      userAnswer,
      correctAnswer: question.correctAnswer,
      isCorrect
    });
  });
  
  return {
    score,
    total: quiz.questions.length,
    percentage: (score / quiz.questions.length) * 100,
    results
  };
}

/**
 * Save quiz results
 * @param {Object} quiz - Quiz object
 * @param {Object} results - Results object
 * @returns {Promise<void>}
 */
export async function saveQuizResults(quiz, results) {
  const quizLogs = await storage.getQuizLogs();
  
  // Find the quiz in logs
  const quizLog = quizLogs.find(log => log.quiz.timestamp === quiz.timestamp);
  
  if (quizLog) {
    quizLog.results = results;
    await chrome.storage.sync.set({ quizLogs });
  }
}

/**
 * Get quiz JavaScript
 * @returns {string} - JavaScript for quiz functionality
 */
export function getQuizJavaScript() {
  return `
    document.addEventListener('DOMContentLoaded', function() {
      const quizForm = document.getElementById('quiz-form');
      const submitButton = document.getElementById('submit-quiz');
      const resultsDiv = document.getElementById('quiz-results');
      const scoreSpan = document.getElementById('score');
      const showExplanationsButton = document.getElementById('show-explanations');
      
      submitButton.addEventListener('click', function() {
        // Collect answers
        const answers = {};
        const questions = document.querySelectorAll('.question');
        
        questions.forEach((question, index) => {
          const selectedOption = question.querySelector('input[name="q' + index + '"]:checked');
          if (selectedOption) {
            answers['q' + index] = selectedOption.value;
          }
        });
        
        // Send message to grade quiz
        chrome.runtime.sendMessage({
          type: 'GRADE_QUIZ',
          answers: answers
        }, function(response) {
          // Display results
          scoreSpan.textContent = response.score;
          resultsDiv.style.display = 'block';
          
          // Mark correct/incorrect answers
          response.results.forEach(result => {
            const questionDiv = document.querySelector('.question[data-question="' + result.questionIndex + '"]');
            if (questionDiv) {
              questionDiv.classList.add(result.isCorrect ? 'correct' : 'incorrect');
              
              // Highlight correct answer
              const correctOption = questionDiv.querySelector('input[value="' + result.correctAnswer + '"]');
              if (correctOption) {
                correctOption.parentElement.classList.add('correct-answer');
              }
              
              // Highlight user's answer if incorrect
              if (!result.isCorrect && result.userAnswer) {
                const userOption = questionDiv.querySelector('input[value="' + result.userAnswer + '"]');
                if (userOption) {
                  userOption.parentElement.classList.add('incorrect-answer');
                }
              }
            }
          });
        });
      });
      
      showExplanationsButton.addEventListener('click', function() {
        const explanations = document.querySelectorAll('.explanation');
        explanations.forEach(exp => {
          exp.style.display = 'block';
        });
      });
    });
  `;
}

/**
 * Get quiz CSS
 * @returns {string} - CSS for quiz styling
 */
export function getQuizCSS() {
  return `
    .quiz-container {
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
      font-family: Arial, sans-serif;
    }
    
    .question {
      margin-bottom: 30px;
      padding: 15px;
      border: 1px solid #ddd;
      border-radius: 5px;
    }
    
    .question.correct {
      border-left: 5px solid #4CAF50;
    }
    
    .question.incorrect {
      border-left: 5px solid #F44336;
    }
    
    .options {
      margin-top: 10px;
    }
    
    .option {
      margin-bottom: 10px;
    }
    
    .correct-answer {
      color: #4CAF50;
      font-weight: bold;
    }
    
    .incorrect-answer {
      color: #F44336;
      text-decoration: line-through;
    }
    
    .explanation {
      margin-top: 15px;
      padding: 10px;
      background-color: #f9f9f9;
      border-left: 3px solid #2196F3;
    }
    
    .quiz-controls {
      margin-top: 20px;
      text-align: center;
    }
    
    button {
      padding: 10px 20px;
      background-color: #2196F3;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 16px;
    }
    
    button:hover {
      background-color: #0b7dda;
    }
    
    #quiz-results {
      margin-top: 20px;
      padding: 15px;
      background-color: #f9f9f9;
      border-radius: 5px;
      text-align: center;
    }
    
    #score {
      font-weight: bold;
      font-size: 18px;
    }
  `;
}
