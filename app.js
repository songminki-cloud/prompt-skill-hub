const requestedTab = new URLSearchParams(window.location.search).get('tab');
const state = { tab: requestedTab === 'skills' ? 'skills' : 'prompts', query: '', data: { prompts: [], skills: [] } };

const content = document.querySelector('#content');
const search = document.querySelector('#search');
const resultCount = document.querySelector('#resultCount');
const headerCount = document.querySelector('#headerCount');
const dialog = document.querySelector('#detailDialog');
const dialogBody = document.querySelector('#dialogBody');
const toast = document.querySelector('#toast');

document.querySelectorAll('.tab').forEach(tab => tab.classList.toggle('is-active', tab.dataset.tab === state.tab));
search.placeholder = state.tab === 'prompts' ? 'Search prompts' : 'Search skills';

const escapeHtml = (value = '') => value.replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
const searchable = item => `${item.title} ${item.description || ''} ${item.content || ''}`.toLocaleLowerCase();

function filteredItems() {
  const items = state.tab === 'prompts' ? state.data.prompts : state.data.skills;
  const terms = state.query.toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return terms.length ? items.filter(item => terms.every(term => searchable(item).includes(term))) : items;
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => {
    toast.classList.add('show');
    clearTimeout(copyText.timer);
    copyText.timer = setTimeout(() => toast.classList.remove('show'), 1300);
  });
}

function showDetail(item, type) {
  const link = item.source || item.link;
  dialogBody.innerHTML = `<article class="detail">
    <h2>${escapeHtml(item.title)}</h2>
    ${type === 'skill' && item.description ? `<p>${escapeHtml(item.description)}</p>` : ''}
    <pre>${escapeHtml(item.content)}</pre>
    <div class="detail-actions">
      <button class="btn primary" data-copy-detail>${type === 'prompt' ? '프롬프트 복사' : '내용 복사'}</button>
      ${link ? `<a class="btn" href="${escapeHtml(link)}" target="_blank" rel="noreferrer">바로가기</a>` : ''}
    </div>
  </article>`;
  dialogBody.querySelector('[data-copy-detail]').addEventListener('click', () => copyText(item.content));
  dialog.showModal();
}

function renderPrompts(items) {
  content.innerHTML = items.length ? `<div class="prompt-grid">${items.map(item => `
    <article class="prompt-card">
      <div class="thumb" data-open="${item.id}">
        ${item.image ? `<img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.title)}" loading="lazy">` : '<div class="placeholder">P</div>'}
      </div>
      <div class="card-meta">
        <h2 class="card-title">${escapeHtml(item.title)}</h2>
        <div class="card-actions">
          <button class="btn primary" data-copy="${item.id}">복사하기</button>
          <button class="btn" data-open="${item.id}">보기</button>
        </div>
      </div>
    </article>`).join('')}</div>` : '<p class="empty">검색 결과가 없습니다.</p>';
  content.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', () => copyText(state.data.prompts.find(item => item.id === button.dataset.copy).content)));
  content.querySelectorAll('[data-open]').forEach(button => button.addEventListener('click', () => showDetail(state.data.prompts.find(item => item.id === button.dataset.open), 'prompt')));
}

function renderSkills(items) {
  content.innerHTML = items.length ? `<div class="skill-list">${items.map(item => `
    <article class="skill-row">
      <div class="skill-title">${escapeHtml(item.title)}</div>
      <p class="skill-desc">${escapeHtml(item.description || '설명 없음')}</p>
      <button class="skill-link" data-skill="${item.id}">내용 보기 →</button>
    </article>`).join('')}</div>` : '<p class="empty">검색 결과가 없습니다.</p>';
  content.querySelectorAll('[data-skill]').forEach(button => button.addEventListener('click', () => showDetail(state.data.skills.find(item => item.id === button.dataset.skill), 'skill')));
}

function render() {
  const items = filteredItems();
  resultCount.textContent = `${items.length}`;
  headerCount.textContent = `${state.data.prompts.length} PROMPTS · ${state.data.skills.length} SKILLS`;
  state.tab === 'prompts' ? renderPrompts(items) : renderSkills(items);
}

document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => {
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('is-active', t === tab));
  state.tab = tab.dataset.tab;
  history.replaceState(null, '', state.tab === 'skills' ? '?tab=skills' : window.location.pathname);
  search.value = '';
  state.query = '';
  search.placeholder = state.tab === 'prompts' ? 'Search prompts' : 'Search skills';
  render();
}));

search.addEventListener('input', event => { state.query = event.target.value; render(); });
document.querySelector('#dialogClose').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });

fetch('data.json').then(response => response.json()).then(data => { state.data = data; render(); });
