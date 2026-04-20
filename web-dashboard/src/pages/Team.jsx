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
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormHelperText,
  Autocomplete
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import RefreshIcon from '@mui/icons-material/Refresh';
import { configApi, observabilityApi } from '../services/api';

// Allowed skills from backend
const ALLOWED_SKILLS = ['bug', 'feature', 'docs', 'security', 'question'];

export default function Team() {
  const [repositories, setRepositories] = useState([]);
  const [selectedRepoId, setSelectedRepoId] = useState(parseInt(localStorage.getItem('repo_id')) || null);
  const [developers, setDevelopers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingRepos, setLoadingRepos] = useState(true);
  const [error, setError] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingDev, setEditingDev] = useState(null);
  const [formData, setFormData] = useState({
    github_login: '',
    skills: [],
    max_capacity: 5,
    repo_id: ''
  });
  const [formErrors, setFormErrors] = useState({});

  // Fetch repositories on mount
  useEffect(() => {
    fetchRepositories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fetch developers when repo changes
  useEffect(() => {
    if (selectedRepoId) {
      fetchDevelopers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRepoId]);

  const fetchRepositories = async () => {
    setLoadingRepos(true);
    try {
      const response = await configApi.getAllRepos({ limit: 100, offset: 0 });
      setRepositories(response.data.repos || []);

      if (!selectedRepoId && response.data.repos.length > 0) {
        setSelectedRepoId(response.data.repos[0].repo_id);
      }
    } catch (err) {
      console.error('Error loading repositories:', err);
      setError('Failed to load repositories');
    } finally {
      setLoadingRepos(false);
    }
  };

  const fetchDevelopers = async () => {
    if (!selectedRepoId) return;

    setLoading(true);
    setError('');
    try {
      const response = await observabilityApi.getWorkload(selectedRepoId);
      console.log('Developers loaded:', response.data);
      setDevelopers(response.data.developers || []);
    } catch (err) {
      console.error('Error loading developers:', err);
      setError('Failed to load developers');
    } finally {
      setLoading(false);
    }
  };

  const handleRepoChange = (event) => {
    const newRepoId = parseInt(event.target.value);
    setSelectedRepoId(newRepoId);
    localStorage.setItem('repo_id', newRepoId);
  };

  const handleOpenDialog = (dev = null) => {
    setFormErrors({});

    if (dev) {
      setEditingDev(dev);
      setFormData({
        github_login: dev.github_login,
        skills: dev.skills,
        max_capacity: dev.max_capacity,
        repo_id: selectedRepoId
      });
    } else {
      setEditingDev(null);
      setFormData({
        github_login: '',
        skills: [],
        max_capacity: 5,
        repo_id: selectedRepoId
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingDev(null);
    setFormErrors({});
  };

  const validateForm = () => {
    const errors = {};

    // Validate repository
    if (!formData.repo_id) {
      errors.repo_id = 'Please select a repository';
    }

    // Validate GitHub username
    if (!formData.github_login || formData.github_login.trim() === '') {
      errors.github_login = 'GitHub username is required';
    } else if (formData.github_login.length < 2) {
      errors.github_login = 'Username must be at least 2 characters';
    } else if (!/^[a-zA-Z0-9-]+$/.test(formData.github_login)) {
      errors.github_login = 'Username can only contain letters, numbers, and hyphens';
    }

    // Validate skills
    if (!formData.skills || formData.skills.length === 0) {
      errors.skills = 'At least one skill is required';
    }

    // Validate max capacity
    if (!formData.max_capacity || formData.max_capacity < 1) {
      errors.max_capacity = 'Capacity must be at least 1';
    } else if (formData.max_capacity > 100) {
      errors.max_capacity = 'Capacity cannot exceed 100';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    // Validate form
    if (!validateForm()) {
      return;
    }

    try {
      const targetRepoId = parseInt(formData.repo_id);

      if (editingDev) {
        await configApi.updateDeveloper(targetRepoId, editingDev.github_login, {
          skills: formData.skills,
          max_capacity: parseInt(formData.max_capacity)
        });
      } else {
        await configApi.addDeveloper(targetRepoId, {
          github_login: formData.github_login.trim(),
          skills: formData.skills,
          max_capacity: parseInt(formData.max_capacity)
        });
      }

      handleCloseDialog();

      if (targetRepoId !== selectedRepoId) {
        setSelectedRepoId(targetRepoId);
        localStorage.setItem('repo_id', targetRepoId);
      } else {
        fetchDevelopers();
      }

      setError('');
    } catch (err) {
      console.error('Error saving developer:', err);
      const errorDetail = err.response?.data?.detail;

      let errorMsg = 'Failed to save developer';
      if (Array.isArray(errorDetail)) {
        errorMsg = errorDetail.map(e => e.msg).join('; ');
      } else if (typeof errorDetail === 'string') {
        errorMsg = errorDetail;
      }

      setError(errorMsg);
    }
  };

  const handleDelete = async (githubLogin) => {
    if (window.confirm(`Remove ${githubLogin}?`)) {
      try {
        await configApi.deleteDeveloper(selectedRepoId, githubLogin);
        fetchDevelopers();
        setError('');
      } catch (err) {
        console.error('Error deleting developer:', err);
        setError('Failed to delete developer');
      }
    }
  };

  const currentRepo = repositories.find(r => r.repo_id === selectedRepoId);

  if (loadingRepos) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (repositories.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <Alert severity="info" sx={{ maxWidth: 500 }}>
          No repositories enrolled yet. Go to <strong>Setup</strong> to enroll your first repository.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header with Repository Selector */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h3" fontWeight="600" sx={{ mb: 2 }}>
            Team Members
          </Typography>

          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControl sx={{ minWidth: 300 }}>
              <InputLabel>Repository</InputLabel>
              <Select
                value={selectedRepoId || ''}
                onChange={handleRepoChange}
                label="Repository"
              >
                {repositories.map((repo) => (
                  <MenuItem key={repo.repo_id} value={repo.repo_id}>
                    {repo.repo_full_name} (ID: {repo.repo_id})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <IconButton
              onClick={fetchDevelopers}
              sx={{ color: '#7C3AED' }}
              title="Refresh"
            >
              <RefreshIcon />
            </IconButton>
          </Box>
        </Box>

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

      {currentRepo && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Showing developers for <strong>{currentRepo.repo_full_name}</strong>
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" py={6}>
          <CircularProgress size={60} />
        </Box>
      ) : (
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
                    No developers for this repository yet.
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Click "Add Developer" to start building your team.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontSize: '1.5rem', fontWeight: 600 }}>
          {editingDev ? 'Edit Developer' : 'Add Developer'}
        </DialogTitle>
        <DialogContent>
          {/* Repository Selector */}
          <FormControl
            fullWidth
            margin="normal"
            required
            error={!!formErrors.repo_id}
          >
            <InputLabel>Repository</InputLabel>
            <Select
              value={formData.repo_id}
              onChange={(e) => {
                setFormData({ ...formData, repo_id: e.target.value });
                setFormErrors({ ...formErrors, repo_id: '' });
              }}
              label="Repository"
              disabled={!!editingDev}
            >
              {repositories.map((repo) => (
                <MenuItem key={repo.repo_id} value={repo.repo_id}>
                  {repo.repo_full_name} (ID: {repo.repo_id})
                </MenuItem>
              ))}
            </Select>
            {formErrors.repo_id && (
              <FormHelperText>{formErrors.repo_id}</FormHelperText>
            )}
          </FormControl>

          {/* GitHub Username */}
          <TextField
            fullWidth
            label="GitHub Username"
            value={formData.github_login}
            onChange={(e) => {
              setFormData({ ...formData, github_login: e.target.value });
              setFormErrors({ ...formErrors, github_login: '' });
            }}
            disabled={!!editingDev}
            margin="normal"
            required
            error={!!formErrors.github_login}
            helperText={
              formErrors.github_login ||
              (editingDev ? "Cannot change username" : "Enter GitHub username without @")
            }
          />

          {/* Skills with Autocomplete - ONLY PREDEFINED SKILLS */}
          <Autocomplete
            multiple
            freeSolo={false}  // ← Prevent custom input
            options={ALLOWED_SKILLS}
            value={formData.skills}
            onChange={(event, newValue) => {
              setFormData({ ...formData, skills: newValue });
              setFormErrors({ ...formErrors, skills: '' });
            }}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip
                  label={option}
                  {...getTagProps({ index })}
                  sx={{ backgroundColor: '#EDE9FE', color: '#7C3AED' }}
                />
              ))
            }
            renderInput={(params) => (
              <TextField
                {...params}
                margin="normal"
                label="Skills *"
                placeholder="Select skills from dropdown"
                required
                error={!!formErrors.skills}
                helperText={
                  formErrors.skills ||
                  "Only allowed skills: bug, feature, docs, security, question"
                }
              />
            )}
          />

          {/* Max Capacity */}
          <TextField
            fullWidth
            label="Max Capacity"
            type="number"
            value={formData.max_capacity}
            onChange={(e) => {
              setFormData({ ...formData, max_capacity: e.target.value });
              setFormErrors({ ...formErrors, max_capacity: '' });
            }}
            margin="normal"
            inputProps={{ min: 1, max: 100 }}
            required
            error={!!formErrors.max_capacity}
            helperText={
              formErrors.max_capacity ||
              "Maximum number of bugs (1-100)"
            }
          />
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={handleCloseDialog} sx={{ textTransform: 'none' }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
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