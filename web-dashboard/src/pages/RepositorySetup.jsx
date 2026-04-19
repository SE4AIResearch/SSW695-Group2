import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Paper,
  Divider
} from '@mui/material';
import { configApi } from '../services/api';

export default function RepositorySetup() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [formData, setFormData] = useState({
    repo_id: '',
    installation_id: '',
    repo_full_name: '',
    // CORRECT VALUES - matching backend validation
    cat_bug: 'bug',
    cat_feature: 'feature',
    cat_docs: 'docs',
    cat_security: 'security',
    cat_question: 'question',
    pri_p0: 'P0',
    pri_p1: 'P1',
    pri_p2: 'P2',
    pri_p3: 'P3',
    default_category: 'bug',
    default_priority: 'P2'
  });
  const [repoId, setRepoId] = useState(null);
  const [isEnrolled, setIsEnrolled] = useState(false); // Track enrollment status

  // Load demo data
  const loadDemoData = () => {
    if (isEnrolled) return; // Don't load if already enrolled
    
    setFormData({
      repo_id: '987654321',
      installation_id: '12345678',
      repo_full_name: 'demo-org/bug-tracker-pro',
      cat_bug: 'bug',
      cat_feature: 'feature',
      cat_docs: 'docs',
      cat_security: 'security',
      cat_question: 'question',
      pri_p0: 'P0',
      pri_p1: 'P1',
      pri_p2: 'P2',
      pri_p3: 'P3',
      default_category: 'bug',
      default_priority: 'P2'
    });
    setError('');
    setSuccess('');
  };

  // Reset form to enroll new repository
  const handleReset = () => {
    setFormData({
      repo_id: '',
      installation_id: '',
      repo_full_name: '',
      cat_bug: 'bug',
      cat_feature: 'feature',
      cat_docs: 'docs',
      cat_security: 'security',
      cat_question: 'question',
      pri_p0: 'P0',
      pri_p1: 'P1',
      pri_p2: 'P2',
      pri_p3: 'P3',
      default_category: 'bug',
      default_priority: 'P2'
    });
    setError('');
    setSuccess('');
    setRepoId(null);
    setIsEnrolled(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const payload = {
        repo_id: parseInt(formData.repo_id),
        installation_id: parseInt(formData.installation_id),
        repo_full_name: formData.repo_full_name,
        config: {
          label_map: {
            categories: {
              bug: formData.cat_bug,
              feature: formData.cat_feature,
              docs: formData.cat_docs,
              security: formData.cat_security,
              question: formData.cat_question
            },
            priorities: {
              P0: formData.pri_p0,
              P1: formData.pri_p1,
              P2: formData.pri_p2,
              P3: formData.pri_p3
            }
          },
          defaults: {
            category: formData.default_category,
            priority: formData.default_priority
          }
        }
      };

      console.log('Sending payload:', JSON.stringify(payload, null, 2));

      const response = await configApi.enrollRepo(payload);

      console.log('Response:', response.data);

      setRepoId(response.data.repo_id);
      setSuccess(`✅ Repository enrolled successfully! Your repo_id is: ${response.data.repo_id}`);
      setIsEnrolled(true); // Mark as enrolled
      
      localStorage.setItem('repo_id', response.data.repo_id);
      localStorage.setItem('repo_full_name', formData.repo_full_name);
      
    } catch (err) {
      console.error('Error:', err);
      const errorDetail = err.response?.data?.detail;
      let errorMsg = 'Failed to enroll repository.';
      
      if (Array.isArray(errorDetail)) {
        errorMsg = errorDetail.map(e => e.msg).join('; ');
      } else if (typeof errorDetail === 'string') {
        errorMsg = errorDetail;
      }
      
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field) => (e) => {
    setFormData({ ...formData, [field]: e.target.value });
  };

  return (
    <Box>
      {/* Header with Demo/Reset Button */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h3" fontWeight="600">
            Repository Setup
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
            {isEnrolled ? 'Repository enrolled and ready!' : 'Enroll a GitHub repository to start automatic bug triaging'}
          </Typography>
        </Box>
        
        {/* Demo Data or Reset Button */}
        {!isEnrolled ? (
          <Button
            variant="outlined"
            onClick={loadDemoData}
            sx={{
              borderColor: '#7C3AED',
              color: '#7C3AED',
              textTransform: 'none',
              px: 3,
              py: 1,
              fontWeight: 600,
              '&:hover': {
                borderColor: '#6D28D9',
                backgroundColor: '#F3F4F6'
              }
            }}
          >
            📋 Load Demo Data
          </Button>
        ) : (
          <Button
            variant="outlined"
            onClick={handleReset}
            sx={{
              borderColor: '#7C3AED',
              color: '#7C3AED',
              textTransform: 'none',
              px: 3,
              py: 1,
              fontWeight: 600,
              '&:hover': {
                borderColor: '#6D28D9',
                backgroundColor: '#F3F4F6'
              }
            }}
          >
            🔄 Enroll New Repository
          </Button>
        )}
      </Box>

      <Card sx={{ maxWidth: 800 }}>
        <CardContent sx={{ p: 4 }}>
          {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mb: 3 }}>{success}</Alert>}

          {repoId && (
            <Paper sx={{ p: 3, mb: 3, backgroundColor: '#EDE9FE', border: '2px solid #7C3AED' }}>
              <Typography variant="h5" sx={{ color: '#7C3AED', mb: 1 }}>
                🎉 Repository Enrolled!
              </Typography>
              <Typography variant="h3" sx={{ fontFamily: 'monospace', color: '#7C3AED', mb: 1 }}>
                repo_id: {repoId}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Saved! Dashboard and Team will use this automatically.
              </Typography>
            </Paper>
          )}

          <form onSubmit={handleSubmit}>
            <Typography variant="h6" sx={{ mb: 2, color: '#7C3AED' }}>
              Repository Information
            </Typography>

            <TextField
              fullWidth
              label="GitHub Repository ID"
              type="number"
              value={formData.repo_id}
              onChange={handleChange('repo_id')}
              margin="normal"
              required
              disabled={isEnrolled} // Disable after enrollment
              helperText={isEnrolled ? "Enrolled repository - click 'Enroll New Repository' to change" : "Find this at: github.com/repos/owner/repo-name (API)"}
            />

            <TextField
              fullWidth
              label="GitHub Installation ID"
              type="number"
              value={formData.installation_id}
              onChange={handleChange('installation_id')}
              margin="normal"
              required
              disabled={isEnrolled} // Disable after enrollment
              helperText={isEnrolled ? "Enrolled repository" : "Get this from your GitHub App installation"}
            />

            <TextField
              fullWidth
              label="Repository Full Name"
              value={formData.repo_full_name}
              onChange={handleChange('repo_full_name')}
              margin="normal"
              required
              disabled={isEnrolled} // Disable after enrollment
              placeholder="owner/repository"
              helperText={isEnrolled ? "Enrolled repository" : "Format: owner/repo (e.g., demo-org/bug-tracker-pro)"}
            />

            <Divider sx={{ my: 3 }} />

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              ℹ️ The fields below are pre-filled with correct values. 
              Only change if you need custom label mappings.
            </Typography>

            <Typography variant="h6" sx={{ mb: 2, color: '#7C3AED' }}>
              Categories (Allowed: bug, feature, docs, security, question)
            </Typography>

            <TextField fullWidth label="Bug" value={formData.cat_bug} onChange={handleChange('cat_bug')} margin="normal" disabled={isEnrolled} />
            <TextField fullWidth label="Feature" value={formData.cat_feature} onChange={handleChange('cat_feature')} margin="normal" disabled={isEnrolled} />
            <TextField fullWidth label="Docs" value={formData.cat_docs} onChange={handleChange('cat_docs')} margin="normal" disabled={isEnrolled} />
            <TextField fullWidth label="Security" value={formData.cat_security} onChange={handleChange('cat_security')} margin="normal" disabled={isEnrolled} />
            <TextField fullWidth label="Question" value={formData.cat_question} onChange={handleChange('cat_question')} margin="normal" disabled={isEnrolled} />

            <Divider sx={{ my: 3 }} />

            <Typography variant="h6" sx={{ mb: 2, color: '#7C3AED' }}>
              Priorities (Allowed: P0, P1, P2, P3)
            </Typography>

            <TextField fullWidth label="P0" value={formData.pri_p0} onChange={handleChange('pri_p0')} margin="normal" disabled={isEnrolled} />
            <TextField fullWidth label="P1" value={formData.pri_p1} onChange={handleChange('pri_p1')} margin="normal" disabled={isEnrolled} />
            <TextField fullWidth label="P2" value={formData.pri_p2} onChange={handleChange('pri_p2')} margin="normal" disabled={isEnrolled} />
            <TextField fullWidth label="P3" value={formData.pri_p3} onChange={handleChange('pri_p3')} margin="normal" disabled={isEnrolled} />

            {!isEnrolled && (
              <Button
                type="submit"
                variant="contained"
                fullWidth
                size="large"
                disabled={loading}
                sx={{
                  mt: 4,
                  py: 1.5,
                  backgroundColor: '#7C3AED',
                  textTransform: 'none',
                  fontSize: '1rem',
                  fontWeight: 600,
                  '&:hover': { backgroundColor: '#6D28D9' }
                }}
              >
                {loading ? <CircularProgress size={24} /> : 'Enroll Repository'}
              </Button>
            )}
          </form>

          {!isEnrolled && (
            <Box sx={{ mt: 3, p: 2, backgroundColor: '#FEF3C7', borderRadius: 2 }}>
              <Typography variant="caption" fontWeight="bold" color="#92400E">
                💡 Quick Demo: Click "Load Demo Data" above, then click "Enroll Repository"!
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}