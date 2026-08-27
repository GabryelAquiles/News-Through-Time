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
const db = getFirestore(app);
const googleProvider = new GoogleAuthProvider();

// --- ELEMENTOS DO DOM ---
const btnGoogle = document.getElementById('btn-google');
const messageDiv = document.getElementById('mensagem');

// --- VERIFICA SE O USUÁRIO JÁ ESTÁ AUTENTICADO ---
onAuthStateChanged(auth, (user) => {
  if (user) {
    // Se o usuário já estiver logado, vai direto para a página principal
    window.location.href = "home.html";
  }
});

// --- CLIQUE NO BOTÃO DE LOGIN ---
btnGoogle.addEventListener('click', async () => {
  clearMessage();

  try {
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;

    // Salva ou atualiza os dados do usuário no Firestore
    await salvarUsuarioNoBanco(user);

    showMessage(`Bem-vindo(a), ${user.displayName}! Redirecionando...`, 'success');

    // Aguarda um pequeno intervalo e redireciona para o painel principal
    setTimeout(() => {
      window.location.href = "home.html";
    }, 1000);

  } catch (error) {
    if (error.code === 'auth/popup-closed-by-user') {
      showMessage("Janela de login fechada antes de concluir.", 'error');
    } else {
      showMessage("Erro ao fazer login com o Google.", 'error');
    }
    console.error("Erro na autenticação:", error);
  }
});

// --- SALVAR/ATUALIZAR DADOS DO USUÁRIO ---
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

function showMessage(text, type) {
  messageDiv.textContent = text;
  messageDiv.className = `message ${type}`;
}

function clearMessage() {
  messageDiv.textContent = '';
  messageDiv.className = 'message';
}