import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { 
  getAuth, 
  onAuthStateChanged,
  signOut
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";

// --- FIREBASE CONFIG ---
const firebaseConfig = {
  apiKey: "AIzaSyBXp2SKVdVdOjbX1Qu8PoIQRskuO0IJIwo",
  authDomain: "news-through-time-53bd9.firebaseapp.com",
  projectId: "news-through-time-53bd9",
  storageBucket: "news-through-time-53bd9.firebasestorage.app",
  messagingSenderId: "41214440361",
  appId: "1:41214440361:web:779495e0afda89bbc4cab8",
  measurementId: "G-62FN2JD1Q7"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// --- CONFIGURAÇÃO GITHUB ---
const GITHUB_USER = "GabryelAquiles";
const GITHUB_REPO = "News-Through-Time";

// --- ELEMENTOS DO DOM ---
const userPhoto = document.getElementById('user-photo');
const userName = document.getElementById('user-name');
const userProfileBtn = document.getElementById('user-profile-btn');
const profileDropdown = document.getElementById('profile-dropdown');
const btnLogout = document.getElementById('btn-logout');

const selectPais = document.getElementById('select-pais');
const btnAnalisar = document.getElementById('btn-analisar');
const statusMsg = document.getElementById('status-msg');
const trendsList = document.getElementById('trends-list');

// Instâncias para controle e atualização dos gráficos
let chartMesInstance = null;
let chartAtualInstance = null;

// --- CONTROLE DE AUTENTICAÇÃO ---
onAuthStateChanged(auth, (user) => {
  if (user) {
    userName.textContent = user.displayName || "Usuário";
    if (user.photoURL) {
      userPhoto.src = user.photoURL;
    }
  } else {
    window.location.href = "index.html";
  }
});

// Dropdown de perfil
userProfileBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  profileDropdown.style.display = profileDropdown.style.display === 'block' ? 'none' : 'block';
});

document.addEventListener('click', () => {
  profileDropdown.style.display = 'none';
});

// Logout
btnLogout.addEventListener('click', async () => {
  await signOut(auth);
  window.location.href = "index.html";
});

// --- CARREGAMENTO DE DADOS ---
btnAnalisar.addEventListener('click', async () => {
  const pais = selectPais.value;
  const csvUrl = `https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/main/trending_${pais}_latest.csv`;

  btnAnalisar.disabled = true;
  mostrarStatus("Carregando tendências e gerando gráficos...", "info");

  try {
    const res = await fetch(csvUrl);
    if (!res.ok) throw new Error("Não foi possível carregar o arquivo de dados do GitHub.");
    const csvData = await res.text();

    const todosItens = processarCSV(csvData);
    const top10Recentes = todosItens.slice(0, 10);

    // Ordena os itens por volume para identificar os maiores do mês
    const top10Mes = [...todosItens]
      .sort((a, b) => b.valorNumerico - a.valorNumerico)
      .slice(0, 10);

    renderizarTop10(top10Recentes);
    renderizarGraficoMes(top10Mes);
    renderizarGraficoAtual(top10Recentes);

    ocultarStatus();

  } catch (err) {
    console.error(err);
    mostrarStatus(`Erro: ${err.message}`, "error");
  } finally {
    btnAnalisar.disabled = false;
  }
});

// Processa o CSV completo convertendo strings de volume em inteiros
function processarCSV(csvText) {
  const linhas = csvText.trim().split('\n').slice(1);
  const lista = [];

  linhas.forEach(linha => {
    const colunas = linha.match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g) || linha.split(',');
    if (colunas.length >= 2) {
      const termo = colunas[0]?.replace(/"/g, '').trim();
      const volumeStr = colunas[1]?.replace(/"/g, '').trim() || '0';
      const tempo = colunas[2]?.replace(/"/g, '').trim() || 'recente';

      lista.push({
        termo: termo,
        volume: volumeStr,
        valorNumerico: converterVolume(volumeStr),
        tempo: tempo
      });
    }
  });

  return lista;
}

// Converte valores formatados ex: "100K+", "1M+" em números utilizáveis pelo gráfico
function converterVolume(volStr) {
  const limpo = volStr.toUpperCase().replace(/\+/g, '').replace(/\./g, '').replace(/,/g, '.').trim();
  if (limpo.includes('K')) {
    return parseFloat(limpo.replace('K', '')) * 1000;
  } else if (limpo.includes('M')) {
    return parseFloat(limpo.replace('M', '')) * 1000000;
  }
  return parseFloat(limpo) || 0;
}

// Renderiza a lista das 10 buscas recentes
function renderizarTop10(itens) {
  trendsList.innerHTML = '';
  
  if (itens.length === 0) {
    trendsList.innerHTML = '<li style="color: #a0aec0;">Nenhum dado encontrado.</li>';
    return;
  }

  itens.forEach((item, index) => {
    const li = document.createElement('li');
    li.className = 'trend-item';

    const termoEncoded = encodeURIComponent(item.termo);
    const googleSearchUrl = `https://www.google.com/search?q=${termoEncoded}`;

    li.innerHTML = `
      <div>
        <span class="trend-rank">#${index + 1}</span>
        <a href="${googleSearchUrl}" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: none;">
          <strong style="cursor: pointer;">${item.termo}</strong>
        </a>
        <span class="trend-time">• ${item.tempo}</span>
      </div>
      <span class="trend-vol">${item.volume}</span>
    `;
    trendsList.appendChild(li);
  });
}

// --- GRÁFICO 1: MAIORES DO MÊS (Barras Horizontais) ---
function renderizarGraficoMes(itens) {
  const canvas = document.getElementById('graficoMes');
  if (!canvas) return;

  if (chartMesInstance) chartMesInstance.destroy();

  const ctx = canvas.getContext('2d');

  chartMesInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: itens.map(item => item.termo),
      datasets: [{
        label: 'Volume Estimado no Mês',
        data: itens.map(item => item.valorNumerico),
        backgroundColor: 'rgba(92, 127, 145, 0.75)',
        borderColor: 'rgba(92, 127, 145, 1)',
        borderWidth: 1.5,
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` Volume: ${itens[ctx.dataIndex].volume}`
          }
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          ticks: {
            callback: (val) => val >= 1000000 ? (val / 1000000) + 'M' : (val >= 1000 ? (val / 1000) + 'K' : val)
          }
        }
      }
    }
  });
}

// --- GRÁFICO 2: VOLUME COMPARATIVO (Barras Verticais) ---
function renderizarGraficoAtual(itens) {
  const canvas = document.getElementById('graficoAtual');
  if (!canvas) return;

  if (chartAtualInstance) chartAtualInstance.destroy();

  const ctx = canvas.getContext('2d');

  chartAtualInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: itens.map(item => item.termo),
      datasets: [{
        label: 'Volume de Buscas Recente',
        data: itens.map(item => item.valorNumerico),
        backgroundColor: 'rgba(174, 198, 207, 0.75)',
        borderColor: 'rgba(146, 177, 190, 1)',
        borderWidth: 2,
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true },
        tooltip: {
          callbacks: {
            label: (ctx) => ` Volume: ${itens[ctx.dataIndex].volume}`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (val) => val >= 1000000 ? (val / 1000000) + 'M' : (val >= 1000 ? (val / 1000) + 'K' : val)
          }
        }
      }
    }
  });
}

function mostrarStatus(texto, tipo) {
  statusMsg.textContent = texto;
  statusMsg.className = `status-msg ${tipo}`;
}

function ocultarStatus() {
  statusMsg.className = 'status-msg';
  statusMsg.textContent = '';
}