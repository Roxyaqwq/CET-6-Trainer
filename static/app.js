// CET-6 Vocabulary Learning - Frontend

const API = '/api';
let currentTab = 'words';
let currentPersona = 'a friendly English tutor';
let chatHistory = [];

// ============ UTILS ============
function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

function toast(msg, type = 'info') {
  const el = $('#toast');
  el.textContent = msg;
  el.className = `toast ${type} show`;
  clearTimeout(el._timeout);
  el._timeout = setTimeout(() => el.classList.remove('show'), 2500);
}

async function api(method, path, body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${API}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

// ============ TABS ============
$$('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    currentTab = tab.dataset.tab;
    $$('.tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    $$('.tab-content').forEach(c => c.classList.remove('active'));
    $(`#tab-${currentTab}`).classList.add('active');
    if (currentTab === 'words') loadWords();
    if (currentTab === 'chat') {
      $('#chat-messages').scrollTop = $('#chat-messages').scrollHeight;
    }
  });
});

// ============ WORDS MODULE ============
async function loadWords() {
  try {
    const data = await api('GET', '/words');
    renderWords(data.words);
  } catch (e) {
    toast('Failed to load words: ' + e.message, 'error');
  }
}

async function loadInfo() {
  try {
    const data = await api('GET', '/info');
    $('#cet6-total').textContent = data.cet6_total_words;
  } catch (e) {}
}

function renderWords(words) {
  const list = $('#word-list');
  $('#word-count').textContent = words.length;
  
  if (words.length === 0) {
    list.innerHTML = '<div class="empty-hint">还没有单词，请先在上面输入英语单词和汉语意思</div>';
    return;
  }

  list.innerHTML = words.map(w => `
    <div class="word-card color-${w.color}">
      <span class="word-text">${escapeHtml(w.word)}</span>
      <span class="word-meaning">${escapeHtml(w.meaning)}</span>
      <span class="word-freq">(${w.freq})</span>
      <div class="card-actions">
        <button class="edit-btn" onclick="openEdit('${escapeHtml(w.word)}','${escapeHtml(w.meaning)}','${w.custom_color}')" title="编辑">&#9998;</button>
        <button class="delete-btn" onclick="deleteWord('${escapeHtml(w.word)}')" title="删除">&#10005;</button>
      </div>
    </div>
  `).join('');
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Add word
$('#add-word-btn').addEventListener('click', addWord);
$('#word-input').addEventListener('keydown', e => { if (e.key === 'Enter') $('#meaning-input').focus(); });
$('#word-input').addEventListener('blur', autoCheckCET6);
$('#meaning-input').addEventListener('keydown', e => { if (e.key === 'Enter') addWord(); });

async function autoCheckCET6() {
  const word = $('#word-input').value.trim();
  if (!word) { $('#input-hint').textContent = ''; return; }

  try {
    const data = await api('GET', `/cet6/check/${encodeURIComponent(word)}`);
    if (data.in_cet6) {
      $('#meaning-input').value = data.meaning;
      $('#meaning-input').style.background = '#eafaf1';
      $('#input-hint').textContent = `CET-6 (freq=${data.freq}) -- meaning auto-filled, press Add or Enter`;
    } else {
      $('#meaning-input').value = '';
      $('#meaning-input').style.background = '#fff5f5';
      $('#meaning-input').placeholder = data.freq === 0 ? 'NOT in CET-6, please enter meaning manually' : 'Input Chinese meaning';
      $('#input-hint').textContent = `NOT in CET-6 database, please enter the Chinese meaning manually`;
    }
  } catch (e) {
    $('#input-hint').textContent = '';
  }
}

async function addWord() {
  const word = $('#word-input').value.trim();
  const meaning = $('#meaning-input').value.trim();
  if (!word || !meaning) {
    toast('Please enter both word and meaning', 'error');
    return;
  }
  try {
    const data = await api('POST', '/words', { word, meaning });
    $('#word-input').value = '';
    $('#meaning-input').value = '';
    $('#meaning-input').style.background = '';
    $('#meaning-input').placeholder = 'Input Chinese meaning';
    const freqLabel = data.in_cet6 ? `(CET-6, freq=${data.freq})` : '(NOT in CET-6)';
    $('#input-hint').textContent = `"${data.word}" added! ${freqLabel}`;
    loadWords();
  } catch (e) {
    toast(e.message, 'error');
    $('#input-hint').textContent = e.message;
  }
}

// Check word
$('#check-btn').addEventListener('click', checkWord);
$('#check-input').addEventListener('keydown', e => { if (e.key === 'Enter') checkWord(); });

async function checkWord() {
  const word = $('#check-input').value.trim();
  if (!word) return;
  try {
    const data = await api('GET', `/cet6/check/${encodeURIComponent(word)}`);
    const el = $('#check-result');
    if (data.in_cet6) {
      el.className = 'hint found';
      el.textContent = `"${word}" is in CET-6 | Frequency: ${data.freq} | Meaning: ${data.meaning}`;
    } else {
      el.className = 'hint not-found';
      el.textContent = `"${word}" is NOT in CET-6 database`;
    }
  } catch (e) {
    toast(e.message, 'error');
  }
}

// Delete word
async function deleteWord(word) {
  if (!confirm(`Delete "${word}"?`)) return;
  try {
    await api('DELETE', `/words/${encodeURIComponent(word)}`);
    toast(`Deleted "${word}"`, 'success');
    loadWords();
  } catch (e) {
    toast(e.message, 'error');
  }
}

// Edit modal
let editTarget = '';

function openEdit(word, meaning, customColor) {
  editTarget = word;
  $('#edit-word-display').textContent = word;
  $('#edit-meaning').value = meaning;
  $('#edit-color').value = customColor || 'none';
  $('#edit-modal').classList.add('show');
}

$('#cancel-edit-btn').addEventListener('click', () => {
  $('#edit-modal').classList.remove('show');
});

$('#edit-modal').addEventListener('click', e => {
  if (e.target === $('#edit-modal')) $('#edit-modal').classList.remove('show');
});

$('#save-edit-btn').addEventListener('click', async () => {
  const meaning = $('#edit-meaning').value.trim();
  const color = $('#edit-color').value;
  if (!meaning) { toast('Meaning cannot be empty', 'error'); return; }
  try {
    await api('PUT', `/words/${encodeURIComponent(editTarget)}`, { meaning, custom_color: color });
    $('#edit-modal').classList.remove('show');
    toast(`Updated "${editTarget}"`, 'success');
    loadWords();
  } catch (e) {
    toast(e.message, 'error');
  }
});

// ============ READING MODULE ============
$('#generate-text-btn').addEventListener('click', async () => {
  const btn = $('#generate-text-btn');
  const output = $('#reading-output');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Generating...';
  output.textContent = '';

  try {
    const body = {
      topic: $('#reading-topic').value.trim() || undefined,
      style: $('#reading-style').value || undefined,
      structure: $('#reading-structure').value || undefined,
      length: parseInt($('#reading-length').value) || undefined,
    };
    const data = await api('POST', '/generate-text', body);
    output.innerHTML = renderMarkdown(data.text);
    if (data.mode === 'mock') {
      output.innerHTML += '\n\n<i style="color:gray">(Generated in demo mode. Set OPENAI_API_KEY for AI-generated content.)</i>';
    }
  } catch (e) {
    output.textContent = 'Error: ' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = '生成阅读文本';
  }
});

function renderMarkdown(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
    .replace(/^### (.*)/gm, '<h4>$1</h4>')
    .replace(/^## (.*)/gm, '<h3>$1</h3>')
    .replace(/^# (.*)/gm, '<h2>$1</h2>');
}

// ============ CHAT MODULE ============
$('#set-persona-btn').addEventListener('click', () => {
  const persona = $('#chat-persona').value.trim();
  if (!persona) return;
  currentPersona = persona;
  $('#persona-display').textContent = `Current persona: ${persona}`;
  toast(`Persona set: ${persona}`, 'success');
});

// Set default persona display
$('#persona-display').textContent = `Default persona: ${currentPersona}`;

$('#send-chat-btn').addEventListener('click', sendChat);
$('#chat-input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChat();
  }
});

async function sendChat() {
  const input = $('#chat-input');
  const msg = input.value.trim();
  if (!msg) return;

  appendChatMsg('user', msg);
  input.value = '';

  const body = {
    persona: currentPersona,
    message: msg,
    history: chatHistory,
  };

  try {
    const data = await api('POST', '/chat', body);
    appendChatMsg('assistant', data.reply);
    chatHistory.push({ role: 'user', content: msg });
    chatHistory.push({ role: 'assistant', content: data.reply });
    if (chatHistory.length > 20) chatHistory = chatHistory.slice(-20);
  } catch (e) {
    appendChatMsg('assistant', 'Sorry, something went wrong: ' + e.message);
  }
}

function appendChatMsg(role, text) {
  const msgs = $('#chat-messages');
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  div.textContent = text;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

// ============ INIT ============
async function init() {
  await loadInfo();
  await loadWords();
}

init();
