/**
 * Options page script for LeetCode AI Tutor
 * Handles loading and saving configuration
 */

// DOM elements
const problemListUrlInput = document.getElementById('problemListUrl');
const aiEndpointInput = document.getElementById('aiEndpoint');
const aiModelInput = document.getElementById('aiModel');
const apiKeyInput = document.getElementById('apiKey');
const dUnderstandInput = document.getElementById('dUnderstand');
const dPseudocodeInput = document.getElementById('dPseudocode');
const dImplementInput = document.getElementById('dImplement');
const dOptimizeInput = document.getElementById('dOptimize');
const ghRepoInput = document.getElementById('ghRepo');
const ghTokenInput = document.getElementById('ghToken');
const quizCronInput = document.getElementById('quizCron');
const saveButton = document.getElementById('saveButton');
const statusDiv = document.getElementById('status');

/**
 * Load configuration from storage
 */
async function loadConfig() {
  try {
    const result = await chrome.storage.sync.get('config');
    const config = result.config || getDefaultConfig();
    
    // Populate form fields
    problemListUrlInput.value = config.problemListUrl || '';
    aiEndpointInput.value = config.aiEndpoint || '';
    aiModelInput.value = config.aiModel || '';
    apiKeyInput.value = config.apiKey || '';
    dUnderstandInput.value = config.phaseDurations?.understand || 300;
    dPseudocodeInput.value = config.phaseDurations?.pseudocode || 600;
    dImplementInput.value = config.phaseDurations?.implement || 900;
    dOptimizeInput.value = config.phaseDurations?.optimize || 600;
    ghRepoInput.value = config.github?.repo || '';
    ghTokenInput.value = config.github?.token || '';
    quizCronInput.value = config.quizCron || '0 10 * * 6,0';
    
    // Update duration labels
    updateDurationLabels();
  } catch (error) {
    console.error('Error loading configuration:', error);
    showStatus('Error loading configuration: ' + error.message, 'error');
  }
}

/**
 * Save configuration to storage
 */
async function saveConfig() {
  try {
    const config = {
      problemListUrl: problemListUrlInput.value.trim(),
      aiEndpoint: aiEndpointInput.value.trim(),
      aiModel: aiModelInput.value.trim(),
      apiKey: apiKeyInput.value.trim(),
      phaseDurations: {
        understand: parseInt(dUnderstandInput.value) || 300,
        pseudocode: parseInt(dPseudocodeInput.value) || 600,
        implement: parseInt(dImplementInput.value) || 900,
        optimize: parseInt(dOptimizeInput.value) || 600
      },
      github: {
        repo: ghRepoInput.value.trim(),
        token: ghTokenInput.value.trim()
      },
      quizCron: quizCronInput.value.trim() || '0 10 * * 6,0'
    };
    
    // Validate configuration
    if (config.problemListUrl && !isValidUrl(config.problemListUrl)) {
      throw new Error('Invalid problem list URL');
    }
    
    if (config.aiEndpoint && !isValidUrl(config.aiEndpoint)) {
      throw new Error('Invalid AI endpoint URL');
    }
    
    // Save to storage
    await chrome.storage.sync.set({ config });
    
    // Notify background script
    chrome.runtime.sendMessage({
      type: 'CONFIG_UPDATED',
      config
    });
    
    showStatus('Configuration saved successfully!', 'success');
  } catch (error) {
    console.error('Error saving configuration:', error);
    showStatus('Error saving configuration: ' + error.message, 'error');
  }
}

/**
 * Get default configuration
 * @returns {Object} - Default configuration object
 */
function getDefaultConfig() {
  return {
    problemListUrl: '',
    aiEndpoint: 'http://localhost:11434',
    aiModel: 'llama2',
    apiKey: '',
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
 * Update duration labels
 */
function updateDurationLabels() {
  const durationInputs = [
    { input: dUnderstandInput, label: document.querySelector('label[for="dUnderstand"] + input + span') },
    { input: dPseudocodeInput, label: document.querySelector('label[for="dPseudocode"] + input + span') },
    { input: dImplementInput, label: document.querySelector('label[for="dImplement"] + input + span') },
    { input: dOptimizeInput, label: document.querySelector('label[for="dOptimize"] + input + span') }
  ];
  
  for (const { input, label } of durationInputs) {
    const seconds = parseInt(input.value) || 0;
    const minutes = Math.floor(seconds / 60);
    label.textContent = `(${minutes} minute${minutes !== 1 ? 's' : ''})`;
  }
}

/**
 * Show status message
 * @param {string} message - Status message
 * @param {string} type - Status type ('success' or 'error')
 */
function showStatus(message, type) {
  statusDiv.textContent = message;
  statusDiv.className = `status ${type}`;
  statusDiv.classList.remove('hidden');
  
  // Hide status after 3 seconds
  setTimeout(() => {
    statusDiv.classList.add('hidden');
  }, 3000);
}

/**
 * Check if a string is a valid URL
 * @param {string} url - URL to check
 * @returns {boolean} - True if URL is valid
 */
function isValidUrl(url) {
  try {
    new URL(url);
    return true;
  } catch (error) {
    return false;
  }
}

// Event listeners
saveButton.addEventListener('click', saveConfig);

// Update duration labels when inputs change
dUnderstandInput.addEventListener('input', updateDurationLabels);
dPseudocodeInput.addEventListener('input', updateDurationLabels);
dImplementInput.addEventListener('input', updateDurationLabels);
dOptimizeInput.addEventListener('input', updateDurationLabels);

// Load configuration when page loads
document.addEventListener('DOMContentLoaded', loadConfig);
