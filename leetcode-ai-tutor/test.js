/**
 * Test script for LeetCode AI Tutor Chrome Extension
 * This script can be used to test various components of the extension
 */

// Test configuration
const TEST_CONFIG = {
  problemListUrl: 'http://localhost:8000/sample-problems.json',
  aiEndpoint: 'http://localhost:11434',
  aiModel: 'llama2',
  phaseDurations: {
    understand: 30, // 30 seconds for testing
    pseudocode: 30,
    implement: 30,
    optimize: 30
  },
  github: {
    repo: 'username/repository',
    token: 'your-github-token'
  },
  quizCron: '* * * * *' // Every minute for testing
};

/**
 * Test storage module
 */
async function testStorage() {
  console.log('Testing storage module...');
  
  try {
    const storage = await import('./storage.js');
    
    // Test saving config
    await storage.saveConfig(TEST_CONFIG);
    console.log('✅ Saved test configuration');
    
    // Test getting config
    const config = await storage.getConfig();
    console.log('✅ Retrieved configuration:', config);
    
    // Test fetching problem list
    if (TEST_CONFIG.problemListUrl.startsWith('http://localhost')) {
      console.log('⚠️ Skipping problem list fetch test (requires local server)');
      console.log('   To test: Run a local server with `python -m http.server` in the extension directory');
    } else {
      const problems = await storage.fetchProblemList(TEST_CONFIG.problemListUrl);
      console.log(`✅ Fetched ${problems.length} problems`);
    }
    
    return true;
  } catch (error) {
    console.error('❌ Storage test failed:', error);
    return false;
  }
}

/**
 * Test timer module
 */
async function testTimer() {
  console.log('Testing timer module...');
  
  try {
    const timer = await import('./timer.js');
    
    // Test scheduling alarms
    timer.scheduleAlarms(TEST_CONFIG.phaseDurations, TEST_CONFIG.quizCron);
    console.log('✅ Scheduled alarms');
    
    // Test phase timer
    const timerObj = timer.startPhaseTimer('test', 5);
    console.log('✅ Started phase timer:', timerObj);
    
    // Test recording phase start
    const record = timer.recordPhaseStart('https://leetcode.com/problems/test/', 'test');
    console.log('✅ Recorded phase start:', record);
    
    // Test getting current phase
    const currentPhase = timer.getCurrentPhase();
    console.log('✅ Got current phase:', currentPhase);
    
    // Test completing current phase
    const completedPhase = timer.completeCurrentPhase();
    console.log('✅ Completed current phase:', completedPhase);
    
    return true;
  } catch (error) {
    console.error('❌ Timer test failed:', error);
    return false;
  }
}

/**
 * Test AI client module
 */
async function testAIClient() {
  console.log('Testing AI client module...');
  
  try {
    const ai = await import('./ai_client.js');
    
    console.log('⚠️ Skipping AI client tests (requires API access)');
    console.log('   To test: Configure AI endpoint and model in TEST_CONFIG');
    
    // Test quiz parsing
    const sampleQuizText = `
Question 1:
What is the time complexity of the Two Sum solution using a hash map?
A) O(n²)
B) O(n log n)
C) O(n)
D) O(1)

Correct answer: C

Explanation: The hash map solution requires a single pass through the array, which is O(n).

Question 2:
Which data structure is most efficient for implementing a cache?
A) Array
B) Linked List
C) Hash Map
D) Binary Search Tree

Correct answer: C

Explanation: Hash maps provide O(1) average time complexity for lookups, which is ideal for caches.
`;
    
    const parsedQuiz = ai.parseQuiz(sampleQuizText);
    console.log('✅ Parsed quiz:', parsedQuiz);
    
    return true;
  } catch (error) {
    console.error('❌ AI client test failed:', error);
    return false;
  }
}

/**
 * Run all tests
 */
async function runTests() {
  console.log('Running LeetCode AI Tutor tests...');
  console.log('==================================');
  
  const results = {
    storage: await testStorage(),
    timer: await testTimer(),
    aiClient: await testAIClient()
  };
  
  console.log('==================================');
  console.log('Test Results:');
  
  for (const [test, passed] of Object.entries(results)) {
    console.log(`${passed ? '✅' : '❌'} ${test}`);
  }
  
  const allPassed = Object.values(results).every(Boolean);
  console.log('==================================');
  console.log(`Overall: ${allPassed ? '✅ All tests passed' : '❌ Some tests failed'}`);
}

// Run tests when script is loaded in browser
if (typeof window !== 'undefined') {
  window.runTests = runTests;
  console.log('Test script loaded. Run tests with window.runTests()');
}

// Export for module usage
export { runTests, testStorage, testTimer, testAIClient };
