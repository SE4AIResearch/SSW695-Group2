import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  IconButton,
  CircularProgress,
  Alert
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { configApi, observabilityApi } from '../services/api';

// const REPO_ID = parseInt(localStorage.getItem('repo_id')) || 2; // UPDATED!

export default function Team() {
  const [repoId, setRepoId] = useState(parseInt(localStorage.getItem('repo_id')) || null);
  const [developers, setDevelopers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingDev, setEditingDev] = useState(null);
  const [formData, setFormData] = useState({
    github_login: '',
    skills: '',
    max_capacity: 5,
    repo_id: localStorage.getItem('repo_id') || ''
  });

  useEffect(() => {
    if (repoId) fetchDevelopers(); 
  }, [repoId]);

  const fetchDevelopers = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await observabilityApi.getWorkload(repoId);
      console.log('Developers loaded:', response.data);
      setDevelopers(response.data.developers || []);
    } catch (err) {
      console.error('Error loading developers:', err);
      setError('Failed to load developers. Make sure backend is running on http://localhost:8000');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (dev = null) => {
    if (dev) {
      setEditingDev(dev);
      setFormData({
        github_login: dev.github_login,
        skills: dev.skills.join(', '),
        max_capacity: dev.max_capacity,
        repo_id: repoId || localStorage.getItem('repo_id') || ''
      });
    } else {
      setEditingDev(null);
      setFormData({
        github_login: '',
        skills: '',
        max_capacity: 5,
        repo_id: repoId || localStorage.getItem('repo_id') || ''
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingDev(null);
    setFormData({ github_login: '', skills: '', max_capacity: 5, repo_id: localStorage.getItem('repo_id') || '' });
  };

  const handleSubmit = async () => {
    try {
      const skillsArray = formData.skills
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);

      if (!formData.github_login) {
        setError('GitHub username is required');
        return;
      }

      if (skillsArray.length === 0) {
        setError('At least one skill is required');
        return;
      }

      if (editingDev) {
        await configApi.updateDeveloper(repoId, editingDev.github_login, {
          skills: skillsArray,
          max_capacity: parseInt(formData.max_capacity)
        });
      } else {
        const targetRepoId = parseInt(formData.repo_id);
        await configApi.addDeveloper(targetRepoId, {
          github_login: formData.github_login,
          skills: skillsArray,
          max_capacity: parseInt(formData.max_capacity)
        });
        // Sync state so fetch, edit, delete all follow the same repo
        localStorage.setItem('repo_id', targetRepoId);
        setRepoId(targetRepoId);
      }

      handleCloseDialog();
      fetchDevelopers();
      setError('');
    } catch (err) {
      console.error('Error saving developer:', err);
      const errorMsg = err.response?.data?.detail || 'Failed to save developer';
      setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
    }
  };

  const handleDelete = async (githubLogin) => {
    if (window.confirm(`Remove ${githubLogin}?`)) {
      try {
        await configApi.deleteDeveloper(repoId, githubLogin);
        fetchDevelopers();
        setError('');
      } catch (err) {
        console.error('Error deleting developer:', err);
        setError('Failed to delete developer');
      }
    }
  };

  if (!repoId) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <Alert severity="info" sx={{ maxWidth: 500 }}>
          No repository enrolled yet. Go to <strong>Repository Setup</strong> first.
        </Alert>
      </Box>
    );
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h3" fontWeight="600">
          Team Members
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
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
          Add Developer
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {developers.map((dev) => (
          <Grid item xs={12} sm={6} md={4} key={dev.github_login}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                  <Typography variant="h5" fontWeight="bold">
                    @{dev.github_login}
                  </Typography>
                  <Box>
                    <IconButton size="small" onClick={() => handleOpenDialog(dev)} color="primary">
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleDelete(dev.github_login)} color="error">
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary" fontWeight="bold">
                    Skills:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {dev.skills.map((skill, idx) => (
                      <Chip
                        key={idx}
                        label={skill}
                        size="small"
                        sx={{ backgroundColor: '#EDE9FE', color: '#7C3AED' }}
                      />
                    ))}
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" fontWeight="bold" sx={{ mb: 0.5 }}>
                    Workload:
                  </Typography>
                  <Chip
                    label={`${dev.open_assignments} / ${dev.max_capacity} bugs`}
                    size="medium"
                    color={dev.open_assignments >= dev.max_capacity ? 'error' : 'success'}
                    sx={{ fontWeight: 600 }}
                  />
                </Box>

                <Typography variant="caption" color="text.secondary">
                  Available Capacity: {dev.available_capacity} {dev.available_capacity === 1 ? 'bug' : 'bugs'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}

        {developers.length === 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ p: 5, textAlign: 'center' }}>
                <Typography variant="h6" color="text.secondary">
                  No developers yet. Click "Add Developer" to start.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontSize: '1.5rem', fontWeight: 600 }}>
          {editingDev ? 'Edit Developer' : 'Add Developer'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Repository ID"
            type="number"
            value={formData.repo_id}
            onChange={(e) => setFormData({ ...formData, repo_id: e.target.value })}
            margin="normal"
            required
            disabled={!!editingDev}
            helperText={editingDev ? "Cannot change repo for existing developer" : "GitHub numeric repo ID"}
          />
          <TextField
            fullWidth
            label="GitHub Username"
            value={formData.github_login}
            onChange={(e) => setFormData({ ...formData, github_login: e.target.value })}
            disabled={!!editingDev}
            margin="normal"
            required
            helperText={editingDev ? "Cannot change username" : "Enter GitHub username without @"}
          />
          <TextField
            fullWidth
            label="Skills"
            value={formData.skills}
            onChange={(e) => setFormData({ ...formData, skills: e.target.value })}
            margin="normal"
            placeholder="bug, feature, docs, security, question"
            required
            helperText="Allowed: bug, feature, docs, security, question (comma-separated)"
          />
          <TextField
            fullWidth
            label="Max Capacity"
            type="number"
            value={formData.max_capacity}
            onChange={(e) => setFormData({ ...formData, max_capacity: e.target.value })}
            margin="normal"
            inputProps={{ min: 1, max: 100 }}
            required
            helperText="Maximum number of bugs this developer can handle"
          />
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={handleCloseDialog} sx={{ textTransform: 'none' }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!formData.github_login || !formData.skills}
            sx={{
              backgroundColor: '#7C3AED',
              textTransform: 'none',
              '&:hover': { backgroundColor: '#6D28D9' }
            }}
          >
            {editingDev ? 'Update' : 'Add Developer'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}