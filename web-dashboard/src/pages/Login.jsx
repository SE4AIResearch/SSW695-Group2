import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Card, 
  CardContent, 
  TextField, 
  Button, 
  Typography,
  Container,
  Alert,
  Divider,
  CircularProgress,
  AppBar,
  Toolbar
} from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import { authService } from '../services/auth';

const GITHUB_CLIENT_ID = process.env.REACT_APP_GITHUB_CLIENT_ID || 'your_client_id';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await authService.login(email, password);
      
      if (result.success) {
        navigate('/dashboard');
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGitHubLogin = () => {
    const redirectUri = encodeURIComponent('http://localhost:3000/auth/callback');
    const scope = encodeURIComponent('read:user user:email');
    const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${redirectUri}&scope=${scope}`;
    window.location.href = githubAuthUrl;
  };

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <AppBar 
        position="static" 
        elevation={0}
        sx={{ 
          backgroundColor: 'white',
          borderBottom: '1px solid #e0e0e0'
        }}
      >
        <Toolbar>
          <Typography 
            variant="h5" 
            sx={{ 
              flexGrow: 1, 
              color: '#7C3AED',
              fontWeight: 'bold'
            }}
          >
            Buma
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', color: '#666' }}>
            <AccessTimeIcon sx={{ mr: 1, fontSize: 20 }} />
            <Typography variant="body2">
              {new Date().toLocaleString('en-US', { 
                month: '2-digit', 
                day: '2-digit', 
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content with Background */}
      <Box
        sx={{
          flexGrow: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)',
          position: 'relative',
          overflow: 'hidden',
          padding: '0 100px',
        }}
      >
        {/* Background Chart Pattern (simulated) */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'100\' height=\'100\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cpath d=\'M0 50 Q25 30, 50 50 T100 50\' stroke=\'%2322c55e\' stroke-width=\'2\' fill=\'none\' opacity=\'0.3\'/%3E%3C/svg%3E")',
            opacity: 0.1,
          }}
        />

        {/* Left Side - Headline */}
        <Box sx={{ maxWidth: 500, color: 'white', zIndex: 1 }}>
          <Typography 
            variant="h2" 
            sx={{ 
              fontWeight: 'bold',
              lineHeight: 1.2,
              mb: 2
            }}
          >
            Automate Bug Triaging With{' '}
            <Box component="span" sx={{ color: '#7C3AED' }}>
              AI-Powered Intelligence
            </Box>
          </Typography>
        </Box>

        {/* Right Side - Login Card */}
        <Card 
          sx={{ 
            width: '100%', 
            maxWidth: 440,
            boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
            borderRadius: 2,
            zIndex: 1
          }}
        >
          <CardContent sx={{ p: 4 }}>
            {/* Login Header */}
            <Typography 
              variant="h4" 
              gutterBottom 
              align="center"
              fontWeight="bold"
            >
              Login
            </Typography>
            <Typography 
              variant="body2" 
              color="text.secondary" 
              align="center" 
              sx={{ mb: 3 }}
            >
              Automate Bug Triaging With AI-Powered Intelligence
            </Typography>

            {/* Error Alert */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {/* GitHub Login Button */}
            <Button
              fullWidth
              variant="outlined"
              size="large"
              startIcon={<GitHubIcon />}
              onClick={handleGitHubLogin}
              sx={{ 
                mb: 2,
                py: 1.5,
                borderColor: '#333',
                color: '#333',
                textTransform: 'none',
                fontSize: '15px',
                '&:hover': {
                  borderColor: '#000',
                  backgroundColor: 'rgba(0,0,0,0.04)',
                }
              }}
            >
              SIGN IN WITH GITHUB
            </Button>

            <Divider sx={{ my: 3 }}>
              <Typography variant="caption" color="text.secondary">
                OR
              </Typography>
            </Divider>

            {/* Email/Password Form */}
            <form onSubmit={handleLogin}>
              <TextField
                fullWidth
                label="Email Address *"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                margin="normal"
                required
                disabled={loading}
                variant="outlined"
                placeholder="inak369@gmail.com"
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Password *"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                margin="normal"
                required
                disabled={loading}
                variant="outlined"
                placeholder="••••••••"
                sx={{ mb: 3 }}
              />
              
              <Button
                fullWidth
                variant="contained"
                type="submit"
                size="large"
                sx={{ 
                  py: 1.5,
                  backgroundColor: '#7C3AED',
                  textTransform: 'none',
                  fontSize: '15px',
                  fontWeight: 'bold',
                  '&:hover': {
                    backgroundColor: '#6D28D9'
                  }
                }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : 'SIGN IN'}
              </Button>
            </form>

            {/* Development Info */}
            <Box 
              sx={{ 
                mt: 3, 
                p: 2, 
                backgroundColor: '#f8f9fa', 
                borderRadius: 1,
                border: '1px solid #e0e0e0'
              }}
            >
              <Typography variant="caption" color="text.secondary">
                <strong>For Development:</strong>
                <br />
                Use GitHub login or test credentials:
                <br />
                Email: admin@test.com | Password: admin123
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}