// ==========================================================================
// CREATIVE DEPOT - CLIENT-SIDE INTERACTION & DATA MANAGEMENT
// ==========================================================================

// ローカル開発時は localhost:8001、Vercel 本番では同一オリジンの /api を使用
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://localhost:8001'
  : '';

document.addEventListener('DOMContentLoaded', () => {
  // --- State Variables ---
  let creativeCards = [];
  let currentFilterCategory = 'all';
  let currentFilterIndustry = 'all';
  let currentSearchQuery = '';

  // --- Category Thumbnail Themes (Unsplash high-quality images) ---
  const categoryImages = {
    "ブランディング": [
      "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=600&q=80"
    ],
    "マス＆ビジュアル表現": [
      "https://images.unsplash.com/photo-1626785774573-4b799315345d?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=600&q=80"
    ],
    "テレビCM・WEB動画": [
      "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=600&q=80"
    ],
    "パッケージデザイン・装丁": [
      "https://images.unsplash.com/photo-1530587191325-3db32d826c18?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1607344645866-009c320c5ab8?auto=format&fit=crop&w=600&q=80"
    ],
    "SNS施策・キャンペーン": [
      "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1562577309-4932fdd64cd1?auto=format&fit=crop&w=600&q=80"
    ],
    "WEBサイト・UI/UX": [
      "https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1586717791821-3f44a563fa4c?auto=format&fit=crop&w=600&q=80"
    ],
    "イベント・ポップアップストア": [
      "https://images.unsplash.com/photo-1511578314322-379afb476865?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1475721027785-f74eccf877e2?auto=format&fit=crop&w=600&q=80"
    ],
    "インストア・販促プロモーション": [
      "https://images.unsplash.com/photo-1563013544-824ae1d704d3?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?auto=format&fit=crop&w=600&q=80"
    ],
    "空間デザイン・環境演出": [
      "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&w=600&q=80"
    ],
    "PR・ソーシャルグッド（SDGs）": [
      "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1550355291-bbee04a92027?auto=format&fit=crop&w=600&q=80"
    ],
    "ゲリラマーケティング": [
      "https://images.unsplash.com/photo-1572945281861-68b122e3e116?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=600&q=80"
    ],
    "AI・最新テック活用": [
      "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1677442136019-21780efad99a?auto=format&fit=crop&w=600&q=80"
    ],
    "メタバース・ゲーム内施策": [
      "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=600&q=80",
      "https://images.unsplash.com/photo-1612287230202-1bf1d85d1bdf?auto=format&fit=crop&w=600&q=80"
    ]
  };

  // --- Domestic Elements ---
  const cardsGridContainer = document.getElementById('cards-grid-container');
  const searchInput = document.getElementById('search-input');
  const clearSearchBtn = document.getElementById('clear-search-btn');
  const resultsCount = document.getElementById('results-count');
  const categoryTagsContainer = document.getElementById('category-tags-container');
  const industryTagsContainer = document.getElementById('industry-tags-container');

  // Navigation Tabs
  const viewModeBtn = document.getElementById('view-mode-btn');
  const adminModeBtn = document.getElementById('admin-mode-btn');
  const viewerSection = document.getElementById('viewer-section');
  const adminSection = document.getElementById('admin-section');

  // Modal elements
  const detailModal = document.getElementById('detail-modal');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const modalHeroBg = document.getElementById('modal-hero-bg');
  const modalCategory = document.getElementById('modal-category');
  const modalIndustry = document.getElementById('modal-industry');
  const modalTitle = document.getElementById('modal-title');
  const modalSubmitter = document.getElementById('modal-submitter');
  const modalDate = document.getElementById('modal-date');
  const modalBrief = document.getElementById('modal-brief');
  const modalInsight = document.getElementById('modal-insight');
  const modalApproach = document.getElementById('modal-approach');
  const modalSolution = document.getElementById('modal-solution');
  const modalLink = document.getElementById('modal-link');
  const modalPdfLink = document.getElementById('modal-pdf-link');
  const modalPdfFilename = document.getElementById('modal-pdf-filename');

  // Admin Form elements
  const addCardForm = document.getElementById('add-card-form');
  const inputTitle = document.getElementById('input-title');
  const inputCategory = document.getElementById('input-category');
  const inputIndustry = document.getElementById('input-industry');
  const inputUrl = document.getElementById('input-url');
  const inputSubmitter = document.getElementById('input-submitter');
  const inputThumbnail = document.getElementById('input-thumbnail');
  const inputRawMemo = document.getElementById('input-raw-memo');
  const inputBrief = document.getElementById('input-brief');
  const inputInsight = document.getElementById('input-insight');
  const inputApproach = document.getElementById('input-approach');
  const inputSolution = document.getElementById('input-solution');
  const inputKeywords = document.getElementById('input-keywords');
  const inputUserMemo = document.getElementById('input-user-memo');
  const randThumbBtn = document.getElementById('rand-thumb-btn');
  const generateAiBtn = document.getElementById('generate-ai-btn');
  const aiLoading = document.getElementById('ai-loading');
  const analyzeUrlBtn = document.getElementById('analyze-url-btn');
  const urlStatusEl = document.getElementById('url-status');
  const editCardIdInput = document.getElementById('edit-card-id');
  const formSubmitBtn = document.getElementById('form-submit-btn');
  const cancelEditBtn = document.getElementById('cancel-edit-btn');

  // PDF elements
  const inputPdf = document.getElementById('input-pdf');
  const pdfUploadArea = document.getElementById('pdf-upload-area');
  const pdfUploadPlaceholder = document.getElementById('pdf-upload-placeholder');
  const pdfSelectedInfo = document.getElementById('pdf-selected-info');
  const pdfFilenameDisplay = document.getElementById('pdf-filename-display');
  const pdfAnalyzeBtn = document.getElementById('pdf-analyze-btn');
  const pdfStatusEl = document.getElementById('pdf-status');
  const sourceTabs = document.querySelectorAll('.source-tab');
  const sourceUrlSection = document.getElementById('source-url-section');
  const sourcePdfSection = document.getElementById('source-pdf-section');
  // PDFのblobURLをカードIDで管理（セッション中のみ有効）
  const pdfBlobMap = new Map();
  let currentPdfFile = null;

  // Keyword search elements
  const keywordInput = document.getElementById('keyword-input');
  const keywordTagsEl = document.getElementById('keyword-tags');
  const keywordTagsWrapper = document.getElementById('keyword-tags-wrapper');
  const searchKeywordsBtn = document.getElementById('search-keywords-btn');
  const searchStatusEl = document.getElementById('search-status');
  const searchResultsPanel = document.getElementById('search-results-panel');
  const searchResultsList = document.getElementById('search-results-list');
  let keywords = [];

  // Sync / Action elements
  const syncTotalCount = document.getElementById('sync-total-count');
  const downloadJsonBtn = document.getElementById('download-json-btn');
  const copyJsonBtn = document.getElementById('copy-json-btn');
  const resetDataBtn = document.getElementById('reset-data-btn');

  // Import elements
  const importTsvInput = document.getElementById('import-tsv-input');
  const importTsvBtn = document.getElementById('import-tsv-btn');
  const importAiBtn = document.getElementById('import-ai-btn');
  const importAiProgress = document.getElementById('import-ai-progress');
  const importPreview = document.getElementById('import-preview');
  const downloadTemplateBtn = document.getElementById('download-template-btn');
  let _pendingImportCards = [];

  // --- Initialize App ---
  init();

  async function init() {
    // 1. Load Data
    const localData = localStorage.getItem('creative_hub_data');
    if (localData) {
      creativeCards = JSON.parse(localData);
      renderCards();
      updateSyncStats();
    } else {
      try {
        const response = await fetch('data.json');
        if (!response.ok) throw new Error('Data file not found');
        creativeCards = await response.json();
        saveDataToLocal();
        renderCards();
        updateSyncStats();
      } catch (error) {
        console.error('Error fetching data.json, loading empty fallback:', error);
        creativeCards = [];
        renderCards();
        updateSyncStats();
      }
    }

    // 2. Setup Category Tags Listeners
    categoryTagsContainer.addEventListener('click', (e) => {
      const btn = e.target.closest('.tag-filter-btn');
      if (!btn) return;

      document.querySelectorAll('.tag-filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      currentFilterCategory = btn.getAttribute('data-category');

      const catLabel = document.getElementById('category-active-label');
      if (catLabel) catLabel.textContent = btn.textContent;
      const catTrigger = document.getElementById('category-trigger-btn');
      if (catTrigger) catTrigger.classList.toggle('has-filter', currentFilterCategory !== 'all');

      renderCards();
    });

    // Setup Industry Tags Listeners
    industryTagsContainer.addEventListener('click', (e) => {
      const btn = e.target.closest('.tag-industry-btn');
      if (!btn) return;

      document.querySelectorAll('.tag-industry-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      currentFilterIndustry = btn.getAttribute('data-industry');

      const indLabel = document.getElementById('industry-active-label');
      if (indLabel) indLabel.textContent = btn.textContent;
      const indTrigger = document.getElementById('industry-trigger-btn');
      if (indTrigger) indTrigger.classList.toggle('has-filter', currentFilterIndustry !== 'all');

      renderCards();
    });

    // 3. Setup Search Listener
    searchInput.addEventListener('input', (e) => {
      currentSearchQuery = e.target.value.toLowerCase().trim();
      if (currentSearchQuery.length > 0) {
        clearSearchBtn.style.display = 'block';
      } else {
        clearSearchBtn.style.display = 'none';
      }
      renderCards();
    });

    clearSearchBtn.addEventListener('click', () => {
      searchInput.value = '';
      currentSearchQuery = '';
      clearSearchBtn.style.display = 'none';
      renderCards();
    });

    // 4. View Switching
    viewModeBtn.addEventListener('click', () => switchMode('viewer'));
    adminModeBtn.addEventListener('click', () => switchMode('admin'));

    // 5. Modal Close
    modalCloseBtn.addEventListener('click', closeModal);
    detailModal.addEventListener('click', (e) => {
      if (e.target === detailModal) closeModal();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && detailModal.classList.contains('active')) {
        closeModal();
      }
    });

    // 6. Admin Actions
    randThumbBtn.addEventListener('click', setRandomThumbnail);
    generateAiBtn.addEventListener('click', generateSimulatedAISummary);
    addCardForm.addEventListener('submit', handleFormSubmit);

    // Edit cancel
    cancelEditBtn.addEventListener('click', () => {
      resetEditMode();
      switchMode('viewer');
    });

    // --- Keyword tag input ---
    keywordInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        addKeyword(keywordInput.value.trim());
      }
    });
    // タグエリアをクリックするとinputにフォーカス
    keywordTagsWrapper.addEventListener('click', () => keywordInput.focus());

    // 検索ボタン
    searchKeywordsBtn.addEventListener('click', () => {
      if (keywords.length > 0) searchByKeywords();
    });

    // Source tabs: URL / PDF 切り替え
    sourceTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        sourceTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const isUrl = tab.dataset.tab === 'url';
        sourceUrlSection.style.display = isUrl ? '' : 'none';
        sourcePdfSection.style.display = isUrl ? 'none' : '';
      });
    });

    // PDF upload area クリック
    pdfUploadArea.addEventListener('click', () => inputPdf.click());
    inputPdf.addEventListener('change', () => {
      if (inputPdf.files[0]) handlePdfSelect(inputPdf.files[0]);
    });
    // ドラッグ&ドロップ
    pdfUploadArea.addEventListener('dragover', e => { e.preventDefault(); pdfUploadArea.classList.add('drag-over'); });
    pdfUploadArea.addEventListener('dragleave', () => pdfUploadArea.classList.remove('drag-over'));
    pdfUploadArea.addEventListener('drop', e => {
      e.preventDefault();
      pdfUploadArea.classList.remove('drag-over');
      const f = e.dataTransfer.files[0];
      const accepted = /\.(pdf|jpe?g|png|webp)$/i.test(f?.name || '') ||
        ['application/pdf','image/jpeg','image/png','image/webp'].includes(f?.type || '');
      if (f && accepted) handlePdfSelect(f);
    });
    // PDF解析ボタン
    if (pdfAnalyzeBtn) pdfAnalyzeBtn.addEventListener('click', () => {
      if (currentPdfFile) analyzePdf(currentPdfFile);
    });

    // URL auto-analyze: ボタンクリック or URL入力後Enterで解析
    analyzeUrlBtn.addEventListener('click', () => {
      const url = inputUrl.value.trim();
      if (url.startsWith('http')) autoAnalyzeUrl(url);
    });
    inputUrl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const url = inputUrl.value.trim();
        if (url.startsWith('http')) autoAnalyzeUrl(url);
      }
    });
    // URLペースト時に自動解析
    inputUrl.addEventListener('paste', (e) => {
      setTimeout(() => {
        const url = inputUrl.value.trim();
        if (url.startsWith('http')) autoAnalyzeUrl(url);
      }, 50);
    });

    // 7. Sync Actions
    downloadJsonBtn.addEventListener('click', downloadJSONFile);
    copyJsonBtn.addEventListener('click', copyJSONToClipboard);
    resetDataBtn.addEventListener('click', resetToOriginalData);

    // 8. TSV Import
    importTsvInput.addEventListener('input', () => previewTsvImport(importTsvInput.value));
    importTsvBtn.addEventListener('click', () => executeTsvImport(importTsvInput.value));
    importAiBtn.addEventListener('click', () => batchAnalyzeAndImport(_pendingImportCards));
    if (downloadTemplateBtn) downloadTemplateBtn.addEventListener('click', downloadImportTemplate);
  }

  // --- Core functions ---

  // Save to localStorage
  function saveDataToLocal() {
    localStorage.setItem('creative_hub_data', JSON.stringify(creativeCards));
    updateSyncStats();
  }

  // Update sync statistics
  function updateSyncStats() {
    if (syncTotalCount) syncTotalCount.textContent = creativeCards.length;
  }

  // Switch between gallery viewer and admin form
  function switchMode(mode) {
    if (mode === 'viewer') {
      viewModeBtn.classList.add('active');
      adminModeBtn.classList.remove('active');
      viewerSection.classList.add('active');
      adminSection.classList.remove('active');
      renderCards(); // Refresh lists
    } else {
      adminModeBtn.classList.add('active');
      viewModeBtn.classList.remove('active');
      adminSection.classList.add('active');
      viewerSection.classList.remove('active');
    }
  }

  // Render cards in the grid
  function renderCards() {
    cardsGridContainer.innerHTML = '';

    // Filter cards
    const filtered = creativeCards.filter(card => {
      const matchesCategory = currentFilterCategory === 'all' || card.category === currentFilterCategory;
      const matchesIndustry = currentFilterIndustry === 'all' || card.industry === currentFilterIndustry;
      
      const searchFields = [
        card.title || '',
        card.category || '',
        card.industry || '',
        card.submitter || '',
        card.brief || '',
        card.insight || '',
        card.approach || '',
        card.solution || '',
        card.keywords || '',
        card.userMemo || '',
      ].join(' ').toLowerCase();

      const matchesSearch = currentSearchQuery === '' || searchFields.includes(currentSearchQuery);

      return matchesCategory && matchesIndustry && matchesSearch;
    });

    // Sort: newest first
    filtered.sort((a, b) => b.id - a.id);

    // Update count
    resultsCount.textContent = filtered.length;

    if (filtered.length === 0) {
      cardsGridContainer.innerHTML = `
        <div class="empty-state">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <h3>該当するクリエイティブ事例が見つかりませんでした</h3>
          <p>キーワードを変更するか、別のカテゴリーを選択してください。</p>
        </div>
      `;
      return;
    }

    filtered.forEach(card => {
      const cardEl = document.createElement('div');
      cardEl.className = 'creative-card glass-panel';
      
      // Select thumbnail or default based on category
      let thumbUrl = card.thumbnail;
      if (!thumbUrl) {
        const themeList = categoryImages[card.category] || categoryImages["マス＆ビジュアル表現"];
        thumbUrl = themeList[card.id % themeList.length];
      }

      cardEl.innerHTML = `
        <div class="card-img-wrapper">
          <img src="${thumbUrl}" alt="${card.title}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=600&q=80'">
          <div class="card-img-overlay" style="display: flex; flex-direction: column; gap: 0.35rem; align-items: flex-start; justify-content: flex-end;">
            <span class="card-badge-cat">${card.category}</span>
            <span class="card-badge-cat" style="background: rgba(139, 92, 246, 0.65); border-color: rgba(139, 92, 246, 0.3); color: #c4b5fd;">${card.industry || 'その他'}</span>
          </div>
        </div>
        <div class="card-content">
          <h3>${card.title}</h3>
          <div class="card-brief-preview">
            <strong>課題:</strong> ${card.brief}
          </div>
          <div class="card-footer">
            <span class="submitter-badge">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
              ${card.submitter}
            </span>
            <span>${card.createdAt || '2026-05-23'}</span>
            <button class="card-edit-btn" title="この事例を編集">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
              編集
            </button>
          </div>
        </div>
      `;

      cardEl.addEventListener('click', () => openModal(card));
      cardEl.querySelector('.card-edit-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        editCard(card);
      });
      cardsGridContainer.appendChild(cardEl);
    });
  }

  // --- Modal Operations ---
  function openModal(card) {
    let thumbUrl = card.thumbnail;
    if (!thumbUrl) {
      const themeList = categoryImages[card.category] || categoryImages["マス＆ビジュアル表現"];
      thumbUrl = themeList[card.id % themeList.length];
    }

    modalHeroBg.style.backgroundImage = `url('${thumbUrl}')`;
    modalCategory.textContent = card.category;
    modalIndustry.textContent = card.industry || 'その他';
    modalTitle.textContent = card.title;
    modalSubmitter.textContent = card.submitter;
    modalDate.textContent = card.createdAt || '2026-05-23';
    modalBrief.textContent = card.brief;
    modalInsight.textContent = card.insight;
    modalApproach.textContent = card.approach || '';
    modalSolution.textContent = card.solution;

    // URL / PDF / 画像 リンクの切り替え
    const cardUrl = card.url || '';
    if (cardUrl.startsWith('pdf://') || cardUrl.startsWith('img://')) {
      // pdf://ファイル名||blobURL or img://ファイル名||blobURL 形式
      const rawPath = cardUrl.replace(/^(pdf|img):\/\//, '');
      const parts = rawPath.split('||');
      const fname = parts[0] || 'file';
      const blobUrl = parts[1] || '';
      modalLink.style.display = 'none';
      if (modalPdfLink) {
        modalPdfLink.href = blobUrl || '#';
        modalPdfLink.style.display = blobUrl ? 'inline-flex' : 'none';
        const label = cardUrl.startsWith('img://') ? '画像を開く' : 'PDFを開く';
        modalPdfLink.querySelector('#modal-pdf-filename')
          ? (modalPdfLink.childNodes[2].textContent = ` — ${fname}`)
          : null;
        if (modalPdfFilename) modalPdfFilename.textContent = `— ${fname}`;
      }
    } else {
      modalLink.href = cardUrl || '#';
      modalLink.style.display = cardUrl ? 'inline-flex' : 'none';
      if (modalPdfLink) modalPdfLink.style.display = 'none';
    }

    detailModal.classList.add('active');
    document.body.style.overflow = 'hidden'; // Stop scrolling background
  }

  function closeModal() {
    detailModal.classList.remove('active');
    document.body.style.overflow = '';
  }

  // --- Form & Simulation Helpers ---

  // Set random thumbnail from the Unsplash list matching category
  function setRandomThumbnail() {
    const selectedCat = inputCategory.value || "マス＆ビジュアル表現";
    const images = categoryImages[selectedCat] || categoryImages["マス＆ビジュアル表現"];
    const randomUrl = images[Math.floor(Math.random() * images.length)];
    inputThumbnail.value = randomUrl;
  }

  // AI Summary Simulator (Brief, Insight, Solution)
  function generateSimulatedAISummary() {
    const title = inputTitle.value.trim();
    const category = inputCategory.value;
    const rawMemo = inputRawMemo.value.trim();

    if (!title || !category) {
      alert('AI要約を生成するには、まず「見出し」と「カテゴリー」を入力してください。素材メモがあればより詳しく分析できます。');
      return;
    }

    // Show Loader
    aiLoading.style.display = 'flex';
    generateAiBtn.disabled = true;

    // Simulate LLM loading delay
    setTimeout(() => {
      // Heuristic parsing: extract key insights based on categories or memo
      let brief = '';
      let insight = '';
      let approach = '';
      let solution = '';

      // Clean inputs
      const memoText = rawMemo || 'このキャンペーン・プロダクトは非常にユニークです。';

      // Template generation dictionary based on category
      const strategyTemplates = {
        "ブランディング": {
          brief: `競合製品との機能的・価格的な差異化が難しくなる中で、単なる認知（名前を知っている状態）を超え、企業の存在意義（パーパス）に深く共鳴する熱狂的なファン（ブランドパートナー）を育成し、中長期的な愛着とリピート率を高めたい。`,
          insight: `現代の消費者は、製品そのものの良さだけでなく、「その企業が社会をどう良くしようとしているか」「どのような価値観のもとで活動しているか」というストーリーに自分自身を重ね合わせ、そこに自己表現や信頼を見出す。`,
          approach: `ブランドの「信念・パーパス」を前面に打ち出し、製品の機能訴求を脇に置く逆転の発想。消費者が「このブランドを使うこと＝自分の価値観の表明」と感じられるよう、一貫したナラティブで感情的なつながりを構築する。`,
          solution: `${title} を軸にした統合ブランディング施策を展開。一貫したビジュアル・メッセージング（VI、ブランドムービー、特設体験サイト等）を通じて情緒的コミュニケーションを設計し、顧客の心が動く強固なブランドポジションを確立した。`
        },
        "マス＆ビジュアル表現": {
          brief: `競合が似たようなデジタル広告に終始する中、スマートフォンのスクロール操作だけでは伝わらない「身体的・空間的なスケール感」を伝え、ブランドの威厳を確立したい。`,
          insight: `人は日々の通勤や街歩きで無意識のうちに刺激を求めている。圧倒的な美しさや巨大なビジュアル表現は、スマホの画面を超えた「強烈な現実体験」として写真に撮られ、SNSで二次拡散される。`,
          approach: `「デジタルでは再現不可能な体験」を逆手に取り、オフラインのスケールそのものをコンテンツ化する。街を圧倒するビジュアルで驚きを生み、来街者が自発的に撮影・シェアする口コミの起点を設計する。`,
          solution: `${title} の大型ポスター・屋外ビジュアルを展開。デジタル画面では再現できない手触り感や解像度にこだわり、街の一部をジャックするインパクトで話題化と認知拡大を達成した。`
        },
        "テレビCM・WEB動画": {
          brief: `15秒・30秒の短尺広告があふれてスキップされる現代において、製品スペックの羅列ではなく、ターゲットの心に響く強いストーリーテリングで情緒的なファンを獲得したい。`,
          insight: `視聴者は説教くさい広告や押し売りのようなメッセージを嫌うが、誰もが共感できる「人間の本質（弱さ、優しさ、日常の小さな歪み）」を描いたドラマには感情移入し、最後まで見入ってしまう。`,
          approach: `製品を「主役」から「脇役」に降格させ、普遍的な人間ドラマを前面に。視聴者が「自分のことだ」と感じる瞬間にブランドがそっと寄り添う構造で、説得ではなく共鳴によってブランド好意を醸成する。`,
          solution: `${title} という感情豊かなストーリー仕立てのムービーを展開。ブランドの提供価値をさりげなく背景に溶け込ませることで、スキップされずにSNS等で拡散されるブランディング動画を構築した。`
        },
        "パッケージデザイン・装丁": {
          brief: `類似商品が並ぶ店頭の棚で埋もれてしまい、広告費用をかけずに製品自体が放つ魅力だけで購入者の目を惹きつけ、ブランド選定の決め手を作りたい。`,
          insight: `現代の消費者はただ「中身」を買うだけでなく、パッケージを部屋に置いたときの心地よさや、開封時のワクワクする儀式（アンボクシング体験）といった「情緒的価値」にお金を払う。`,
          approach: `パッケージ自体を「広告媒体かつSNSコンテンツ」として設計する。棚で目を奪うだけでなく、開封・使用・処分のすべてのシーンで写真に撮りたくなる仕掛けを仕込み、製品が自ら拡散する構造を作る。`,
          solution: `製品のアイデンティティを体現する ${title} を設計。素材感から開封のステップまで綿密に計算し、購入したことを誰かに自慢したくなるようなデザインと構造に落とし込んだ。`
        },
        "SNS施策・キャンペーン": {
          brief: `企業からの一方的なプレスリリースや広告配信ではタイムライン上で無視されるため、ユーザー自らが自発的に参加し、会話を生み出す自走型キャンペーンを展開したい。`,
          insight: `ユーザーは企業の宣伝を手伝いたくはないが、「自分がツッコミを入れられる隙があるネタ」「自分のセンスやユニークさをフォロワーにアピールできる大義名分」があれば喜んで乗ってくる。`,
          approach: `ブランドが「舞台装置」を用意し、主役はユーザー自身に委ねる参加型フォーマットを設計。企業メッセージを伝えるのではなく、ユーザーが自己表現したくなる「お題」を作ることで自走拡散を生む。`,
          solution: `${title} の仕組みをSNS上でローンチ。ユーザーが気軽にボケたり、自分ならではの回答をハッシュタグと共に投稿したくなる「お題」を設計し、一気にトレンド入りさせる拡散の輪を生み出した。`
        },
        "WEBサイト・UI/UX": {
          brief: `情報量が多すぎるサイト設計では離脱率が高く、商品やブランドのコアイメージを直感的・没入的に体験してもらい、コンバージョンへと誘導する設計が不足していた。`,
          insight: `スクロールやクリックといった「自らの能動的なインタラクション」に対して、小気味よい音や美しいアニメーション（マイクロインタラクション）で反応が返ってくると、脳内に心地よさが生まれ、ゲーム感覚で滞在時間が伸びる。`,
          approach: `情報設計ではなく「体験設計」を起点に据える。ユーザーのスクロールやクリックに世界観で応答するインタラクションを軸に据え、ブランドの世界に没入させながら自然にCTAへ誘導する動線を設計する。`,
          solution: `${title} を実装。3D演出やなめらかな画面遷移を活用し、ブランドの世界観をシームレスかつインタラクティブに冒険できるWebサイトに仕上げ、ユーザーを引き込んだ。`
        },
        "イベント・ポップアップストア": {
          brief: `オンライン上の接点だけでは製品の「肌触り」や「リアルな体験」が伝わらず、強いファン化やメディアによる報道（パブリシティ）が限定的だった。`,
          insight: `人は単にモノを見るだけでなく、「その場所でしかできない五感を使った体験」や「他人と共有できる思い出の空間」に価値を感じる。特に限定的なイベントは希少性からプレミアム感が生まれる。`,
          approach: `「今ここにしかない体験」を設計し、ブランドとの記憶を身体に刻む。来場者が写真を撮らずにはいられない仕掛けを随所に配置し、会場の外へ口コミが広がるメディア化した空間を作る。`,
          solution: `ブランドの世界観を立体的に体験できる ${title} を企画・運営。写真映えする内装や体験型アトラクションを設け、来場者が自発的に拡散し、メディアがニュースとして取り上げる仕掛けを作った。`
        },
        "インストア・販促プロモーション": {
          brief: `ECの台頭により店舗への来店動機が薄れる中、店頭での購買意思決定（ラストワンマイル）の瞬間にアプローチし、他社製品ではなく自社製品をカゴに入れる決定打が欠けていた。`,
          insight: `消費者は購入時に「失敗したくない」と警戒しているが、店頭で「今だけお得」「偶然面白いモノを見つけた」という宝探しのような体験があると、衝動買いや非日常の購買へのハードルが下がる。`,
          approach: `購買の「最後の1メートル」を制する什器・POPを起点に、店頭体験そのものをプロモーションメディア化。「なぜ今買うべきか」が一瞬で伝わる訴求と希少性演出で、迷いを決断に変換する。`,
          solution: `思わず足を止める什器とPOPを組み合わせた ${title} を展開。その場で購入する明快なインセンティブと目を引くデザインで、来店者の最後の一歩を後押しする購買体験を設計した。`
        },
        "空間デザイン・環境演出": {
          brief: `オフィスや商業施設において、単なる通路や空間としての機能に留まり、ブランドの思想を五感で感じさせるシンボリックな体験やメッセージ性が弱い。`,
          insight: `物理的な空間スケール、音、光、温度の変化は、視覚だけの情報（デジタル画面）に比べて脳に直接作用し、その場所にいた記憶を長期間にわたって感情に結びつけやすい。`,
          approach: `空間を「ブランドの思想を歩いて体験できる物語」として再設計する。入口から出口まで動線をナラティブで貫き、歩を進めるごとにブランドの世界観への没入が深まる体験設計を行う。`,
          solution: `テクノロジーとアートを融合させた ${title} を設計。空間全体を使って物語を表現することで、訪問者が歩みを進めるごとにブランドの理念を体感できるドラマチックな環境を構築した。`
        },
        "PR・ソーシャルグッド（SDGs）": {
          brief: `企業の社会貢献活動（CSR）は真面目すぎてニュースになりにくく、また生活者にとっても「自分事」として捉えられず、共感や具体的なアクションにつながりにくい。`,
          insight: `お説教のような環境・社会保護のメッセージは耳を素通りするが、「クリエイティブなアイデアで解決へのアプローチが楽しくデザインされている」のを見ると、賢い選択として自発的に協力したくなる。`,
          approach: `社会課題解決をエンターテインメントとして設計し、参加すること自体を報酬にする。ユーザーの行動変容を「お願い」ではなく「楽しい選択肢」として提示し、善意をムーブメントに変える。`,
          solution: `社会課題をエンターテインメントや革新的なアイデアに昇華させた ${title} を発表。単なる啓発活動に留まらず、一般消費者が参加すること自体が社会貢献になるエコシステムを設計し、大きなパブリシティを獲得した。`
        },
        "ゲリラマーケティング": {
          brief: `予算が限られる中、大手の物量広告に対抗するために、日常の何気ない瞬間に強烈な驚きをもたらし、バズやクチコミで一気に拡散させる戦術が必要だった。`,
          insight: `人はいつもの日常風景（駅、道路、街並み）に「ちょっとした異物」が混入していると、強烈な違和感から足を止め、すぐに写真を撮って「何これ！」とSNSに投稿したくなる。`,
          approach: `広告費ゼロで「ニュース」を作る。街や公共空間を文脈ごとハックし、「なぜここに？」という違和感と驚きでメディアとSNSが自発的に拡散する事件を起こす。小さな介入で最大の波紋を生む。`,
          solution: `日常のインフラや街の空間をハックする ${title} をゲリラ的に展開。事前告知なしで驚きを提供し、SNSやメディアが勝手に取り上げて拡散する「波及効果」の最大化を図った。`
        },
        "AI・最新テック活用": {
          brief: `デジタル化が進み、万人向けの画一的な広告メッセージではユーザーの心が動かなくなっており、個人個人のコンテクストに合わせた超精密なアプローチが求められていた。`,
          insight: `ユーザーは大量の無駄な広告には拒絶反応を示すが、「今の自分の気分や状況に完璧に合致したパーソナライズ情報」であれば、驚きと共に特別な体験として受け入れる。`,
          approach: `テクノロジーを「精度向上ツール」ではなく「体験創造エンジン」として活用する。ユーザーのリアルタイムな文脈をAIが解釈し、その瞬間にしか存在しないパーソナライズされた表現を生成する体験設計を行う。`,
          solution: `最新のテクノロジーを活用した ${title} をローンチ。ユーザーのリアルタイムな感情や入力データをもとにAIが瞬時にパーソナライズされた表現を創り出し、双方向性のある新しい広告体験を提供した。`
        },
        "メタバース・ゲーム内施策": {
          brief: `若年層（Z世代・α世代）のテレビ離れやSNS広告への忌避感が強まる中、彼らが毎日の余暇を過ごす3D仮想空間（メタバース）のコミュニティにシームレスに入り込む必要があった。`,
          insight: `若年層は「見る広告」には反応しないが、自分自身のアバターを着飾ったり、ゲーム内で友達と集まって遊ぶ「体験の一部」としてブランドのアイテムやワールドが提供されれば、ごく自然に受け入れ楽しむ。`,
          approach: `広告枠を買うのではなく、ゲームの「コンテンツそのもの」になる。ブランド世界観をゲームの語法で翻訳し、ユーザーが遊ぶ中で自然にブランドへの親密度が高まる体験を設計する。`,
          solution: `FortniteやRobloxといったプラットフォーム上に ${title} を展開。ブランドをテーマにした独自のミニゲームやアバター用デジタルアイテムを提供し、ゲーム体験を通じてブランドと深くエンゲージメントを結ぶ機会を創出した。`
        }
      };

      // Extract template
      const template = strategyTemplates[category] || strategyTemplates["マス＆ビジュアル表現"];

      // Mix with user inputs if raw memo has details
      brief = template.brief;
      insight = template.insight;
      approach = template.approach;
      solution = template.solution;

      if (rawMemo.length > 15) {
        brief = `【原資の課題】${rawMemo.substring(0, 100)}...\n\n上記に基づき、${template.brief}`;
        insight = `【分析】${template.insight}\n（メモの要素「${rawMemo.substring(10, 30)}...」から、ユーザーが求める体験・本音を抽出）`;
        solution = `【実行】${title}を活用し、${rawMemo.substring(Math.max(0, rawMemo.length - 80))} を実装。${template.solution}`;
      }

      // Populate textareas
      inputBrief.value = brief;
      inputInsight.value = insight;
      inputApproach.value = approach;
      inputSolution.value = solution;

      // Hide Loader & Restore
      aiLoading.style.display = 'none';
      generateAiBtn.disabled = false;
    }, 1500);
  }

  // Handle form submission (add or edit)
  function handleFormSubmit(e) {
    e.preventDefault();

    const title = inputTitle.value.trim();
    const category = inputCategory.value;
    const industry = inputIndustry.value;
    const url = inputUrl.value.trim();
    const submitter = inputSubmitter.value.trim();
    let thumbnail = inputThumbnail.value.trim();
    const brief = inputBrief.value.trim();
    const insight = inputInsight.value.trim();
    const approach = inputApproach.value.trim();
    const solution = inputSolution.value.trim();
    const keywords = inputKeywords.value.trim();
    const userMemo = inputUserMemo ? inputUserMemo.value.trim() : '';

    if (!title || !category || !industry || !url || !submitter || !brief || !insight || !approach || !solution) {
      alert('必須項目（*）を入力し、Brief / Insight / Approach / Solution の構成を作成してください。');
      return;
    }

    if (!thumbnail) {
      const themeList = categoryImages[category] || categoryImages["マス＆ビジュアル表現"];
      thumbnail = themeList[Math.floor(Math.random() * themeList.length)];
    }

    const editId = parseInt(editCardIdInput.value);

    if (editId) {
      // --- 編集モード: 既存カードを更新 ---
      const idx = creativeCards.findIndex(c => c.id === editId);
      if (idx !== -1) {
        creativeCards[idx] = { ...creativeCards[idx], title, category, industry, brief, insight, approach, solution, keywords, userMemo, url, thumbnail, submitter };
      }
      saveDataToLocal();
      resetEditMode();
      switchMode('viewer');
      setTimeout(() => cardsGridContainer.scrollIntoView({ behavior: 'smooth' }), 200);
      alert(`事例「${title}」を更新しました！`);
    } else {
      // --- 追加モード: 新規カードを追加 ---
      const newId = creativeCards.length > 0 ? Math.max(...creativeCards.map(c => c.id)) + 1 : 1;
      const today = new Date().toISOString().split('T')[0];
      creativeCards.push({ id: newId, title, category, industry, brief, insight, approach, solution, keywords, userMemo, url, thumbnail, submitter, createdAt: today });
      saveDataToLocal();
      addCardForm.reset();
      switchMode('viewer');
      setTimeout(() => cardsGridContainer.scrollIntoView({ behavior: 'smooth' }), 200);
      alert(`事例「${title}」をデータベースに追加しました！`);
    }
  }

  function editCard(card) {
    switchMode('admin');
    editCardIdInput.value = card.id;
    inputTitle.value = card.title || '';
    inputCategory.value = card.category || '';
    inputIndustry.value = card.industry || '';
    // PDF/画像URLの場合はURL欄に表示しない（PDFタブに切り替え）
    if ((card.url || '').startsWith('pdf://') || (card.url || '').startsWith('img://')) {
      inputUrl.value = card.url || '';
      // PDFタブに切り替え
      sourceTabs.forEach(t => t.classList.remove('active'));
      document.querySelector('[data-tab="pdf"]')?.classList.add('active');
      sourceUrlSection.style.display = 'none';
      sourcePdfSection.style.display = '';
      const fname = card.url.replace(/^(pdf|img):\/\//, '').split('||')[0];
      if (pdfFilenameDisplay) pdfFilenameDisplay.textContent = fname;
      if (pdfUploadPlaceholder) pdfUploadPlaceholder.style.display = 'none';
      if (pdfSelectedInfo) pdfSelectedInfo.style.display = 'flex';
    } else {
      inputUrl.value = card.url || '';
    }
    inputThumbnail.value = card.thumbnail || '';
    inputSubmitter.value = card.submitter || '';
    inputBrief.value = card.brief || '';
    inputInsight.value = card.insight || '';
    inputApproach.value = card.approach || '';
    inputSolution.value = card.solution || '';
    inputKeywords.value = card.keywords || '';
    if (inputUserMemo) inputUserMemo.value = card.userMemo || '';

    formSubmitBtn.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
      この事例を更新する
    `;
    cancelEditBtn.style.display = 'inline-flex';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function resetEditMode() {
    editCardIdInput.value = '';
    addCardForm.reset();
    formSubmitBtn.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
      事例データベースに追加する
    `;
    cancelEditBtn.style.display = 'none';
    setUrlStatus('idle');
  }

  // --- JSON File download & Clipboard Utilities ---

  // Export current list to json file for project override
  function downloadJSONFile() {
    // Generate clean copy (excluding any frontend-specific dynamic state if any)
    const jsonString = JSON.stringify(creativeCards, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'data.json';
    document.body.appendChild(a);
    a.click();
    
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Copy json code to clipboard
  function copyJSONToClipboard() {
    const jsonString = JSON.stringify(creativeCards, null, 2);
    
    navigator.clipboard.writeText(jsonString).then(() => {
      const originalText = copyJsonBtn.innerHTML;
      copyJsonBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
        コピーしました！
      `;
      copyJsonBtn.style.background = 'rgba(16, 185, 129, 0.2)';
      copyJsonBtn.style.color = '#34d399';
      copyJsonBtn.style.borderColor = 'rgba(16, 185, 129, 0.4)';
      
      setTimeout(() => {
        copyJsonBtn.innerHTML = originalText;
        copyJsonBtn.style.background = '';
        copyJsonBtn.style.color = '';
        copyJsonBtn.style.borderColor = '';
      }, 2000);
    }).catch(err => {
      console.error('Could not copy JSON: ', err);
      alert('コピーに失敗しました。お使いのブラウザの設定を確認してください。');
    });
  }

  // --- Keyword Tag Input ---

  function addKeyword(word) {
    if (!word || keywords.includes(word)) { keywordInput.value = ''; return; }
    keywords.push(word);
    keywordInput.value = '';
    renderKeywordTags();
    searchKeywordsBtn.disabled = false;
  }

  function removeKeyword(word) {
    keywords = keywords.filter(k => k !== word);
    renderKeywordTags();
    searchKeywordsBtn.disabled = keywords.length === 0;
    if (keywords.length === 0) {
      searchResultsPanel.style.display = 'none';
      setSearchStatus('idle');
    }
  }

  function renderKeywordTags() {
    keywordTagsEl.innerHTML = keywords.map(k => `
      <span class="keyword-tag">
        ${k}
        <button type="button" class="keyword-tag-remove" data-keyword="${k}">&times;</button>
      </span>
    `).join('');
    keywordTagsEl.querySelectorAll('.keyword-tag-remove').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        removeKeyword(btn.dataset.keyword);
      });
    });
    // inputのplaceholderを消す
    keywordInput.placeholder = keywords.length > 0 ? '' : '例: Nike、SNSキャンペーン、2024 ／ Enterで追加';
  }

  async function searchByKeywords() {
    const category = inputCategory.value || '';
    const industry = inputIndustry.value || '';
    const userMemo = inputUserMemo ? inputUserMemo.value.trim() : '';
    setSearchStatus('loading', 'ネット検索中・AI分析中...');
    searchKeywordsBtn.disabled = true;

    try {
      const res = await fetch(`${API_BASE}/api/search-keywords`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keywords, category, industry, user_memo: userMemo }),
      });
      const data = await res.json();

      if (data.success) {
        // フォームに自動入力
        if (data.title) inputTitle.value = data.title;
        if (data.url) inputUrl.value = data.url;
        if (data.thumbnail) inputThumbnail.value = data.thumbnail;
        if (data.category && !inputCategory.value) inputCategory.value = data.category;
        if (data.industry && !inputIndustry.value) inputIndustry.value = data.industry;
        if (data.brief) inputBrief.value = data.brief;
        if (data.insight) inputInsight.value = data.insight;
        if (data.approach) inputApproach.value = data.approach;
        if (data.solution) inputSolution.value = data.solution;

        // 参考記事一覧を表示
        renderSearchResults(data.articles || []);
        setSearchStatus('success', `${data.articles?.length || 0}件の記事を収集・分析しました。内容を確認・編集してください。`);
      } else {
        setSearchStatus('error', data.error || '検索に失敗しました');
      }
    } catch {
      setSearchStatus('error', 'AIサーバーに接続できません。' + (API_BASE ? 'python server.py を起動してください。' : 'しばらくしてから再試行してください。'));
    }

    searchKeywordsBtn.disabled = false;
  }

  function renderSearchResults(articles) {
    if (!articles.length) { searchResultsPanel.style.display = 'none'; return; }
    searchResultsList.innerHTML = articles.map((a, i) => `
      <div class="search-result-item ${i === 0 ? 'primary' : ''}" data-url="${a.url}">
        <div class="result-meta">
          ${i === 0 ? '<span class="result-primary-badge">メイン参照</span>' : ''}
          <a href="${a.url}" target="_blank" class="result-title">${a.title}</a>
        </div>
        <p class="result-snippet">${a.snippet?.substring(0, 120)}...</p>
        <button type="button" class="result-use-btn" data-url="${a.url}" data-title="${a.title.replace(/"/g, '&quot;')}">
          この記事をメインに設定
        </button>
      </div>
    `).join('');

    // 「この記事をメインに設定」クリック
    searchResultsList.querySelectorAll('.result-use-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        inputUrl.value = btn.dataset.url;
        inputTitle.value = btn.dataset.title;
        // アクティブ表示を切り替え
        searchResultsList.querySelectorAll('.search-result-item').forEach(el => el.classList.remove('primary'));
        btn.closest('.search-result-item').classList.add('primary');
        btn.closest('.search-result-item').querySelector('.result-meta').insertAdjacentHTML('afterbegin',
          '<span class="result-primary-badge">メイン参照</span>');
      });
    });

    searchResultsPanel.style.display = 'block';
  }

  function setSearchStatus(state, message = '') {
    if (state === 'idle') { searchStatusEl.style.display = 'none'; return; }
    searchStatusEl.className = `url-status url-status-${state}`;
    searchStatusEl.textContent = message;
    searchStatusEl.style.display = 'flex';
  }

  // --- PDF Upload & Analyze ---

  function handlePdfSelect(file) {
    currentPdfFile = file;
    pdfUploadPlaceholder.style.display = 'none';
    pdfSelectedInfo.style.display = 'flex';
    pdfFilenameDisplay.textContent = file.name;
    setPdfStatus('idle');
    // ファイル選択後に自動解析
    analyzePdf(file);
  }

  function setPdfStatus(state, message = '') {
    if (state === 'idle') { pdfStatusEl.style.display = 'none'; return; }
    pdfStatusEl.className = `url-status url-status-${state}`;
    pdfStatusEl.textContent = message;
    pdfStatusEl.style.display = 'flex';
  }

  async function analyzePdf(file) {
    if (!file) return;
    const category = inputCategory.value || '';
    const title = inputTitle.value.trim();
    const kws = inputKeywords.value.trim();
    const userMemo = inputUserMemo ? inputUserMemo.value.trim() : '';

    const isImage = file.type.startsWith('image/');
    setPdfStatus('loading', `${isImage ? '画像' : 'PDF'}を読み込んでAI解析中...`);
    if (pdfAnalyzeBtn) pdfAnalyzeBtn.disabled = true;

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', category);
      formData.append('title', title);
      formData.append('keywords', kws);
      formData.append('user_memo', userMemo);

      const res = await fetch(`${API_BASE}/api/analyze-pdf`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (data.success) {
        if (data.title && !inputTitle.value) inputTitle.value = data.title;
        if (data.category && !inputCategory.value) inputCategory.value = data.category;
        if (data.industry && !inputIndustry.value) inputIndustry.value = data.industry;
        if (data.brief) inputBrief.value = data.brief;
        if (data.insight) inputInsight.value = data.insight;
        if (data.approach) inputApproach.value = data.approach;
        if (data.solution) inputSolution.value = data.solution;

        // BlobURLを生成してURLフィールドに設定（pdf:// or img:// プレフィックスでファイル名も保持）
        const blobUrl = URL.createObjectURL(file);
        const prefix = file.type === 'application/pdf' ? 'pdf' : 'img';
        inputUrl.value = `${prefix}://${file.name}||${blobUrl}`;

        setPdfStatus('success', `「${data.title || file.name}」の解析が完了しました。内容を確認してください。`);
        setTimeout(() => setPdfStatus('idle'), 5000);
      } else {
        setPdfStatus('error', data.error || 'PDF解析に失敗しました');
      }
    } catch {
      setPdfStatus('error', 'サーバーに接続できません。');
    }
    if (pdfAnalyzeBtn) pdfAnalyzeBtn.disabled = false;
  }

  // --- URL Auto-Analyze ---

  async function autoAnalyzeUrl(url) {
    const category = inputCategory.value || '';
    const title = inputTitle.value.trim();
    const kws = inputKeywords.value.trim()
      ? inputKeywords.value.split(',').map(s => s.trim()).filter(Boolean)
      : [];
    const userMemo = inputUserMemo ? inputUserMemo.value.trim() : '';
    setUrlStatus('loading', '記事を取得・AI分析中...');
    analyzeUrlBtn.disabled = true;

    try {
      const res = await fetch(`${API_BASE}/api/analyze-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, category, title, keywords: kws, user_memo: userMemo }),
      });
      const data = await res.json();

      if (data.success) {
        if (data.title && !inputTitle.value) inputTitle.value = data.title;
        if (data.thumbnail && !inputThumbnail.value) inputThumbnail.value = data.thumbnail;
        if (data.category && !inputCategory.value) inputCategory.value = data.category;
        if (data.industry && !inputIndustry.value) inputIndustry.value = data.industry;
        if (data.brief) inputBrief.value = data.brief;
        if (data.insight) inputInsight.value = data.insight;
        if (data.approach) inputApproach.value = data.approach;
        if (data.solution) inputSolution.value = data.solution;
        setUrlStatus('success', '記事情報を自動入力しました。内容を確認・編集してください。');
        setTimeout(() => setUrlStatus('idle'), 4000);
      } else {
        setUrlStatus('error', data.error || 'URLの取得に失敗しました');
      }
    } catch {
      setUrlStatus('error', 'AIサーバーに接続できません。' + (API_BASE ? 'ターミナルで python server.py を起動してください。' : 'しばらくしてから再試行してください。'));
    }

    analyzeUrlBtn.disabled = false;
  }

  function setUrlStatus(state, message = '') {
    if (state === 'idle') {
      urlStatusEl.style.display = 'none';
      return;
    }
    urlStatusEl.className = `url-status url-status-${state}`;
    urlStatusEl.textContent = message;
    urlStatusEl.style.display = 'flex';
  }

  // --- TSV Bulk Import (from Google Sheets copy-paste) ---

  // スプレッドシートコピー時の引用符付きフィールド（セル内改行含む）を正しく解析
  function parseTsvRows(rawText) {
    const rows = [];
    let row = [];
    let field = '';
    let inQuotes = false;
    const text = rawText.replace(/\r\n/g, '\n') + '\n';

    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      if (inQuotes) {
        if (ch === '"') {
          if (text[i + 1] === '"') { field += '"'; i++; }
          else inQuotes = false;
        } else {
          // セル内の改行はスペースに変換
          field += (ch === '\n') ? ' ' : ch;
        }
      } else {
        if (ch === '"') {
          inQuotes = true;
        } else if (ch === '\t') {
          row.push(field.trim());
          field = '';
        } else if (ch === '\n') {
          row.push(field.trim());
          field = '';
          if (row.some(f => f)) rows.push(row);
          row = [];
        } else {
          field += ch;
        }
      }
    }
    return rows;
  }

  function parseTsv(rawText) {
    const rows = parseTsvRows(rawText);
    const cards = [];
    const today = new Date().toISOString().split('T')[0];
    let nextId = creativeCards.length > 0 ? Math.max(...creativeCards.map(c => c.id)) + 1 : 1;

    for (const cols of rows) {
      if (!cols.length) continue;

      // ヘッダー行をスキップ
      if (
        cols[0].includes('タイムスタンプ') || cols[0].toLowerCase().includes('timestamp') ||
        cols[0].includes('情報提供者') || cols[0].includes('施策タイプ') || cols[0].includes('タイトル')
      ) continue;

      // タイムスタンプ列を自動検出してスキップ
      let i = 0;
      if (cols[0].match(/^\d{4}[\/\-]\d{2}[\/\-]\d{2}/)) i = 1;

      const remaining = cols.slice(i);
      if (!remaining.length) continue;

      // 最小フォーマット（3列以下）: 情報提供者 | タイトル | URL → AIで補完
      if (remaining.length <= 3) {
        const [submitter = '', title = '', url = ''] = remaining;
        if (!title && !url) continue;
        cards.push({
          id: nextId++,
          title: title.trim(), url: url.trim(), submitter: submitter.trim(),
          category: '', industry: '', brief: '', insight: '', approach: '', solution: '', keywords: '', thumbnail: '',
          createdAt: today, _needsAI: true,
        });
      } else {
        // フルフォーマット（11列）
        const [submitter = '', category = '', industry = '', title = '', url = '',
               brief = '', insight = '', approach = '', solution = '', thumbnail = '', keywords = ''] = remaining;
        if (!title && !url) continue;
        cards.push({
          id: nextId++,
          title, category, industry, brief, insight, approach, solution, keywords,
          url, thumbnail, submitter, createdAt: today,
        });
      }
    }
    return cards;
  }

  function previewTsvImport(rawText) {
    if (!rawText.trim()) {
      importPreview.style.display = 'none';
      importAiBtn.style.display = 'none';
      importTsvBtn.style.display = 'none';
      _pendingImportCards = [];
      return;
    }
    const cards = parseTsv(rawText);
    _pendingImportCards = cards;

    if (!cards.length) {
      importPreview.innerHTML = '<p class="import-preview-empty">有効なデータ行が見つかりませんでした。列の順番を確認してください。</p>';
      importPreview.style.display = 'block';
      importAiBtn.style.display = 'none';
      importTsvBtn.style.display = 'none';
      return;
    }

    const hasNeedsAI = cards.some(c => c._needsAI);

    if (hasNeedsAI) {
      importPreview.innerHTML = `
        <p class="import-preview-count">${cards.length}件を検出 — AIが自動補完します</p>
        ${cards.map(c => `
          <div class="import-preview-row">
            <span class="import-preview-title">${c.title || '(タイトルなし)'}</span>
            <span class="import-preview-meta import-preview-url">${c.url || '—'}</span>
            <span class="import-preview-ai-badge">AI補完待ち</span>
          </div>
        `).join('')}
      `;
      importAiBtn.style.display = 'flex';
      importTsvBtn.style.display = 'none';
    } else {
      importPreview.innerHTML = `
        <p class="import-preview-count">${cards.length}件のデータを検出</p>
        ${cards.map(c => `
          <div class="import-preview-row">
            <span class="import-preview-title">${c.title || '(タイトルなし)'}</span>
            <span class="import-preview-meta">${c.category} / ${c.industry} — ${c.submitter}</span>
          </div>
        `).join('')}
      `;
      importAiBtn.style.display = 'none';
      importTsvBtn.style.display = 'flex';
    }
    importPreview.style.display = 'block';
  }

  async function batchAnalyzeAndImport(cards) {
    if (!cards.length) return;
    importAiBtn.disabled = true;
    importAiProgress.style.display = 'block';
    importAiProgress.innerHTML = `
      <div class="ai-progress-spinner"></div>
      <span class="ai-progress-text">AIが ${cards.length} 件を分析中...</span>
    `;

    try {
      const items = cards.map(c => ({
        submitter: c.submitter,
        title: c.title,
        url: c.url,
        keywords: c.keywords ? c.keywords.split(',').map(s => s.trim()).filter(Boolean) : [],
        user_memo: c.userMemo || '',
      }));
      const res = await fetch(`${API_BASE}/api/batch-analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items }),
      });
      const data = await res.json();

      const today = new Date().toISOString().split('T')[0];
      let nextId = creativeCards.length > 0 ? Math.max(...creativeCards.map(c => c.id)) + 1 : 1;
      const results = data.results.map((r, idx) => {
        const orig = cards[idx];
        if (r.success) {
          return {
            id: orig.id,
            submitter: r.submitter,
            title: r.title || orig.title,
            url: r.url,
            category: r.category,
            industry: r.industry,
            brief: r.brief,
            insight: r.insight,
            approach: r.approach || '',
            solution: r.solution,
            keywords: r.keywords || '',
            userMemo: orig.userMemo || '',
            thumbnail: r.thumbnail || '',
            createdAt: orig.createdAt || today,
          };
        }
        return {
          id: orig.id,
          submitter: orig.submitter,
          title: orig.title,
          url: orig.url,
          category: '', industry: '', brief: '', insight: '', approach: '', solution: '', keywords: '', thumbnail: '',
          createdAt: orig.createdAt || today,
        };
      });

      const successCount = data.results.filter(r => r.success).length;
      importAiProgress.innerHTML = `<span class="ai-progress-done">✓ AI分析完了（${successCount}/${cards.length} 件成功）</span>`;

      await new Promise(r => setTimeout(r, 1200));

      creativeCards.push(...results);
      saveDataToLocal();
      importTsvInput.value = '';
      importPreview.style.display = 'none';
      importAiProgress.style.display = 'none';
      importAiBtn.style.display = 'none';
      importAiBtn.disabled = false;
      _pendingImportCards = [];
      switchMode('viewer');
      setTimeout(() => cardsGridContainer.scrollIntoView({ behavior: 'smooth' }), 200);
    } catch {
      importAiProgress.innerHTML = `<span class="ai-progress-error">⚠️ AI分析に失敗しました。サーバーが起動しているか確認してください（python server.py）。</span>`;
      importAiBtn.disabled = false;
    }
  }

  function executeTsvImport(rawText) {
    const cards = parseTsv(rawText).filter(c => !c._needsAI);
    if (!cards.length) { alert('インポートできるデータがありません。'); return; }
    if (!confirm(`${cards.length}件の事例をインポートします。よろしいですか？`)) return;

    creativeCards.push(...cards);
    saveDataToLocal();
    importTsvInput.value = '';
    importPreview.style.display = 'none';
    importTsvBtn.style.display = 'none';
    _pendingImportCards = [];
    switchMode('viewer');
    setTimeout(() => cardsGridContainer.scrollIntoView({ behavior: 'smooth' }), 200);
    alert(`${cards.length}件の事例をインポートしました！`);
  }

  function downloadImportTemplate() {
    const headers = ['情報提供者', 'タイトル（施策名・事例名）', '記事URL'];
    const example = [
      '山田太郎',
      'ブランド名 × キャンペーン名（例: Nike × Just Do It 2024）',
      'https://example.com/article',
    ];

    const BOM = '﻿';
    const csvContent = BOM
      + headers.map(h => `"${h}"`).join(',') + '\n'
      + example.map(v => `"${v}"`).join(',') + '\n';

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'creative-depot-template.csv';
    a.click();
    URL.revokeObjectURL(url);
  }

  // Reset local changes and fetch data.json again
  async function resetToOriginalData() {
    if (!confirm('ローカルで追加したすべての情報がリセットされ、data.jsonファイルの初期データに戻ります。よろしいですか？')) {
      return;
    }

    localStorage.removeItem('creative_hub_data');
    
    // Fetch data.json again
    try {
      const response = await fetch('data.json');
      if (!response.ok) throw new Error('Data file not found');
      creativeCards = await response.json();
      saveDataToLocal();
      renderCards();
      alert('データを初期状態にリセットしました。');
      switchMode('viewer');
    } catch (error) {
      console.error('Error resetting data:', error);
      creativeCards = [];
      saveDataToLocal();
      renderCards();
      alert('データの初期化に失敗しました。データが空になりました。');
    }
  }

});
