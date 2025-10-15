import React, { useState, useEffect } from 'react';
import './Login.css';

const Login = ({ onLogin }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLogin, setIsLogin] = useState(true);
    const [rememberMe, setRememberMe] = useState(false);

    useEffect(() => {
        const storedUsername = localStorage.getItem('rememberedUsername');
        if (storedUsername) {
            setUsername(storedUsername);
            setRememberMe(true);
        }
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        const endpoint = isLogin ? 'http://localhost:8000/login/' : 'http://localhost:8000/register/';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });
        const data = await response.json();
        if (response.ok) {
            if (isLogin) {
                alert('Login successful');
                localStorage.setItem('user_id', data.user_id);
                if (rememberMe) {
                    localStorage.setItem('rememberedUsername', username);
                } else {
                    localStorage.removeItem('rememberedUsername');
                }
                onLogin(data.user_id);
            } else {
                alert('Registration successful');
                setIsLogin(true);
                setPassword('');
            }
        } else {
            alert(data.detail);
        }
    };

    return (
        <div className="login-container">
            <div className="login-form">
                <img src="/querion free.ico" alt="Querion" className="login-logo" />
                <h1>Querion</h1>
                <h2>{isLogin ? 'Login' : 'Register'}</h2>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Username</label>
                        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} />
                    </div>
                    <div className="form-group">
                        <label>Password</label>
                        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
                    </div>
                    <div className="form-group remember-me">
                        <input type="checkbox" id="rememberMe" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} />
                        <label htmlFor="rememberMe">Remember Me</label>
                    </div>
                    <button type="submit">{isLogin ? 'Login' : 'Register'}</button>
                </form>
                <button className="toggle-button" onClick={() => setIsLogin(!isLogin)}>
                    {isLogin ? 'Need to register?' : 'Have an account?'}
                </button>
            </div>
        </div>
    );
};

export default Login;