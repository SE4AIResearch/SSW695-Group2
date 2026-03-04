import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CircularProgress, Box, Typography, Alert } from '@mui/material';
import axios from 'axios';

export default function AuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState('');

  useEffect(() => {
    const handleGitHubCallback = async () => {
      // Get the authorization code from URL
      const code = searchParams.get('code');
      const errorParam = searchParams.get('error');

      // Check if user denied access
      if (errorParam) {
        setError('GitHub authentication was cancelled');
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      if (!code) {
        setError('No authorization code received');
        setTimeout(() => navigate('/login'), 2000);
        return;
      }

      try {
        // Send code to your backend
        const response = await axios.post(
          'http://localhost:8000/api/v1/auth/github',
          { code },
          {
            headers: {
              'Content-Type': 'application/json',
            },
          }
        );

        const { token, user } = response.data;

        // Save to localStorage
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));

        // Redirect to dashboard
        navigate('/dashboard');
      } catch (error) {
        console.error('GitHub authentication error:', error);
        setError(
          error.response?.data?.message || 
          'Failed to authenticate with GitHub. Please try again.'
        );
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleGitHubCallback();
  }, [navigate, searchParams]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: '#f5f5f5',
      }}
    >
      {error ? (
        <>
          <Alert severity="error" sx={{ mb: 2, maxWidth: 400 }}>
            {error}
          </Alert>
          <Typography variant="body2" color="text.secondary">
            Redirecting to login...
          </Typography>
        </>
      ) : (
        <>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>
            Signing in with GitHub...
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Please wait while we complete your authentication
          </Typography>
        </>
      )}
    </Box>
  );
}