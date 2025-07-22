/**
 * Timer module for LeetCode AI Tutor
 * Handles phase timing and alarm scheduling
 */

/**
 * Schedule alarms based on configuration
 * @param {Object} phaseDurations - Object containing phase durations in seconds
 * @param {string} quizCron - Cron expression for quiz scheduling
 */
export function scheduleAlarms(phaseDurations, quizCron) {
  // Clear existing alarms
  chrome.alarms.clearAll();
  
  // Schedule weekend quiz reminder (daily check)
  chrome.alarms.create('quizReminderCheck', { 
    periodInMinutes: 60 * 24 // Check once per day
  });
}

/**
 * Start a phase timer
 * @param {string} phaseName - Name of the phase
 * @param {number} durationSec - Duration in seconds
 * @returns {Object} - Timer object with start time
 */
export function startPhaseTimer(phaseName, durationSec) {
  // Clear any existing alarm for this phase
  chrome.alarms.clear(phaseName);
  
  // Create new alarm for this phase
  chrome.alarms.create(phaseName, { 
    delayInMinutes: durationSec / 60 
  });
  
  // Return timer object with start time
  return {
    phase: phaseName,
    startTime: new Date(),
    durationSec: durationSec
  };
}

/**
 * Stop a phase timer
 * @param {string} phaseName - Name of the phase
 * @returns {Promise<boolean>} - True if alarm was cleared
 */
export async function stopPhaseTimer(phaseName) {
  return chrome.alarms.clear(phaseName);
}

/**
 * Get remaining time for a phase
 * @param {string} phaseName - Name of the phase
 * @returns {Promise<number>} - Remaining time in seconds
 */
export async function getRemainingTime(phaseName) {
  const alarms = await chrome.alarms.getAll();
  const alarm = alarms.find(a => a.name === phaseName);
  
  if (!alarm) {
    return 0;
  }
  
  // Calculate remaining time in seconds
  const remainingMs = alarm.scheduledTime - Date.now();
  return Math.max(0, Math.floor(remainingMs / 1000));
}

/**
 * Check if a given date matches the cron expression
 * @param {Date} date - Date to check
 * @param {string} cronExpression - Cron expression
 * @returns {boolean} - True if date matches cron expression
 */
export function matchesCron(date, cronExpression) {
  // Simple cron implementation for weekend detection
  // Format: "0 10 * * 6,0" (10:00 AM on Saturday and Sunday)
  const parts = cronExpression.split(' ');
  if (parts.length !== 5) return false;
  
  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;
  
  // Check day of week (0 = Sunday, 6 = Saturday)
  const currentDayOfWeek = date.getDay().toString();
  if (dayOfWeek !== '*' && !dayOfWeek.split(',').includes(currentDayOfWeek)) {
    return false;
  }
  
  // Check hour
  if (hour !== '*' && parseInt(hour) !== date.getHours()) {
    return false;
  }
  
  // Check minute
  if (minute !== '*' && parseInt(minute) !== date.getMinutes()) {
    return false;
  }
  
  // For simplicity, we're not fully implementing day of month and month checks
  return true;
}

/**
 * Format time in MM:SS format
 * @param {number} seconds - Time in seconds
 * @returns {string} - Formatted time string
 */
export function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Record phase start time
 * @param {string} problemUrl - URL of the problem
 * @param {string} phase - Phase name
 * @returns {Object} - Phase record object
 */
export function recordPhaseStart(problemUrl, phase) {
  const record = {
    problemUrl,
    phase,
    startTime: new Date()
  };
  
  // Store in session storage (not sync storage) to avoid quota issues
  sessionStorage.setItem('currentPhase', JSON.stringify(record));
  return record;
}

/**
 * Get current phase record
 * @returns {Object|null} - Current phase record or null
 */
export function getCurrentPhase() {
  const record = sessionStorage.getItem('currentPhase');
  return record ? JSON.parse(record) : null;
}

/**
 * Complete current phase
 * @returns {Object|null} - Completed phase record or null
 */
export function completeCurrentPhase() {
  const record = getCurrentPhase();
  if (!record) return null;
  
  record.endTime = new Date();
  record.duration = (record.endTime - new Date(record.startTime)) / 1000;
  
  // Clear current phase
  sessionStorage.removeItem('currentPhase');
  return record;
}
