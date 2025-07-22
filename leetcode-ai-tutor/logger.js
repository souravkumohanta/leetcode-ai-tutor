/**
 * Logger module for LeetCode AI Tutor
 * Handles logging progress and committing to GitHub
 */

import * as storage from './storage.js';

/**
 * Log phase timing
 * @param {string} problemUrl - URL of the problem
 * @param {string} phaseName - Name of the phase
 * @param {Date} start - Start time
 * @param {Date} end - End time
 * @returns {Promise<Object>} - Log entry
 */
export async function logPhaseTiming(problemUrl, phaseName, start, end) {
  const duration = (end - start) / 1000; // in seconds
  
  const logEntry = {
    timestamp: new Date().toISOString(),
    problemUrl,
    phase: phaseName,
    duration,
    start: start.toISOString(),
    end: end.toISOString()
  };
  
  // Save to storage
  const logs = await storage.getLogs();
  logs.push(logEntry);
  await chrome.storage.sync.set({ logs });
  
  return logEntry;
}

/**
 * Log solution
 * @param {string} problemUrl - URL of the problem
 * @param {string} pseudocode - User's pseudocode
 * @param {string} userCode - User's implementation
 * @param {string} aiGuidance - AI guidance provided
 * @returns {Promise<Object>} - Solution log entry
 */
export async function logSolution(problemUrl, pseudocode, userCode, aiGuidance) {
  const solutionEntry = {
    timestamp: new Date().toISOString(),
    problemUrl,
    pseudocode,
    userCode,
    aiGuidance
  };
  
  // Save to storage
  await storage.logSolution(problemUrl, pseudocode, userCode, aiGuidance);
  
  // Create markdown content for GitHub
  const mdContent = createSolutionMarkdown(solutionEntry);
  
  // Extract problem name from URL for filename
  const problemName = extractProblemName(problemUrl);
  const filename = `${new Date().toISOString().split('T')[0]}-${problemName}.md`;
  
  // Commit to GitHub
  try {
    await commitToGitHub(mdContent, filename);
    return { ...solutionEntry, committed: true };
  } catch (error) {
    console.error('Error committing to GitHub:', error);
    return { ...solutionEntry, committed: false, error: error.message };
  }
}

/**
 * Create markdown content for solution
 * @param {Object} solution - Solution object
 * @returns {string} - Markdown content
 */
function createSolutionMarkdown(solution) {
  const problemName = extractProblemName(solution.problemUrl);
  
  return `# ${problemName} - LeetCode Solution
  
## Problem Link
[${problemName}](${solution.problemUrl})

## Date
${new Date(solution.timestamp).toLocaleDateString()}

## Pseudocode
\`\`\`
${solution.pseudocode}
\`\`\`

## Implementation
\`\`\`
${solution.userCode}
\`\`\`

## AI Guidance
${solution.aiGuidance}

## Notes
- Solved on: ${new Date(solution.timestamp).toLocaleString()}
`;
}

/**
 * Extract problem name from URL
 * @param {string} url - Problem URL
 * @returns {string} - Problem name
 */
function extractProblemName(url) {
  try {
    // Extract problem name from URL
    // Example: https://leetcode.com/problems/two-sum/ -> two-sum
    const match = url.match(/problems\/([^\/]+)/);
    if (match && match[1]) {
      return match[1];
    }
    
    // Fallback: use the last part of the URL
    const parts = url.split('/').filter(Boolean);
    return parts[parts.length - 1] || 'unknown-problem';
  } catch (error) {
    console.error('Error extracting problem name:', error);
    return 'unknown-problem';
  }
}

/**
 * Commit to GitHub
 * @param {string} mdContent - Markdown content
 * @param {string} filename - Filename
 * @returns {Promise<Object>} - GitHub API response
 */
export async function commitToGitHub(mdContent, filename) {
  const config = await storage.getConfig();
  
  if (!config.github.repo || !config.github.token) {
    throw new Error('GitHub repository or token not configured');
  }
  
  const apiUrl = `https://api.github.com/repos/${config.github.repo}/contents/logs/${filename}`;
  
  // Check if file exists
  let sha = '';
  try {
    const response = await fetch(apiUrl, {
      headers: {
        'Authorization': `token ${config.github.token}`,
        'Accept': 'application/vnd.github.v3+json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      sha = data.sha;
    }
  } catch (error) {
    // File doesn't exist, which is fine
    console.log('File does not exist yet, will create it');
  }
  
  // Create or update file
  const payload = {
    message: `Log solution for ${filename.replace('.md', '')}`,
    content: btoa(mdContent), // Base64 encode content
    ...(sha ? { sha } : {}) // Include SHA if file exists
  };
  
  const response = await fetch(apiUrl, {
    method: 'PUT',
    headers: {
      'Authorization': `token ${config.github.token}`,
      'Content-Type': 'application/json',
      'Accept': 'application/vnd.github.v3+json'
    },
    body: JSON.stringify(payload)
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(`GitHub API error: ${errorData.message}`);
  }
  
  return response.json();
}

/**
 * Generate weekly report
 * @returns {Promise<string>} - Markdown report
 */
export async function generateWeeklyReport() {
  const logs = await storage.getLogs();
  const solutions = await storage.getSolutions();
  
  // Group logs by problem
  const problemMap = {};
  
  // Process phase logs
  for (const log of logs) {
    if (!problemMap[log.problemUrl]) {
      problemMap[log.problemUrl] = {
        url: log.problemUrl,
        name: extractProblemName(log.problemUrl),
        phases: {},
        solution: null
      };
    }
    
    if (!problemMap[log.problemUrl].phases[log.phase]) {
      problemMap[log.problemUrl].phases[log.phase] = [];
    }
    
    problemMap[log.problemUrl].phases[log.phase].push(log);
  }
  
  // Process solutions
  for (const solution of solutions) {
    if (!problemMap[solution.problemUrl]) {
      problemMap[solution.problemUrl] = {
        url: solution.problemUrl,
        name: extractProblemName(solution.problemUrl),
        phases: {},
        solution: solution
      };
    } else {
      problemMap[solution.problemUrl].solution = solution;
    }
  }
  
  // Generate markdown report
  let markdown = `# Weekly LeetCode Progress Report\n\n`;
  markdown += `Generated: ${new Date().toLocaleDateString()}\n\n`;
  
  markdown += `## Problems Solved\n\n`;
  
  const problems = Object.values(problemMap);
  for (const problem of problems) {
    markdown += `### ${problem.name}\n`;
    markdown += `- URL: [${problem.name}](${problem.url})\n`;
    
    // Add phase timing information
    if (Object.keys(problem.phases).length > 0) {
      markdown += `- Phases:\n`;
      for (const [phase, logs] of Object.entries(problem.phases)) {
        const totalDuration = logs.reduce((sum, log) => sum + log.duration, 0);
        markdown += `  - ${phase}: ${formatDuration(totalDuration)}\n`;
      }
    }
    
    // Add solution information
    if (problem.solution) {
      markdown += `- Solved on: ${new Date(problem.solution.timestamp).toLocaleDateString()}\n`;
    }
    
    markdown += `\n`;
  }
  
  return markdown;
}

/**
 * Format duration in seconds to human-readable format
 * @param {number} seconds - Duration in seconds
 * @returns {string} - Formatted duration
 */
function formatDuration(seconds) {
  if (seconds < 60) {
    return `${seconds.toFixed(0)} seconds`;
  } else if (seconds < 3600) {
    return `${(seconds / 60).toFixed(1)} minutes`;
  } else {
    return `${(seconds / 3600).toFixed(1)} hours`;
  }
}
