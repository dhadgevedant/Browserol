const runTaskButton = document.getElementById('run-task');
const taskInput = document.getElementById('task-input');
const statusElement = document.getElementById('status');
const logOutput = document.getElementById('log-output');
const historyList = document.getElementById('history-list');

const API_BASE = 'http://localhost:8000';

function appendLog(message) {
  const timestamp = new Date().toLocaleTimeString();
  logOutput.textContent += `[${timestamp}] ${message}\n`;
  logOutput.scrollTop = logOutput.scrollHeight;
}

async function loadHistory() {
  try {
    const response = await fetch(`${API_BASE}/history`);
    if (!response.ok) {
      appendLog('Unable to load history.');
      return;
    }
    const data = await response.json();
    historyList.innerHTML = '';
    data.history.slice(0, 5).forEach((item) => {
      const li = document.createElement('li');
      li.innerHTML = `<strong>${new Date(item.timestamp).toLocaleString()}</strong>: ${item.instruction}`;
      historyList.appendChild(li);
    });
  } catch (error) {
    appendLog(`History request failed: ${error}`);
  }
}

async function runTask() {
  const instruction = taskInput.value.trim();
  if (!instruction) {
    appendLog('Please enter an instruction.');
    return;
  }

  statusElement.textContent = 'Running...';
  appendLog(`Sending task: ${instruction}`);

  try {
    const response = await fetch(`${API_BASE}/run-task`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ instruction }),
    });

    if (!response.ok) {
      const error = await response.json();
      appendLog(`Request failed: ${error.detail || response.statusText}`);
      statusElement.textContent = 'Error';
      return;
    }

    const result = await response.json();
    statusElement.textContent = result.success ? 'Completed' : 'Failed';
    appendLog(`Task completed: ${result.success ? 'Success' : 'Partial failure'}`);
    result.logs.forEach((entry) => {
      appendLog(`Step ${entry.step_number}: ${JSON.stringify(entry.raw)}`);
      appendLog(`  Status: ${entry.status}`);
      if (entry.result) {
        appendLog(`  Result: ${JSON.stringify(entry.result)}`);
      }
      if (entry.error) {
        appendLog(`  Error: ${entry.error}`);
      }
      if (entry.vision_hint) {
        appendLog(`  Vision hint: ${entry.vision_hint}`);
      }
    });

    await loadHistory();
  } catch (error) {
    appendLog(`Task request failed: ${error}`);
    statusElement.textContent = 'Error';
  }
}

runTaskButton.addEventListener('click', runTask);
window.addEventListener('load', loadHistory);
