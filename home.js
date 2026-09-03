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

// --- GITHUB & GEMINI CONFIG ---
const GITHUB_USER = "GabryelAquiles";
const GITHUB_REPO = "News-Through-Time";
const GEMINI_API_KEY = "AQ.Ab8RN6Lk60gcHb82XvqQ07gwA57TV4FfwqWwycu9fRZgz0-zlw"; 

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
const resumoText = document.getElementById('resumo-text');

// --- CONTROLE DE AUTENTICAÇÃO ---
onAuthStateChanged(auth, (user) => {
  if (user) {
    userName.textContent = user.displayName || "Usuário";
    if (user.photoURL) {
      userPhoto.src = user.photoURL;
    }
  } else {
    // Redireciona para o login se não estiver autenticado
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
  mostrarStatus("Buscando dados das tendências...", "info");

  try {
    // 1. Puxar CSV do GitHub
    const res = await fetch(csvUrl);
    if (!res.ok) throw new Error("Não foi possível carregar o arquivo de dados.");
    const csvData = await res.text();

    // 2. Extrair e Exibir os 10 primeiros resultados
    const top10 = processarTop10(csvData);
    renderizarTop10(top10);

    // 3. Gerar Resumo via Gemini
    mostrarStatus("Analisando com Inteligência Artificial...", "info");
    const resumo = await gerarResumoGemini(top10, pais);
    
    resumoText.innerText = resumo;
    ocultarStatus();

  } catch (err) {
    console.error(err);
    mostrarStatus(`Erro: ${err.message}`, "error");
  } finally {
    btnAnalisar.disabled = false;
  }
});

// Processa o CSV e isola apenas os 10 primeiros itens
function processarTop10(csvText) {
  const linhas = csvText.trim().split('\n').slice(1);
  const lista = [];

  for (let i = 0; i < Math.min(linhas.length, 10); i++) {
    const colunas = linhas[i].match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g) || linhas[i].split(',');
    if (colunas.length >= 2) {
      lista.push({
        termo: colunas[0]?.replace(/"/g, '').trim(),
        volume: colunas[1]?.replace(/"/g, '').trim(),
        tempo: colunas[2]?.replace(/"/g, '').trim() || 'recente'
      });
    }
  }
  return lista;
}

// Renderiza os 10 itens na lista HTML
function renderizarTop10(itens) {
  trendsList.innerHTML = '';
  
  if (itens.length === 0) {
    trendsList.innerHTML = '<li style="color: #a0aec0;">Nenhum dado encontrado.</li>';
    return;
  }

  itens.forEach((item, index) => {
    const li = document.createElement('li');
    li.className = 'trend-item';
    li.innerHTML = `
      <div>
        <span class="trend-rank">#${index + 1}</span>
        <strong>${item.termo}</strong>
        <span class="trend-time">• ${item.tempo}</span>
      </div>
      <span class="trend-vol">${item.volume}</span>
    `;
    trendsList.appendChild(li);
  });
}

// Chama a API do Gemini enviando apenas o Top 10
async function gerarResumoGemini(top10List, pais) {
  const urlApi = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`;

  const prompt = `Você é um analista de dados. Analise estas 10 maiores tendências de busca do Google Trends no ${pais} e faça um resumo conciso (em 3 parágrafos curtos) explicando o contexto geral do que as pessoas estão buscando agora:\n\n` + 
    top10List.map((t, i) => `${i+1}. ${t.termo} (${t.volume})`).join('\n');

  const resposta = await fetch(urlApi, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
  });

  if (!resposta.ok) {
    const err = await resposta.json();
    throw new Error(err.error?.message || "Erro na resposta do Gemini.");
  }

  const data = await resposta.json();
  return data.candidates[0].content.parts[0].text;
}

function mostrarStatus(texto, tipo) {
  statusMsg.textContent = texto;
  statusMsg.className = `status-msg ${tipo}`;
}

function ocultarStatus() {
  statusMsg.className = 'status-msg';
  statusMsg.textContent = '';
}
