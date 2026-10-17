const CHART_COLORS = [
  'rgba(88, 166, 255, 0.85)',   // blue
  'rgba(163, 113, 247, 0.85)',  // purple
  'rgba(63, 185, 80, 0.85)',    // green
  'rgba(210, 153, 34, 0.85)',   // yellow
  'rgba(248, 81, 73, 0.85)',    // red
];

let data = null;
let radarChart = null;
let selectedModels = new Set();
let sortColumn = 'arena_elo';
let sortAsc = false;

async function init() {
  const resp = await fetch('data/benchmarks.json');
  data = await resp.json();

  document.getElementById('lastUpdated').textContent = `最終更新: ${data.lastUpdated}`;

  renderBenchmarkCards();
  initModelToggles();
  renderTable();
  renderRadarChart();
}

function renderBenchmarkCards() {
  const container = document.getElementById('benchmarkCards');
  container.innerHTML = data.benchmarks.map(b => `
    <div class="card">
      <div class="card-category">${b.category}</div>
      <div class="card-title">${b.name}</div>
      <div class="card-desc">${b.description}</div>
    </div>
  `).join('');
}

function initModelToggles() {
  // Select top 3 by default
  const sorted = [...data.models].sort((a, b) => (b.scores.arena_elo || 0) - (a.scores.arena_elo || 0));
  sorted.slice(0, 3).forEach(m => selectedModels.add(m.name));

  const container = document.getElementById('modelToggles');
  data.models.forEach((model, i) => {
    const btn = document.createElement('button');
    btn.className = `model-toggle${selectedModels.has(model.name) ? ' active' : ''}`;
    const colorIdx = i % CHART_COLORS.length;
    const color = CHART_COLORS[colorIdx];
    btn.innerHTML = `<span class="dot" style="background:${color}"></span>${model.name}`;
    btn.addEventListener('click', () => toggleModel(model.name, btn));
    container.appendChild(btn);
  });
}

function toggleModel(name, btn) {
  if (selectedModels.has(name)) {
    selectedModels.delete(name);
    btn.classList.remove('active');
  } else {
    if (selectedModels.size >= 5) return; // max 5
    selectedModels.add(name);
    btn.classList.add('active');
  }
  renderRadarChart();
}

function renderRadarChart() {
  const ctx = document.getElementById('radarChart').getContext('2d');

  if (radarChart) radarChart.destroy();

  const labels = data.benchmarks.map(b => b.name);
  const datasets = [];

  // We need to normalize scores for the radar chart
  // ELO is on a different scale, so normalize all to 0-100
  const benchmarkIds = data.benchmarks.map(b => b.id);
  const ranges = {};

  benchmarkIds.forEach(id => {
    const scores = data.models.map(m => m.scores[id] || 0);
    ranges[id] = { min: Math.min(...scores), max: Math.max(...scores) };
  });

  let colorIdx = 0;
  data.models.forEach((model, i) => {
    if (!selectedModels.has(model.name)) return;
    const color = CHART_COLORS[colorIdx % CHART_COLORS.length];
    const bgColor = color.replace('0.85', '0.15');
    colorIdx++;

    const normalized = benchmarkIds.map(id => {
      const score = model.scores[id] || 0;
      const r = ranges[id];
      if (r.max === r.min) return 50;
      // Normalize to 20-100 range to keep chart readable
      return 20 + ((score - r.min) / (r.max - r.min)) * 80;
    });

    datasets.push({
      label: model.name,
      data: normalized,
      borderColor: color,
      backgroundColor: bgColor,
      borderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6,
    });
  });

  radarChart = new Chart(ctx, {
    type: 'radar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        r: {
          beginAtZero: false,
          min: 0,
          max: 100,
          ticks: {
            stepSize: 20,
            color: '#8b949e',
            backdropColor: 'transparent',
            font: { size: 10 },
          },
          grid: { color: 'rgba(48, 54, 61, 0.8)' },
          angleLines: { color: 'rgba(48, 54, 61, 0.8)' },
          pointLabels: {
            color: '#e6edf3',
            font: { size: 11 },
          },
        },
      },
      plugins: {
        legend: {
          labels: {
            color: '#e6edf3',
            font: { size: 12 },
            padding: 16,
          },
        },
        tooltip: {
          callbacks: {
            label: function(ctx) {
              // Show actual score instead of normalized
              const modelName = ctx.dataset.label;
              const benchmarkId = data.benchmarks[ctx.dataIndex].id;
              const model = data.models.find(m => m.name === modelName);
              const actual = model.scores[benchmarkId];
              return `${modelName}: ${actual}`;
            }
          }
        }
      },
    },
  });
}

function renderTable() {
  renderTableHeader();
  renderTableBody();
}

function renderTableHeader() {
  const tr = document.getElementById('tableHeader');
  const cols = [
    { key: 'rank', label: '#' },
    { key: 'name', label: 'Series' },
    { key: 'variant', label: 'Model' },
    ...data.benchmarks.map(b => ({ key: b.id, label: b.name })),
  ];

  tr.innerHTML = cols.map(col => {
    let cls = '';
    if (col.key === sortColumn) {
      cls = sortAsc ? 'sorted-asc' : 'sorted-desc';
    }
    return `<th class="${cls}" data-col="${col.key}">${col.label}</th>`;
  }).join('');

  tr.querySelectorAll('th').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.col;
      if (col === 'rank') return;
      if (sortColumn === col) {
        sortAsc = !sortAsc;
      } else {
        sortColumn = col;
        sortAsc = col === 'name'; // alpha asc, scores desc
      }
      renderTable();
    });
  });
}

function renderTableBody() {
  const tbody = document.getElementById('tableBody');

  // Find best score for each benchmark
  const bestScores = {};
  data.benchmarks.forEach(b => {
    bestScores[b.id] = Math.max(...data.models.map(m => m.scores[b.id] || 0));
  });

  // Sort models
  const sorted = [...data.models].sort((a, b) => {
    if (sortColumn === 'name' || sortColumn === 'variant') {
      const aVal = sortColumn === 'variant' ? (a.arenaVariant || '') : a.name;
      const bVal = sortColumn === 'variant' ? (b.arenaVariant || '') : b.name;
      return sortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    const aVal = a.scores[sortColumn] || 0;
    const bVal = b.scores[sortColumn] || 0;
    return sortAsc ? aVal - bVal : bVal - aVal;
  });

  tbody.innerHTML = sorted.map((model, i) => {
    const rank = i + 1;
    const rankClass = rank <= 3 ? `rank-${rank}` : '';
    const scoreCells = data.benchmarks.map(b => {
      const score = model.scores[b.id];
      const isBest = score === bestScores[b.id];
      return `<td class="score-cell${isBest ? ' score-best' : ''}">${score != null ? score : '-'}</td>`;
    }).join('');

    return `<tr>
      <td class="rank-cell ${rankClass}">${rank}</td>
      <td class="model-name">${model.name}<span class="provider-badge">${model.provider}</span></td>
      <td class="variant-cell">${model.arenaVariant || '-'}</td>
      ${scoreCells}
    </tr>`;
  }).join('');
}

init();
