// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyBas8LZdCgfecT2J-KwAlyx_6Iep3KiopA",
  authDomain: "nordhjemstore.firebaseapp.com",
  projectId: "nordhjemstore",
  storageBucket: "nordhjemstore.firebasestorage.app",
  messagingSenderId: "757427498119",
  appId: "1:757427498119:web:6374e7aa076e732c44dc22",
  measurementId: "G-R6Z48HN304"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
