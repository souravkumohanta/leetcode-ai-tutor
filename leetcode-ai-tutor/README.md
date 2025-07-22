# LeetCode AI Tutor Chrome Extension

A Chrome extension that helps you practice LeetCode problems with structured phases, AI guidance, and progress tracking.

## Features

- **Structured Problem-Solving Phases**: Break down problem-solving into four phases:
  - **Understand**: Take time to fully understand the problem
  - **Pseudocode**: Plan your solution with pseudocode
  - **Implement**: Write the actual code implementation
  - **Optimize**: Refine and optimize your solution

- **Timed Phases**: Each phase has a configurable time limit to help you practice efficiently

- **AI Guidance**: Get hints and optimal solutions from AI when you're stuck
  - Supports both local AI (Ollama) and cloud-based services (OpenAI, Anthropic)

- **Progress Tracking**: Log your solutions and track your progress over time

- **GitHub Integration**: Automatically commit your solutions to a GitHub repository

- **Weekend Review Quizzes**: Test your understanding with spaced-repetition quizzes on weekends

## Installation

### From Source (Developer Mode)

1. Clone or download this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top-right corner
4. Click "Load unpacked" and select the `leetcode-ai-tutor` folder
5. The extension should now be installed and will override your new tab page

### Icon Setup

1. Open `icons.html` in your browser
2. Click on each icon to download it as a PNG file
3. Save the icons in the `icons` folder with the appropriate names:
   - `icon16.png`
   - `icon48.png`
   - `icon128.png`

## Configuration

After installation, the extension will open the options page. You can also access it by right-clicking the extension icon and selecting "Options".

### Problem List

Provide a URL to a JSON file containing LeetCode problems. The JSON should have the following format:

```json
{
  "problems": [
    {
      "url": "https://leetcode.com/problems/two-sum/",
      "title": "Two Sum",
      "difficulty": "Easy",
      "tags": ["Array", "Hash Table"]
    },
    {
      "url": "https://leetcode.com/problems/add-two-numbers/",
      "title": "Add Two Numbers",
      "difficulty": "Medium",
      "tags": ["Linked List", "Math", "Recursion"]
    }
  ]
}
```

### AI Configuration

- **AI Endpoint**: URL for the AI service
  - For local Ollama: `http://localhost:11434`
  - For OpenAI: `https://api.openai.com/v1`
  - For Anthropic: `https://api.anthropic.com/v1`

- **AI Model**: Name of the model to use
  - For Ollama: `llama2`, `codellama`, etc.
  - For OpenAI: `gpt-3.5-turbo`, `gpt-4`, etc.
  - For Anthropic: `claude-2`, etc.

- **API Key**: Required for cloud-based services (leave empty for local Ollama)

### Phase Durations

Set the duration (in seconds) for each phase:
- Understand: Default 300 (5 minutes)
- Pseudocode: Default 600 (10 minutes)
- Implement: Default 900 (15 minutes)
- Optimize: Default 600 (10 minutes)

### GitHub Integration

- **GitHub Repository**: Format: `username/repository`
- **GitHub Personal Access Token**: Token with 'repo' scope permissions

### Quiz Schedule

- **Quiz Schedule (Cron Expression)**: Default: `0 10 * * 6,0` (10:00 AM on weekends)

## Usage

1. Open a new tab to see the current problem
2. Start with the "Understand" phase
   - Take notes to understand the problem
   - Use the timer to limit your time
3. Move to the "Pseudocode" phase
   - Write pseudocode for your solution
4. Continue to the "Implement" phase
   - Implement your solution in code
5. Finish with the "Optimize" phase
   - Optimize your solution for time and space complexity
6. Mark the problem as solved to move to the next one

### Buttons

- **Next Phase**: Move to the next phase
- **Get Hint**: Get a hint from AI
- **Show Solution**: Show the optimal solution from AI
- **Mark Solved**: Mark the problem as solved and move to the next one
- **Skip Problem**: Skip the current problem and move to the next one

## Requirements

- Chrome browser
- For local AI: Ollama running locally
- For GitHub integration: GitHub account and personal access token
- For cloud-based AI: API key for the respective service

## Development

The extension is built with vanilla JavaScript and uses Chrome's extension APIs. The main components are:

- `manifest.json`: Extension configuration
- `background.js`: Background script for handling events
- `newtab.html/js`: New tab page UI and logic
- `options.html/js`: Options page UI and logic
- `storage.js`: Storage handling
- `timer.js`: Timer functionality
- `ai_client.js`: AI service integration
- `logger.js`: Logging and GitHub integration
- `quiz.js`: Weekend quiz functionality

## License

MIT
