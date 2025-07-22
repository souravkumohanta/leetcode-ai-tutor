/**
 * AI Client module for LeetCode AI Tutor
 * Handles interactions with AI services (local Ollama or cloud-based)
 */

import * as storage from './storage.js';

/**
 * Call AI service with a prompt
 * @param {string} prompt - The prompt to send to the AI
 * @param {Object} config - Configuration object with AI settings
 * @returns {Promise<Object>} - AI response
 */
async function callAI(prompt, config) {
  if (config.aiEndpoint.includes('127.0.0.1:1234')) {
    // User's local Skywork model
    return fetchFromSkywork(prompt, config);
  } else if (config.aiEndpoint.includes('localhost') || config.aiEndpoint.includes('127.0.0.1')) {
    // Local Ollama implementation
    return fetchFromOllama(prompt, config);
  } else {
    // Cloud API implementation (OpenAI, etc.)
    return fetchFromCloudAPI(prompt, config);
  }
}

/**
 * Fetch response from local Skywork model
 * @param {string} prompt - The prompt to send to the model
 * @param {Object} config - Configuration object with AI settings
 * @returns {Promise<Object>} - Skywork response
 */
async function fetchFromSkywork(prompt, config) {
  try {
    const response = await fetch(`${config.aiEndpoint}/v1/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: config.aiModel,
        messages: [
          {
            role: "system",
            content: "You are an expert programming tutor specializing in algorithms and data structures for coding interviews."
          },
          {
            role: "user",
            content: prompt
          }
        ],
        temperature: 0.7,
        max_tokens: 1000
      })
    });
    
    const data = await response.json();
    return {
      text: data.choices?.[0]?.message?.content || "No response from Skywork model",
      model: config.aiModel,
      provider: 'skywork'
    };
  } catch (error) {
    console.error('Error calling Skywork model:', error);
    return {
      text: "Error: Could not connect to local Skywork model. Please check your configuration.",
      error: error.message
    };
  }
}

/**
 * Fetch response from local Ollama instance
 * @param {string} prompt - The prompt to send to Ollama
 * @param {Object} config - Configuration object with AI settings
 * @returns {Promise<Object>} - Ollama response
 */
async function fetchFromOllama(prompt, config) {
  try {
    const response = await fetch(`${config.aiEndpoint}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: config.aiModel,
        prompt: prompt,
        stream: false
      })
    });
    
    const data = await response.json();
    return {
      text: data.response,
      model: config.aiModel,
      provider: 'ollama'
    };
  } catch (error) {
    console.error('Error calling Ollama:', error);
    return {
      text: "Error: Could not connect to Ollama. Please check your configuration.",
      error: error.message
    };
  }
}

/**
 * Fetch response from cloud API
 * @param {string} prompt - The prompt to send to the cloud API
 * @param {Object} config - Configuration object with AI settings
 * @returns {Promise<Object>} - Cloud API response
 */
async function fetchFromCloudAPI(prompt, config) {
  // Detect API type based on endpoint URL
  if (config.aiEndpoint.includes('openai.com')) {
    return fetchFromOpenAI(prompt, config);
  } else if (config.aiEndpoint.includes('anthropic.com')) {
    return fetchFromAnthropic(prompt, config);
  } else {
    // Generic API implementation
    try {
      const response = await fetch(config.aiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${config.apiKey || ''}`
        },
        body: JSON.stringify({
          model: config.aiModel,
          prompt: prompt,
          max_tokens: 1000
        })
      });
      
      const data = await response.json();
      return {
        text: data.choices?.[0]?.text || data.output || data.response || "No response from API",
        model: config.aiModel,
        provider: 'generic'
      };
    } catch (error) {
      console.error('Error calling cloud API:', error);
      return {
        text: "Error: Could not connect to AI service. Please check your configuration.",
        error: error.message
      };
    }
  }
}

/**
 * Fetch response from OpenAI API
 * @param {string} prompt - The prompt to send to OpenAI
 * @param {Object} config - Configuration object with AI settings
 * @returns {Promise<Object>} - OpenAI response
 */
async function fetchFromOpenAI(prompt, config) {
  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.apiKey || ''}`
      },
      body: JSON.stringify({
        model: config.aiModel || 'gpt-3.5-turbo',
        messages: [
          {
            role: 'system',
            content: 'You are an expert programming tutor specializing in algorithms and data structures for coding interviews.'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        max_tokens: 1000
      })
    });
    
    const data = await response.json();
    return {
      text: data.choices?.[0]?.message?.content || "No response from OpenAI",
      model: config.aiModel,
      provider: 'openai'
    };
  } catch (error) {
    console.error('Error calling OpenAI:', error);
    return {
      text: "Error: Could not connect to OpenAI. Please check your API key and configuration.",
      error: error.message
    };
  }
}

/**
 * Fetch response from Anthropic API
 * @param {string} prompt - The prompt to send to Anthropic
 * @param {Object} config - Configuration object with AI settings
 * @returns {Promise<Object>} - Anthropic response
 */
async function fetchFromAnthropic(prompt, config) {
  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': config.apiKey || '',
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: config.aiModel || 'claude-2',
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ],
        max_tokens: 1000
      })
    });
    
    const data = await response.json();
    return {
      text: data.content?.[0]?.text || "No response from Anthropic",
      model: config.aiModel,
      provider: 'anthropic'
    };
  } catch (error) {
    console.error('Error calling Anthropic:', error);
    return {
      text: "Error: Could not connect to Anthropic. Please check your API key and configuration.",
      error: error.message
    };
  }
}

/**
 * Get pseudocode for a problem
 * @param {string} problemUrl - URL of the problem
 * @returns {Promise<Object>} - AI response with pseudocode
 */
export async function getPseudocode(problemUrl) {
  const config = await storage.getConfig();
  const prompt = `
You are an expert programming tutor. I'm working on the LeetCode problem at ${problemUrl}.
Please provide a clear, step-by-step pseudocode solution for this problem.
Focus on the algorithm and approach, not the specific programming language syntax.
Include:
1. A brief explanation of the problem
2. The key insights needed to solve it
3. Time and space complexity analysis
4. Step-by-step pseudocode
`;
  
  return callAI(prompt, config);
}

/**
 * Get coaching based on user's pseudocode
 * @param {string} problemUrl - URL of the problem
 * @param {string} userPseudocode - User's pseudocode
 * @returns {Promise<Object>} - AI response with coaching
 */
export async function getCoaching(problemUrl, userPseudocode) {
  const config = await storage.getConfig();
  const prompt = `
You are an expert programming tutor. I'm working on the LeetCode problem at ${problemUrl}.
Here is my pseudocode solution:

${userPseudocode}

Please review my pseudocode and provide constructive feedback:
1. Is my approach correct? If not, what's wrong with it?
2. Can the algorithm be optimized further?
3. Are there any edge cases I'm missing?
4. What's the time and space complexity of my solution?
5. Any suggestions for implementation?
`;
  
  return callAI(prompt, config);
}

/**
 * Get optimal solution for a problem
 * @param {string} problemUrl - URL of the problem
 * @returns {Promise<Object>} - AI response with optimal solution
 */
export async function getOptimalSolution(problemUrl) {
  const config = await storage.getConfig();
  const prompt = `
You are an expert programming tutor. I'm working on the LeetCode problem at ${problemUrl}.
I've attempted the problem but would like to see an optimal solution.
Please provide:
1. The most efficient algorithm for this problem
2. A clear implementation in pseudocode
3. Detailed explanation of why this approach is optimal
4. Time and space complexity analysis
5. Any common pitfalls to avoid
`;
  
  return callAI(prompt, config);
}

/**
 * Generate a quiz based on past problems
 * @param {Array<string>} topics - Array of problem URLs or topics
 * @returns {Promise<Object>} - AI response with quiz
 */
export async function generateQuiz(topics) {
  const config = await storage.getConfig();
  const topicsText = topics.join('\n');
  const prompt = `
You are an expert programming tutor. Based on the following LeetCode problems I've worked on:

${topicsText}

Please create a quiz with 5 questions that test my understanding of the core concepts from these problems.
For each question:
1. Provide a short problem statement
2. Include 4 multiple-choice options
3. Mark the correct answer
4. Add a brief explanation of why the answer is correct

Focus on testing algorithmic understanding rather than syntax details.
`;
  
  return callAI(prompt, config);
}

/**
 * Parse quiz response into structured format
 * @param {string} quizText - Raw quiz text from AI
 * @returns {Object} - Structured quiz object
 */
export function parseQuiz(quizText) {
  // Simple parsing logic - can be enhanced for more robust parsing
  const questions = [];
  const sections = quizText.split(/Question \d+:/i).filter(s => s.trim());
  
  for (let i = 0; i < sections.length; i++) {
    const section = sections[i].trim();
    
    // Extract options
    const options = [];
    const optionMatches = section.match(/[A-D]\)\s.+/g) || [];
    for (const match of optionMatches) {
      options.push(match.trim());
    }
    
    // Extract correct answer
    let correctAnswer = '';
    const correctMatch = section.match(/Correct answer:\s*([A-D])/i);
    if (correctMatch) {
      correctAnswer = correctMatch[1];
    }
    
    // Extract explanation
    let explanation = '';
    const explMatch = section.match(/Explanation:\s*([\s\S]+)$/i);
    if (explMatch) {
      explanation = explMatch[1].trim();
    }
    
    // Extract problem statement (everything before first option)
    let problemStatement = section;
    if (optionMatches.length > 0) {
      const firstOptionIndex = section.indexOf(optionMatches[0]);
      if (firstOptionIndex > 0) {
        problemStatement = section.substring(0, firstOptionIndex).trim();
      }
    }
    
    questions.push({
      problemStatement,
      options,
      correctAnswer,
      explanation
    });
  }
  
  return {
    questions,
    timestamp: new Date().toISOString()
  };
}
