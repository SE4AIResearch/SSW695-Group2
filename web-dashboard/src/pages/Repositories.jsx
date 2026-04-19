import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import SettingsIcon from '@mui/icons-material/Settings';
import { useNavigate } from 'react-router-dom';
import { configApi } from '../services/api';

export default function Repositories() {
  const navigate = useNavigate();
  const [repositories, setRepositories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const currentRepoId = parseInt(localStorage.getItem('repo_id'));

  useEffect(() => {
    fetchRepositories();
  }, []);

  const fetchRepositories = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await configApi.getAllRepos({ limit: 100, offset: 0 });
      console.log('Repositories:', response.data);
      setRepositories(response.data.repos || []); // ← FIXED: Use 'repos' not 'repositories'
    } catch (err) {
      console.error('Error fetching repositories:', err);
      setError('Failed to load repositories. Make sure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectRepo = (repo) => {
    localStorage.setItem('repo_id', repo.repo_id);
    localStorage.setItem('repo_full_name', repo.repo_full_name);
    setSuccess(`✅ Switched to ${repo.repo_full_name}`);
    
    // Refresh to update the current repo indicator
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h3" fontWeight="600">
            Repositories
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
            Manage enrolled GitHub repositories
          </Typography>
        </Box>
        
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/setup')}
          sx={{
            backgroundColor: '#7C3AED',
            px: 3,
            py: 1.5,
            fontSize: '1rem',
            textTransform: 'none',
            fontWeight: 600,
            '&:hover': { backgroundColor: '#6D28D9' }
          }}
        >
          Enroll New Repository
        </Button>
      </Box>

      {/* Alerts */}
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}

      {/* Repositories Table */}
      {repositories.length === 0 ? (
        <Card>
          <CardContent sx={{ p: 6, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
              No repositories enrolled yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Get started by enrolling your first GitHub repository
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => navigate('/setup')}
              sx={{
                backgroundColor: '#7C3AED',
                textTransform: 'none',
                '&:hover': { backgroundColor: '#6D28D9' }
              }}
            >
              Enroll Repository
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: '#F9FAFB' }}>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell><strong>Repository</strong></TableCell>
                  <TableCell><strong>Repo ID</strong></TableCell>
                  <TableCell><strong>Installation ID</strong></TableCell>
                  <TableCell><strong>Enrolled</strong></TableCell>
                  <TableCell align="right"><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {repositories.map((repo) => {
                  const isActive = repo.repo_id === currentRepoId;
                  
                  return (
                    <TableRow 
                      key={repo.repo_id}
                      sx={{
                        backgroundColor: isActive ? '#F3F4F6' : 'white',
                        '&:hover': { backgroundColor: '#F9FAFB' }
                      }}
                    >
                      {/* Status */}
                      <TableCell>
                        {isActive ? (
                          <Tooltip title="Currently active">
                            <Chip 
                              icon={<CheckCircleIcon />}
                              label="Active" 
                              size="small" 
                              sx={{ 
                                backgroundColor: '#7C3AED', 
                                color: 'white',
                                fontWeight: 600
                              }}
                            />
                          </Tooltip>
                        ) : (
                          <Chip 
                            label="Available" 
                            size="small" 
                            variant="outlined"
                            sx={{ borderColor: '#D1D5DB', color: '#6B7280' }}
                          />
                        )}
                      </TableCell>

                      {/* Repository Name */}
                      <TableCell>
                        <Box>
                          <Typography variant="body1" fontWeight="600">
                            {repo.repo_full_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {repo.config?.defaults?.category || 'bug'} / {repo.config?.defaults?.priority || 'P2'}
                          </Typography>
                        </Box>
                      </TableCell>

                      {/* Repo ID */}
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#6B7280' }}>
                          {repo.repo_id}
                        </Typography>
                      </TableCell>

                      {/* Installation ID */}
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#6B7280' }}>
                          {repo.installation_id}
                        </Typography>
                      </TableCell>

                      {/* Created Date */}
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {formatDate(repo.created_at)}
                        </Typography>
                      </TableCell>

                      {/* Actions */}
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                          {!isActive && (
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => handleSelectRepo(repo)}
                              sx={{
                                textTransform: 'none',
                                borderColor: '#7C3AED',
                                color: '#7C3AED',
                                '&:hover': {
                                  borderColor: '#6D28D9',
                                  backgroundColor: '#F3F4F6'
                                }
                              }}
                            >
                              Use This Repo
                            </Button>
                          )}
                          
                          <Tooltip title="Configure">
                            <IconButton 
                              size="small"
                              onClick={() => navigate('/setup')}
                              sx={{ color: '#6B7280' }}
                            >
                              <SettingsIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Summary Footer */}
          <Box sx={{ p: 3, backgroundColor: '#F9FAFB', borderTop: '1px solid #E5E7EB' }}>
            <Typography variant="body2" color="text.secondary">
              <strong>{repositories.length}</strong> {repositories.length === 1 ? 'repository' : 'repositories'} enrolled
              {currentRepoId && ` • Currently using repo_id: ${currentRepoId}`}
            </Typography>
          </Box>
        </Card>
      )}
    </Box>
  );
}