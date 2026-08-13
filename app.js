import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { 
  getAuth, 
  GoogleAuthProvider, 
  signInWithPopup,
  onAuthStateChanged 
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { 
  getFirestore, 
  doc, 
  setDoc, 
  serverTimestamp 
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";

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
const db = getFirestore(app);
const googleProvider = new GoogleAuthProvider();

const GITHUB_USER = "GabryelAquiles";
const GITHUB_REPO = "News-Through-Time"; 
const CSV_URL = `https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/main/trending_BR_latest.csv`;

const GEMINI_API_KEY = "AQ.Ab8RN6IOpiRO-WqW3NgO0UNI0cggkdTHUK_E6xhMS8KOf_f3Jg";

const btnGoogle = document.getElementById('btn-google');
const btnResumo = document.getElementById('btn-resumo'); 
const messageDiv = document.getElementById('message');
const elResumoTexto = document.getElementById('resumo-texto');
const containerResumo = document.getElementById('resumo-container');

onAuthStateChanged(auth, (user) => {
  if (user) {
    console.log("Usuário autenticado:", user.displayName);
  }
});

btnGoogle.addEventListener('click', async () => {
  clearMessage();

  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;

    await salvarUsuarioNoBanco(user);

    showMessage(`Bem-vindo(a), ${user.displayName}! Buscando resumo de tendências...`, 'success');

    await carregarEGerarResumoIA();

  } catch (error) {
    if (error.code === 'auth/popup-closed-by-user') {
      showMessage("Janela de login fechada antes de concluir.", 'error');
    } else {
      showMessage("Erro ao fazer login com o Google.", 'error');
    }
    console.error(error);
  }
});

async function salvarUsuarioNoBanco(user) {
  const userRef = doc(db, "usuarios", user.uid);
  
  await setDoc(userRef, {
    uid: user.uid,
    nome: user.displayName,
    email: user.email,
    foto: user.photoURL,
    ultimoAcesso: serverTimestamp()
  }, { merge: true }); 
}

async function carregarEGerarResumoIA() {
  try {
    const respostaCsv = await fetch(CSV_URL);
    if (!respostaCsv.ok) throw new Error("Não foi possível carregar os dados das tendências.");
    const textoCsv = await respostaCsv.text();

    showMessage("Analisando as tendências com Inteligência Artificial...", "success");

    const resumo = await gerarResumoGemini(textoCsv);

    if (elResumoTexto && containerResumo) {
      elResumoTexto.innerText = resumo;
      containerResumo.style.display = "block";
    }

  } catch (erro) {
    console.error("Erro no processamento da IA:", erro);
    showMessage(`Aviso: Login efetuado, mas erro ao gerar resumo IA.`, 'error');
  }
}

async function gerarResumoGemini(dadosCsv) {
  const urlApi = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`;

  const prompt = `Analise os dados extraídos do Google Trends (Brasil) abaixo (contendo Tendências, Volume e Tempo decorrido) e gere um resumo compacto destacando os 3 principais assuntos mais relevantes no momento, explicando o contexto resumidamente.\n\nDADOS DO CSV:\n${dadosCsv}`;

  const payload = {
    contents: [{
      parts: [{ text: prompt }]
    }]
  };

  const resposta = await fetch(urlApi, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!resposta.ok) {
    const dadosErro = await resposta.json();
    throw new Error(dadosErro.error?.message || "Falha na API do Gemini.");
  }

  const dados = await resposta.json();
  return dados.candidates[0].content.parts[0].text;
}

function showMessage(text, type) {
  messageDiv.textContent = text;
  messageDiv.className = `message ${type}`;
}

function clearMessage() {
  messageDiv.textContent = '';
  messageDiv.className = 'message';
}
