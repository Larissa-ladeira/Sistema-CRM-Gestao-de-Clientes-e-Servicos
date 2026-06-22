import {FaUser, FaLock} from 'react-icons/fa';

import{ useState } from 'react';

import './Login.css';

import './App.css';

const Login = () => {
    const [username, SetUsername] = useState("");
    const [password, setPassword] = useState("");

    const handleSubmit = (event) => {
        event.preventDefault();

        alert("Enviamos os dados:" + username + " - " + password);
};
  return (
    <div className="container">
        <form onSumit={handleSubmit}>
            <h1>Acesse o sistema</h1>
            <div className="input-field">
                <input type="email" placeholder="Digite seu email" required onChange ={(e) => SetUsername(e.target.value)}/>
                <FaUser className='icon' />
            </div>
            <div className="input-field">
                <input type="password" placeholder="Digite sua senha" required onChange ={(e) => setPassword(e.target.value)}/>
                <FaLock className='icon' />
            </div>
            <div className="recall-forget">
                <label>
                    <input type="checkbox" />

                    Lembre de mim 
                    <a href="#">Esqueceu a senha?</a>
                </label>
            </div>
            <button type="submit">Entrar</button>
            <div className="signup-link">
                <p>Não tem uma conta? <a href="#">Registrar</a></p>
            </div>
        </form>
    </div>
    
  );
};

export default Login;
