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
  CircularProgress
} from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import { authService } from '../services/auth';

// Replace this with your actual GitHub Client ID from Step 1
// const GITHUB_CLIENT_ID = 'Ov23liXXXXXXXXXXXX'; // ⚠️ REPLACE WITH YOUR CLIENT ID
// At the top of Login.jsx
const GITHUB_CLIENT_ID = process.env.REACT_APP_GITHUB_CLIENT_ID || 'your_fallback_client_id';
export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Regular email/password login
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

  // GitHub OAuth login
  const handleGitHubLogin = () => {
    const redirectUri = encodeURIComponent('http://localhost:3000/auth/callback');
    const scope = encodeURIComponent('read:user user:email');
    
    const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${redirectUri}&scope=${scope}`;
    
    // Redirect to GitHub
    window.location.href = githubAuthUrl;
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f5f5f5',
        }}
      >
        <Card sx={{ width: '100%', maxWidth: 400, boxShadow: 3 }}>
          <CardContent sx={{ p: 4 }}>
            {/* Header */}
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Typography 
                variant="h4" 
                gutterBottom 
                fontWeight="bold"
                color="primary"
              >
                Bug Triaging System
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Automate Bug Triaging With AI-Powered Intelligence
              </Typography>
            </Box>

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
                '&:hover': {
                  borderColor: '#000',
                  backgroundColor: 'rgba(0,0,0,0.04)',
                }
              }}
            >
              Sign in with GitHub
            </Button>

            <Divider sx={{ my: 3 }}>
              <Typography variant="caption" color="text.secondary">
                OR
              </Typography>
            </Divider>

            {/* Email/Password Login Form */}
            <form onSubmit={handleLogin}>
              <TextField
                fullWidth
                label="Email Address"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                margin="normal"
                required
                disabled={loading}
                variant="outlined"
              />
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                margin="normal"
                required
                disabled={loading}
                variant="outlined"
              />
              
              <Button
                fullWidth
                variant="contained"
                type="submit"
                size="large"
                sx={{ mt: 3, mb: 2, py: 1.5 }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : 'Sign In'}
              </Button>
            </form>

            {/* Development Note */}
            <Box 
              sx={{ 
                mt: 3, 
                p: 2, 
                backgroundColor: '#f8f9fa', 
                borderRadius: 1,
                border: '1px dashed #ddd'
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
    </Container>
  );
}