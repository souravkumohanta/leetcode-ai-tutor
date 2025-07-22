# Getting Started with LeetCode AI Tutor

This guide will help you get started with the LeetCode AI Tutor Chrome extension.

## Installation

1. **Set up the extension**:
   - Make sure you have all the required files in the `leetcode-ai-tutor` directory
   - Generate icon files using the `icons.html` file and save them in the `icons` directory
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" in the top-right corner
   - Click "Load unpacked" and select the `leetcode-ai-tutor` folder

2. **Configure the extension**:
   - After installation, the options page will open automatically
   - If not, right-click the extension icon and select "Options"
   - Configure the following settings:
     - Problem List URL: URL to your JSON file containing LeetCode problems (see `sample-problems.json` for format)
     - AI Endpoint: URL for your AI service (local Ollama or cloud-based)
     - AI Model: Name of the model to use
     - Phase Durations: Time limits for each phase
     - GitHub Repository: For logging solutions (optional)
     - Quiz Schedule: When to conduct weekend quizzes

## Testing

Before using the extension, you can test its components:

1. Open `test.html` in your browser
2. Click the "Run All Tests" button to test all components
3. Or test individual components using the specific test buttons

For testing the problem list fetching:
- Run a local server with `python -m http.server` in the extension directory
- This will serve the `sample-problems.json` file at `http://localhost:8000/sample-problems.json`

## Using the Extension

Once installed and configured, the extension will override your new tab page:

1. **Open a new tab** to see the current problem
2. **Start with the "Understand" phase**:
   - Take notes to understand the problem
   - Use the timer to limit your time
3. **Move to the "Pseudocode" phase**:
   - Write pseudocode for your solution
4. **Continue to the "Implement" phase**:
   - Implement your solution in code
5. **Finish with the "Optimize" phase**:
   - Optimize your solution for time and space complexity
6. **Mark the problem as solved** to move to the next one

### Buttons

- **Next Phase**: Move to the next phase
- **Get Hint**: Get a hint from AI
- **Show Solution**: Show the optimal solution from AI
- **Mark Solved**: Mark the problem as solved and move to the next one
- **Skip Problem**: Skip the current problem and move to the next one

## Features

- **Structured Problem-Solving Phases**: Break down problem-solving into four phases
- **Timed Phases**: Each phase has a configurable time limit
- **AI Guidance**: Get hints and optimal solutions from AI
- **Progress Tracking**: Log your solutions and track your progress
- **GitHub Integration**: Automatically commit your solutions to GitHub
- **Weekend Review Quizzes**: Test your understanding with spaced-repetition quizzes

## Troubleshooting

If you encounter issues:

1. **Check the console** for error messages:
   - Right-click on the new tab page and select "Inspect"
   - Go to the "Console" tab to see any error messages

2. **Verify your configuration**:
   - Make sure your problem list URL is accessible
   - Check that your AI endpoint is correct and running
   - Ensure your GitHub token has the correct permissions

3. **Run the tests**:
   - Open `test.html` to run tests and identify issues

## Next Steps

- Create your own problem list JSON file with problems you want to practice
- Customize the extension by modifying the code to suit your needs
- Contribute to the project by adding new features or fixing bugs

Happy coding and good luck with your LeetCode practice!
