/**
 * New Tab page script for LeetCode AI Tutor
 * Handles problem display, phase transitions, and timer management
 */

// DOM elements
const problemTitleElement = document.getElementById('problemTitle');
const problemLinkElement = document.getElementById('problemLink');
const problemDifficultyElement = document.getElementById('problemDifficulty');
const currentPhaseElement = document.getElementById('currentPhase');
const timerElement = document.getElementById('timer');
const phaseElements = document.querySelectorAll('.phase');
const nextPhaseBtn = document.getElementById('nextPhaseBtn');
const hintBtn = document.getElementById('hintBtn');
const solutionBtn = document.getElementById('solutionBtn');
const solvedBtn = document.getElementById('solvedBtn');
const skipBtn = document.getElementById('skipBtn');
const codeEditor = document.getElementById('codeEditor');
const codeTitleElement = document.getElementById('codeTitle');
const aiResponseElement = document.getElementById('aiResponse');
const aiResponseContentElement = document.getElementById('aiResponseContent');
const loadingElement = document.getElementById('loading');
const progressListElement = document.getElementById('progressList');

// State variables
let currentProblem = null;
let currentPhase = 'understand';
let completedPhases = [];
let timerInterval = null;
let remainingTime = 0;
let phaseStartTime = null;
let userSolutions = {
  pseudocode: '',
  implementation: '',
  optimization: ''
};
let aiGuidance = '';

/**
 * Initialize the page
 */
async function initialize() {
  try {
    // Load current problem
    await loadCurrentProblem();
    
    // Start the first phase
    await startPhase('understand');
    
    // Load recent progress
    await loadRecentProgress();
    
    // Set up event listeners
    setupEventListeners();
  } catch (error) {
    console.error('Error initializing page:', error);
    showError('Failed to initialize. Please check your configuration and try again.');
  }
}

/**
 * Load the current problem from storage
 */
async function loadCurrentProblem() {
  showLoading(true);
  
  try {
    // Import storage module dynamically
    const storage = await import('./storage.js');
    
    // Get current problem
    const { problems, currentIndex } = await storage.getState();
    
    if (!problems || problems.length === 0) {
      throw new Error('No problems found. Please configure a problem list URL in the options page.');
    }
    
    currentProblem = problems[currentIndex];
    
    // Update UI
    updateProblemDisplay(currentProblem);
  } catch (error) {
    console.error('Error loading problem:', error);
    showError('Failed to load problem. Please check your configuration and try again.');
  } finally {
    showLoading(false);
  }
}

/**
 * Update the problem display
 * @param {Object} problem - Problem object
 */
function updateProblemDisplay(problem) {
  problemTitleElement.textContent = problem.title || 'Unknown Problem';
  problemLinkElement.href = problem.url || '#';
  
  // Set difficulty class
  problemDifficultyElement.textContent = problem.difficulty || 'Medium';
  problemDifficultyElement.className = 'problem-difficulty';
  
  if (problem.difficulty) {
    const lowerDifficulty = problem.difficulty.toLowerCase();
    if (lowerDifficulty === 'easy') {
      problemDifficultyElement.classList.add('difficulty-easy');
    } else if (lowerDifficulty === 'medium') {
      problemDifficultyElement.classList.add('difficulty-medium');
    } else if (lowerDifficulty === 'hard') {
      problemDifficultyElement.classList.add('difficulty-hard');
    }
  }
}

/**
 * Start a phase
 * @param {string} phase - Phase name
 */
async function startPhase(phase) {
  showLoading(true);
  
  try {
    // Import timer module dynamically
    const timer = await import('./timer.js');
    
    // Update current phase
    currentPhase = phase;
    
    // Update UI
    updatePhaseDisplay(phase);
    
    // Set code editor title and placeholder based on phase
    updateCodeEditorForPhase(phase);
    
    // Send message to background script to start phase
    const response = await chrome.runtime.sendMessage({
      type: 'START_PHASE',
      phase,
      problemUrl: currentProblem.url
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    // Start timer
    phaseStartTime = new Date();
    remainingTime = response.durationSec;
    startTimer(remainingTime);
  } catch (error) {
    console.error('Error starting phase:', error);
    showError(`Failed to start ${phase} phase: ${error.message}`);
  } finally {
    showLoading(false);
  }
}

/**
 * Complete the current phase
 */
async function completePhase() {
  showLoading(true);
  
  try {
    // Stop timer
    stopTimer();
    
    // Save user's solution for this phase
    saveCurrentSolution();
    
    // Send message to background script to complete phase
    const response = await chrome.runtime.sendMessage({
      type: 'COMPLETE_PHASE',
      phase: currentPhase,
      problemUrl: currentProblem.url
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    // Mark phase as completed
    completedPhases.push(currentPhase);
    
    // Update UI
    updateCompletedPhases();
    
    // Move to next phase
    const nextPhase = getNextPhase(currentPhase);
    if (nextPhase) {
      await startPhase(nextPhase);
    } else {
      // All phases completed
      showMessage('All phases completed! You can now mark the problem as solved.');
    }
  } catch (error) {
    console.error('Error completing phase:', error);
    showError(`Failed to complete ${currentPhase} phase: ${error.message}`);
  } finally {
    showLoading(false);
  }
}

/**
 * Get the next phase
 * @param {string} currentPhase - Current phase
 * @returns {string|null} - Next phase or null if all phases are completed
 */
function getNextPhase(currentPhase) {
  const phases = ['understand', 'pseudocode', 'implement', 'optimize'];
  const currentIndex = phases.indexOf(currentPhase);
  
  if (currentIndex < phases.length - 1) {
    return phases[currentIndex + 1];
  }
  
  return null;
}

/**
 * Update the phase display
 * @param {string} phase - Phase name
 */
function updatePhaseDisplay(phase) {
  // Update phase title
  currentPhaseElement.textContent = phase.charAt(0).toUpperCase() + phase.slice(1);
  
  // Update phase indicators
  phaseElements.forEach(element => {
    const elementPhase = element.dataset.phase;
    element.classList.remove('active');
    
    if (elementPhase === phase) {
      element.classList.add('active');
    }
  });
}

/**
 * Update completed phases in UI
 */
function updateCompletedPhases() {
  phaseElements.forEach(element => {
    const elementPhase = element.dataset.phase;
    element.classList.remove('completed');
    
    if (completedPhases.includes(elementPhase)) {
      element.classList.add('completed');
    }
  });
}

/**
 * Update code editor for the current phase
 * @param {string} phase - Phase name
 */
function updateCodeEditorForPhase(phase) {
  switch (phase) {
    case 'understand':
      codeTitleElement.textContent = 'Understanding Notes';
      codeEditor.placeholder = 'Take notes to understand the problem...';
      codeEditor.value = userSolutions.understanding || '';
      break;
      
    case 'pseudocode':
      codeTitleElement.textContent = 'Pseudocode';
      codeEditor.placeholder = 'Write pseudocode for your solution...';
      codeEditor.value = userSolutions.pseudocode || '';
      break;
      
    case 'implement':
      codeTitleElement.textContent = 'Implementation';
      codeEditor.placeholder = 'Implement your solution...';
      codeEditor.value = userSolutions.implementation || '';
      break;
      
    case 'optimize':
      codeTitleElement.textContent = 'Optimized Solution';
      codeEditor.placeholder = 'Optimize your solution...';
      codeEditor.value = userSolutions.optimization || '';
      break;
  }
}

/**
 * Save the current solution
 */
function saveCurrentSolution() {
  const solution = codeEditor.value;
  
  switch (currentPhase) {
    case 'understand':
      userSolutions.understanding = solution;
      break;
      
    case 'pseudocode':
      userSolutions.pseudocode = solution;
      break;
      
    case 'implement':
      userSolutions.implementation = solution;
      break;
      
    case 'optimize':
      userSolutions.optimization = solution;
      break;
  }
}

/**
 * Start the timer
 * @param {number} seconds - Duration in seconds
 */
function startTimer(seconds) {
  // Clear any existing timer
  stopTimer();
  
  // Set initial time
  remainingTime = seconds;
  updateTimerDisplay();
  
  // Start interval
  timerInterval = setInterval(() => {
    remainingTime--;
    
    if (remainingTime <= 0) {
      // Time's up
      stopTimer();
      handlePhaseTimeout();
    } else {
      updateTimerDisplay();
    }
  }, 1000);
}

/**
 * Stop the timer
 */
function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

/**
 * Update the timer display
 */
function updateTimerDisplay() {
  const minutes = Math.floor(remainingTime / 60);
  const seconds = remainingTime % 60;
  
  timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Handle phase timeout
 */
function handlePhaseTimeout() {
  showMessage(`Time's up for the ${currentPhase} phase! You can continue or move to the next phase.`);
}

/**
 * Get a hint for the current problem
 */
async function getHint() {
  showLoading(true);
  
  try {
    // Send message to background script to get hint
    const response = await chrome.runtime.sendMessage({
      type: 'GET_HINT',
      problemUrl: currentProblem.url
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    // Show AI response
    showAIResponse('Hint', response.hint);
    
    // Save AI guidance
    aiGuidance += `\n\n--- Hint ---\n${response.hint}`;
  } catch (error) {
    console.error('Error getting hint:', error);
    showError(`Failed to get hint: ${error.message}`);
  } finally {
    showLoading(false);
  }
}

/**
 * Get the optimal solution for the current problem
 */
async function getSolution() {
  showLoading(true);
  
  try {
    // Send message to background script to get solution
    const response = await chrome.runtime.sendMessage({
      type: 'GET_SOLUTION',
      problemUrl: currentProblem.url
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    // Show AI response
    showAIResponse('Optimal Solution', response.solution);
    
    // Save AI guidance
    aiGuidance += `\n\n--- Optimal Solution ---\n${response.solution}`;
  } catch (error) {
    console.error('Error getting solution:', error);
    showError(`Failed to get solution: ${error.message}`);
  } finally {
    showLoading(false);
  }
}

/**
 * Mark the current problem as solved
 */
async function markSolved() {
  showLoading(true);
  
  try {
    // Save current solution
    saveCurrentSolution();
    
    // Send message to background script to mark problem as solved
    const response = await chrome.runtime.sendMessage({
      type: 'MARK_SOLVED',
      problemUrl: currentProblem.url,
      pseudocode: userSolutions.pseudocode,
      userCode: userSolutions.implementation || userSolutions.optimization,
      aiGuidance
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    // Show success message
    showMessage('Problem marked as solved! Moving to next problem...');
    
    // Reset state
    resetState();
    
    // Load next problem
    currentProblem = response.nextProblem;
    updateProblemDisplay(currentProblem);
    
    // Start first phase
    await startPhase('understand');
  } catch (error) {
    console.error('Error marking problem as solved:', error);
    showError(`Failed to mark problem as solved: ${error.message}`);
  } finally {
    showLoading(false);
  }
}

/**
 * Skip the current problem
 */
async function skipProblem() {
  showLoading(true);
  
  try {
    // Send message to background script to skip problem
    const response = await chrome.runtime.sendMessage({
      type: 'SKIP_PROBLEM'
    });
    
    if (response.error) {
      throw new Error(response.error);
    }
    
    // Show message
    showMessage('Problem skipped. Moving to next problem...');
    
    // Reset state
    resetState();
    
    // Load next problem
    currentProblem = response.nextProblem;
    updateProblemDisplay(currentProblem);
    
    // Start first phase
    await startPhase('understand');
  } catch (error) {
    console.error('Error skipping problem:', error);
    showError(`Failed to skip problem: ${error.message}`);
  } finally {
    showLoading(false);
  }
}

/**
 * Reset the state
 */
function resetState() {
  // Stop timer
  stopTimer();
  
  // Reset phases
  currentPhase = 'understand';
  completedPhases = [];
  
  // Reset solutions
  userSolutions = {
    understanding: '',
    pseudocode: '',
    implementation: '',
    optimization: ''
  };
  
  // Reset AI guidance
  aiGuidance = '';
  
  // Hide AI response
  aiResponseElement.style.display = 'none';
}

/**
 * Show AI response
 * @param {string} title - Response title
 * @param {string} content - Response content
 */
function showAIResponse(title, content) {
  aiResponseElement.style.display = 'block';
  aiResponseElement.querySelector('h3').textContent = title;
  
  // Format content with markdown-like syntax
  const formattedContent = formatAIResponse(content);
  aiResponseContentElement.innerHTML = formattedContent;
}

/**
 * Format AI response with markdown-like syntax
 * @param {string} content - Raw response content
 * @returns {string} - Formatted HTML
 */
function formatAIResponse(content) {
  // Replace code blocks
  let formatted = content.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
  
  // Replace line breaks
  formatted = formatted.replace(/\n/g, '<br>');
  
  return formatted;
}

/**
 * Load recent progress
 */
async function loadRecentProgress() {
  try {
    // Import storage module dynamically
    const storage = await import('./storage.js');
    
    // Get solutions
    const solutions = await storage.getSolutions();
    
    // Sort by timestamp (newest first)
    solutions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    // Take the 5 most recent
    const recentSolutions = solutions.slice(0, 5);
    
    // Update UI
    updateProgressList(recentSolutions);
  } catch (error) {
    console.error('Error loading recent progress:', error);
  }
}

/**
 * Update progress list
 * @param {Array} solutions - Array of solution objects
 */
function updateProgressList(solutions) {
  // Clear list
  progressListElement.innerHTML = '';
  
  if (solutions.length === 0) {
    const emptyItem = document.createElement('li');
    emptyItem.className = 'progress-item';
    emptyItem.textContent = 'No solved problems yet.';
    progressListElement.appendChild(emptyItem);
    return;
  }
  
  // Add items
  for (const solution of solutions) {
    const item = document.createElement('li');
    item.className = 'progress-item';
    
    // Extract problem name from URL
    const problemName = extractProblemName(solution.problemUrl);
    
    // Format timestamp
    const timestamp = new Date(solution.timestamp).toLocaleString();
    
    item.innerHTML = `
      <div class="problem-name">${problemName}</div>
      <div class="timestamp">Solved on: ${timestamp}</div>
    `;
    
    progressListElement.appendChild(item);
  }
}

/**
 * Extract problem name from URL
 * @param {string} url - Problem URL
 * @returns {string} - Problem name
 */
function extractProblemName(url) {
  try {
    // Extract problem name from URL
    // Example: https://leetcode.com/problems/two-sum/ -> Two Sum
    const match = url.match(/problems\/([^\/]+)/);
    if (match && match[1]) {
      // Convert kebab-case to title case
      return match[1].split('-').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ');
    }
    
    // Fallback: use the last part of the URL
    const parts = url.split('/').filter(Boolean);
    return parts[parts.length - 1] || 'Unknown Problem';
  } catch (error) {
    console.error('Error extracting problem name:', error);
    return 'Unknown Problem';
  }
}

/**
 * Show loading indicator
 * @param {boolean} show - Whether to show or hide
 */
function showLoading(show) {
  loadingElement.style.display = show ? 'block' : 'none';
}

/**
 * Show error message
 * @param {string} message - Error message
 */
function showError(message) {
  alert(`Error: ${message}`);
}

/**
 * Show message
 * @param {string} message - Message
 */
function showMessage(message) {
  alert(message);
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
  // Next phase button
  nextPhaseBtn.addEventListener('click', () => {
    completePhase();
  });
  
  // Hint button
  hintBtn.addEventListener('click', () => {
    getHint();
  });
  
  // Solution button
  solutionBtn.addEventListener('click', () => {
    getSolution();
  });
  
  // Solved button
  solvedBtn.addEventListener('click', () => {
    markSolved();
  });
  
  // Skip button
  skipBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to skip this problem?')) {
      skipProblem();
    }
  });
  
  // Phase indicator clicks
  phaseElements.forEach(element => {
    element.addEventListener('click', () => {
      const phase = element.dataset.phase;
      
      // Only allow clicking on completed phases or the current phase
      if (phase === currentPhase || completedPhases.includes(phase)) {
        saveCurrentSolution();
        updateCodeEditorForPhase(phase);
      }
    });
  });
  
  // Listen for messages from background script
  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === 'PHASE_TIMEOUT') {
      handlePhaseTimeout();
    }
  });
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', initialize);
