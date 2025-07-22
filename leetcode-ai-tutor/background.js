/**
 * Background script for LeetCode AI Tutor
 * Handles extension initialization, alarm scheduling, and message handling
 */

import * as storage from './storage.js';
import * as timer from './timer.js';
import * as quiz from './quiz.js';

/**
 * Initialize the extension
 */
async function initialize() {
  console.log('Initializing LeetCode AI Tutor extension...');
  
  // Get configuration
  const config = await storage.getConfig();
  
  // Load problem list if URL is configured
  if (config.problemListUrl) {
    try {
      const problems = await storage.fetchProblemList(config.problemListUrl);
      await chrome.storage.sync.set({ problems, currentIndex: 0 });
      console.log(`Loaded ${problems.length} problems from ${config.problemListUrl}`);
    } catch (error) {
      console.error('Error loading problem list:', error);
    }
  }
  
  // Schedule alarms
  timer.scheduleAlarms(config.phaseDurations, config.quizCron);
  
  console.log('Initialization complete');
}

/**
 * Handle extension installation or update
 */
chrome.runtime.onInstalled.addListener(details => {
  if (details.reason === 'install') {
    console.log('Extension installed');
    initialize();
    
    // Open options page on install
    chrome.runtime.openOptionsPage();
  } else if (details.reason === 'update') {
    console.log('Extension updated');
    initialize();
  }
});

/**
 * Handle messages from content scripts and popup
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Received message:', message);
  
  switch (message.type) {
    case 'CONFIG_UPDATED':
      handleConfigUpdate(message.config).then(result => {
        sendResponse(result);
      });
      return true; // Keep the message channel open for async response
      
    case 'START_PHASE':
      handleStartPhase(message.phase, message.problemUrl).then(result => {
        sendResponse(result);
      });
      return true;
      
    case 'COMPLETE_PHASE':
      handleCompletePhase(message.phase, message.problemUrl).then(result => {
        sendResponse(result);
      });
      return true;
      
    case 'GET_HINT':
      handleGetHint(message.problemUrl).then(result => {
        sendResponse(result);
      });
      return true;
      
    case 'GET_SOLUTION':
      handleGetSolution(message.problemUrl).then(result => {
        sendResponse(result);
      });
      return true;
      
    case 'MARK_SOLVED':
      handleMarkSolved(message.problemUrl, message.pseudocode, message.userCode, message.aiGuidance).then(result => {
        sendResponse(result);
      });
      return true;
      
    case 'SKIP_PROBLEM':
      handleSkipProblem().then(result => {
        sendResponse(result);
      });
      return true;
      
    case 'GRADE_QUIZ':
      handleGradeQuiz(message.answers).then(result => {
        sendResponse(result);
      });
      return true;
      
    default:
      console.log('Unknown message type:', message.type);
      sendResponse({ error: 'Unknown message type' });
  }
});

/**
 * Handle alarm events
 */
chrome.alarms.onAlarm.addListener(alarm => {
  console.log('Alarm triggered:', alarm.name);
  
  if (alarm.name === 'quizReminderCheck') {
    handleQuizReminderCheck();
  } else {
    // Phase timeout alarm
    handlePhaseTimeout(alarm.name);
  }
});

/**
 * Handle configuration update
 * @param {Object} config - Updated configuration
 * @returns {Promise<Object>} - Result object
 */
async function handleConfigUpdate(config) {
  try {
    // Save configuration
    await storage.saveConfig(config);
    
    // Reload problem list if URL is configured
    if (config.problemListUrl) {
      const problems = await storage.fetchProblemList(config.problemListUrl);
      await chrome.storage.sync.set({ problems, currentIndex: 0 });
    }
    
    // Reschedule alarms
    timer.scheduleAlarms(config.phaseDurations, config.quizCron);
    
    return { success: true };
  } catch (error) {
    console.error('Error handling config update:', error);
    return { error: error.message };
  }
}

/**
 * Handle starting a phase
 * @param {string} phase - Phase name
 * @param {string} problemUrl - Problem URL
 * @returns {Promise<Object>} - Result object
 */
async function handleStartPhase(phase, problemUrl) {
  try {
    const config = await storage.getConfig();
    const durationSec = config.phaseDurations[phase];
    
    if (!durationSec) {
      throw new Error(`Invalid phase: ${phase}`);
    }
    
    const timerObj = timer.startPhaseTimer(phase, durationSec);
    const record = timer.recordPhaseStart(problemUrl, phase);
    
    return {
      success: true,
      phase,
      durationSec,
      startTime: record.startTime
    };
  } catch (error) {
    console.error('Error starting phase:', error);
    return { error: error.message };
  }
}

/**
 * Handle completing a phase
 * @param {string} phase - Phase name
 * @param {string} problemUrl - Problem URL
 * @returns {Promise<Object>} - Result object
 */
async function handleCompletePhase(phase, problemUrl) {
  try {
    // Stop the timer
    await timer.stopPhaseTimer(phase);
    
    // Complete the phase and get the record
    const record = timer.completeCurrentPhase();
    
    if (!record) {
      throw new Error('No active phase found');
    }
    
    // Log the phase timing
    const logEntry = await storage.logPhase(
      problemUrl,
      phase,
      new Date(record.startTime),
      new Date()
    );
    
    return {
      success: true,
      phase,
      duration: record.duration
    };
  } catch (error) {
    console.error('Error completing phase:', error);
    return { error: error.message };
  }
}

/**
 * Handle phase timeout
 * @param {string} phase - Phase name
 */
async function handlePhaseTimeout(phase) {
  // Get current phase
  const currentPhase = timer.getCurrentPhase();
  
  if (!currentPhase || currentPhase.phase !== phase) {
    return; // Not the current phase or no active phase
  }
  
  // Create notification
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title: 'Time\'s Up!',
    message: `Your time for the ${phase} phase has ended.`,
    buttons: [
      { title: 'Get Hint' },
      { title: 'Continue Anyway' }
    ]
  });
  
  // Complete the phase
  const record = timer.completeCurrentPhase();
  
  if (record) {
    // Log the phase timing
    await storage.logPhase(
      record.problemUrl,
      phase,
      new Date(record.startTime),
      new Date()
    );
  }
  
  // Send message to UI
  chrome.runtime.sendMessage({
    type: 'PHASE_TIMEOUT',
    phase
  });
}

/**
 * Handle getting a hint
 * @param {string} problemUrl - Problem URL
 * @returns {Promise<Object>} - Result object with hint
 */
async function handleGetHint(problemUrl) {
  try {
    // Import AI client dynamically to avoid circular dependencies
    const ai = await import('./ai_client.js');
    
    // Get pseudocode hint
    const response = await ai.getPseudocode(problemUrl);
    
    return {
      success: true,
      hint: response.text
    };
  } catch (error) {
    console.error('Error getting hint:', error);
    return { error: error.message };
  }
}

/**
 * Handle getting a solution
 * @param {string} problemUrl - Problem URL
 * @returns {Promise<Object>} - Result object with solution
 */
async function handleGetSolution(problemUrl) {
  try {
    // Import AI client dynamically to avoid circular dependencies
    const ai = await import('./ai_client.js');
    
    // Get optimal solution
    const response = await ai.getOptimalSolution(problemUrl);
    
    return {
      success: true,
      solution: response.text
    };
  } catch (error) {
    console.error('Error getting solution:', error);
    return { error: error.message };
  }
}

/**
 * Handle marking a problem as solved
 * @param {string} problemUrl - Problem URL
 * @param {string} pseudocode - User's pseudocode
 * @param {string} userCode - User's implementation
 * @param {string} aiGuidance - AI guidance provided
 * @returns {Promise<Object>} - Result object
 */
async function handleMarkSolved(problemUrl, pseudocode, userCode, aiGuidance) {
  try {
    // Import logger dynamically to avoid circular dependencies
    const logger = await import('./logger.js');
    
    // Log solution
    const result = await logger.logSolution(problemUrl, pseudocode, userCode, aiGuidance);
    
    // Move to next problem
    const { problems, currentIndex } = await storage.getState();
    const nextIndex = (currentIndex + 1) % problems.length;
    await storage.setCurrentIndex(nextIndex);
    
    return {
      success: true,
      nextProblem: problems[nextIndex],
      githubCommitted: result.committed
    };
  } catch (error) {
    console.error('Error marking problem as solved:', error);
    return { error: error.message };
  }
}

/**
 * Handle skipping a problem
 * @returns {Promise<Object>} - Result object with next problem
 */
async function handleSkipProblem() {
  try {
    const { problems, currentIndex } = await storage.getState();
    const nextIndex = (currentIndex + 1) % problems.length;
    await storage.setCurrentIndex(nextIndex);
    
    return {
      success: true,
      nextProblem: problems[nextIndex]
    };
  } catch (error) {
    console.error('Error skipping problem:', error);
    return { error: error.message };
  }
}

/**
 * Handle quiz reminder check
 */
async function handleQuizReminderCheck() {
  try {
    const shouldConduct = await quiz.shouldConductQuiz();
    
    if (shouldConduct) {
      // Create notification
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icons/icon128.png',
        title: 'Weekend Review Quiz',
        message: 'It\'s time for your weekend review quiz! Test your understanding of concepts from problems you\'ve solved.',
        buttons: [
          { title: 'Take Quiz Now' },
          { title: 'Remind Me Later' }
        ]
      });
    }
  } catch (error) {
    console.error('Error checking quiz reminder:', error);
  }
}

/**
 * Handle grading a quiz
 * @param {Object} answers - User's answers
 * @returns {Promise<Object>} - Result object with quiz results
 */
async function handleGradeQuiz(answers) {
  try {
    // Get current quiz from storage
    const quizLogs = await storage.getQuizLogs();
    const currentQuiz = quizLogs[quizLogs.length - 1]?.quiz;
    
    if (!currentQuiz) {
      throw new Error('No active quiz found');
    }
    
    // Grade quiz
    const results = quiz.gradeQuiz(currentQuiz, answers);
    
    // Save results
    await quiz.saveQuizResults(currentQuiz, results);
    
    return results;
  } catch (error) {
    console.error('Error grading quiz:', error);
    return { error: error.message };
  }
}

// Initialize on startup
chrome.runtime.onStartup.addListener(() => {
  console.log('Extension starting up');
  initialize();
});
