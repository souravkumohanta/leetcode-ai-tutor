/**
 * Storage module for LeetCode AI Tutor
 * Provides wrapper functions for Chrome's storage API
 */

/**
 * Fetch problem list from the provided URL
 * @param {string} url - URL to fetch problem list from
 * @returns {Promise<Array>} - Array of problem objects
 */
export async function fetchProblemList(url) {
  try {
    const response = await fetch(url);
    const data = await response.json();
    return data.problems || [];
  } catch (error) {
    console.error('Error fetching problem list:', error);
    return [];
  }
}

/**
 * Get current state (problems and current index)
 * @returns {Promise<Object>} - Object containing problems array and current index
 */
export async function getState() {
  const result = await chrome.storage.sync.get(['problems', 'currentIndex']);
  return {
    problems: result.problems || [],
    currentIndex: result.currentIndex || 0
  };
}

/**
 * Set current problem index
 * @param {number} index - New problem index
 * @returns {Promise<void>}
 */
export async function setCurrentIndex(index) {
  await chrome.storage.sync.set({ currentIndex: index });
}

/**
 * Get user configuration
 * @returns {Promise<Object>} - User configuration object
 */
export async function getConfig() {
  const result = await chrome.storage.sync.get('config');
  return result.config || getDefaultConfig();
}

/**
 * Save user configuration
 * @param {Object} config - User configuration object
 * @returns {Promise<void>}
 */
export async function saveConfig(config) {
  await chrome.storage.sync.set({ config });
}

/**
 * Get default configuration
 * @returns {Object} - Default configuration object
 */
function getDefaultConfig() {
  return {
    problemListUrl: '',
    aiEndpoint: 'http://127.0.0.1:1234',
    aiModel: 'skywork_skywork-swe-32b',
    phaseDurations: {
      understand: 300, // 5 minutes
      pseudocode: 600, // 10 minutes
      implement: 900, // 15 minutes
      optimize: 600 // 10 minutes
    },
    github: {
      repo: '',
      token: ''
    },
    quizCron: '0 10 * * 6,0' // 10:00 AM on weekends
  };
}

/**
 * Log phase timing
 * @param {string} problemUrl - URL of the problem
 * @param {string} phase - Phase name
 * @param {Date} start - Start time
 * @param {Date} end - End time
 * @returns {Promise<void>}
 */
export async function logPhase(problemUrl, phase, start, end) {
  const logs = await getLogs();
  logs.push({
    timestamp: new Date().toISOString(),
    problemUrl,
    phase,
    duration: (end - start) / 1000, // in seconds
    start: start.toISOString(),
    end: end.toISOString()
  });
  await chrome.storage.sync.set({ logs });
}

/**
 * Get all logs
 * @returns {Promise<Array>} - Array of log objects
 */
export async function getLogs() {
  const result = await chrome.storage.sync.get('logs');
  return result.logs || [];
}

/**
 * Save solution log
 * @param {string} problemUrl - URL of the problem
 * @param {string} pseudocode - User's pseudocode
 * @param {string} userCode - User's implementation
 * @param {string} aiGuidance - AI guidance provided
 * @returns {Promise<void>}
 */
export async function logSolution(problemUrl, pseudocode, userCode, aiGuidance) {
  const solutions = await getSolutions();
  solutions.push({
    timestamp: new Date().toISOString(),
    problemUrl,
    pseudocode,
    userCode,
    aiGuidance
  });
  await chrome.storage.sync.set({ solutions });
}

/**
 * Get all solution logs
 * @returns {Promise<Array>} - Array of solution objects
 */
export async function getSolutions() {
  const result = await chrome.storage.sync.get('solutions');
  return result.solutions || [];
}

/**
 * Save quiz log
 * @param {Object} quiz - Quiz object
 * @returns {Promise<void>}
 */
export async function saveQuizLog(quiz) {
  const quizLogs = await getQuizLogs();
  quizLogs.push({
    timestamp: new Date().toISOString(),
    quiz
  });
  await chrome.storage.sync.set({ quizLogs });
}

/**
 * Get all quiz logs
 * @returns {Promise<Array>} - Array of quiz log objects
 */
export async function getQuizLogs() {
  const result = await chrome.storage.sync.get('quizLogs');
  return result.quizLogs || [];
}

/**
 * Get past problem URLs for quiz generation
 * @returns {Promise<Array>} - Array of problem URLs
 */
export async function getPastProblemUrls() {
  const solutions = await getSolutions();
  return solutions.map(solution => solution.problemUrl);
}
